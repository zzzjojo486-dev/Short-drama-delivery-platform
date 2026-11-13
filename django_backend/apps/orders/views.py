import os
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from apps.common.response import fail, ok
from apps.orders.models import Order, OrderApplication, OrderDelivery, Review
from apps.users.permissions import IsAdminStaff, IsReviewer

MAX_DELIVERY_VIDEO_BYTES = 1073741824
ALLOWED_VIDEO_EXTENSIONS = {".mp4"}


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "role", None) in (0, 1))


class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user)


class IsCreator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, "role", None) == 3)


class OrderInput(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    brief = serializers.CharField(required=False, allow_blank=True)
    requirement = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(max_length=32, required=False, allow_blank=True)
    budget = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise ValidationError("包含不允许修改的字段")
        return attrs


class ReviewInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "reject"))
    opinion = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["action"] == "reject" and not attrs["opinion"]:
            raise ValidationError("驳回必须填写审核意见")
        return attrs


def application_data(application):
    return {
        "id": application.id, "order": application.order_id,
        "creator": application.creator_id,
        "creator_name": application.creator.nickname or application.creator.username,
        "proposal": application.proposal, "selected": application.selected,
        "created_at": application.created_at,
    }


def delivery_data(delivery, request=None, with_reviews=False):
    video_file = delivery.video_file.url if delivery.video_file else None
    if video_file and request:
        video_file = request.build_absolute_uri(video_file)
    data = {
        "id": delivery.id, "order": delivery.order.title,
        "order_id": delivery.order_id, "creator": delivery.creator.username,
        "creator_id": delivery.creator_id, "delivery_type": delivery.delivery_type,
        "video_file": video_file,
        "video_url": delivery.video_url, "note": delivery.note,
        "status": delivery.status, "created_at": delivery.created_at,
    }
    if with_reviews:
        data["reviews"] = [
            {
                "id": r.id, "action": r.action, "opinion": r.opinion,
                "reviewer_id": r.reviewer_id, "created_at": r.created_at,
            }
            for r in Review.objects.filter(
                target_type=Review.DELIVERY, target_id=delivery.id,
            ).order_by("id")
        ]
    return data


def order_data(order, detail=False, request=None):
    data = {
        "id": order.id, "title": order.title, "brief": order.brief,
        "requirement": order.requirement, "category": order.category,
        "budget": order.budget, "status": order.status,
        "publisher": order.publisher_id, "created": order.created, "updated": order.updated,
    }
    if detail:
        data["applications"] = [
            application_data(a) for a in order.applications.select_related("creator").order_by("id")
        ]
        data["deliveries"] = [
            delivery_data(d, request=request)
            for d in order.deliveries.select_related("creator", "order").order_by("-created_at", "-id")
        ]
        can_complete, blocked_reason = complete_check(order)
        data["can_complete"] = can_complete
        data["complete_blocked_reason"] = blocked_reason
    return data


def complete_check(order):
    selected_creator_ids = list(
        order.applications.filter(selected=True).values_list("creator_id", flat=True)
    )
    if not selected_creator_ids:
        return False, "商单须至少有一位入选创作者才可结单"
    deliveries = order.deliveries.all()
    if deliveries.filter(status=OrderDelivery.PENDING).exists():
        return False, "商单存在待审核交付，暂不可结单"
    approved_creator_ids = set(
        deliveries.filter(status=OrderDelivery.APPROVED).values_list("creator_id", flat=True)
    )
    missing = [cid for cid in selected_creator_ids if cid not in approved_creator_ids]
    if missing:
        return False, "存在入选创作者尚无审核通过的交付"
    return True, None


def validate_and_save_video(uploaded_file):
    name = (uploaded_file.name or "").strip()
    if not name:
        raise ValidationError("请上传视频文件")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError("仅支持 MP4 格式视频")

    rel_dir = "deliveries"
    abs_dir = os.path.join(str(settings.MEDIA_ROOT), rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    unique = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(abs_dir, unique)

    total = 0
    exceeded = False
    with open(abs_path, "wb") as dst:
        for chunk in uploaded_file.chunks():
            total += len(chunk)
            if total > MAX_DELIVERY_VIDEO_BYTES:
                exceeded = True
                break
            dst.write(chunk)
    if exceeded:
        try:
            os.remove(abs_path)
        except OSError:
            pass
        raise ValidationError("视频大小不能超过 1GB")
    if total == 0:
        try:
            os.remove(abs_path)
        except OSError:
            pass
        raise ValidationError("视频文件不能为空")
    return f"{rel_dir}/{unique}"


def validate_video_url(value):
    value = (value or "").strip()
    if not value:
        raise ValidationError("请填写视频外链")
    if len(value) > 500:
        raise ValidationError("视频外链不能超过 500 个字符")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError("视频外链必须是 http/https 链接")
    return value


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def paginated_envelope(paginator, page, alias=None):
    envelope = {
        "count": paginator.page.paginator.count,
        "next": paginator.get_next_link(),
        "previous": paginator.get_previous_link(),
        "results": page,
    }
    if alias:
        envelope[alias] = page
    return envelope


class AdminOrderListView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        orders = Order.objects.order_by("-created", "-id")
        status = request.query_params.get("status", "")
        if status != "":
            try:
                status = int(status)
            except (TypeError, ValueError):
                return fail(400, "商单状态无效")
            if status not in dict(Order.STATUS_CHOICES):
                return fail(400, "商单状态无效")
            orders = orders.filter(status=status)
        category = request.query_params.get("category")
        search = request.query_params.get("search")
        if category:
            orders = orders.filter(category=category)
        if search:
            orders = orders.filter(title__icontains=search)
        paginator = OrderPagination()
        page = paginator.paginate_queryset(orders, request)
        return ok(paginated_envelope(paginator, [order_data(order) for order in page]))

    def post(self, request):
        serializer = OrderInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            order = Order.objects.create(publisher=request.user, **serializer.validated_data)
        return ok({"order": order_data(order)}, message="商单已创建")


class AdminOrderDetailView(APIView):
    def get_permissions(self):
        return [IsAdminStaff() if self.request.method == "GET" else IsOperator()]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        return ok({"order": order_data(order, detail=True, request=request)})

    @transaction.atomic
    def patch(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status not in (Order.DRAFT, Order.REJECTED):
            return fail(400, "仅草稿或已驳回商单可修改")
        serializer = OrderInput(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(order, field, value)
        order.save()
        return ok({"order": order_data(order)}, message="商单已保存")


class AdminOrderTransitionView(APIView):
    permission_classes = [IsOperator]
    transition = None

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if self.transition == "submit":
            if order.status not in (Order.DRAFT, Order.REJECTED):
                return fail(400, "仅草稿或已驳回商单可提交审核")
            order.status = Order.PENDING
        elif self.transition == "complete":
            if order.status != Order.PROGRESS:
                return fail(400, "仅进行中商单可结单")
            can_complete, reason = complete_check(order)
            if not can_complete:
                return fail(400, reason)
            order.status = Order.COMPLETED
        elif self.transition == "close":
            if order.status in (Order.COMPLETED, Order.CLOSED):
                return fail(400, "终态商单不可关闭")
            order.status = Order.CLOSED
        else:
            return fail(400, "不支持的商单操作")
        order.save(update_fields=["status", "updated"])
        return ok({"order": order_data(order)})


class AdminOrderReviewView(APIView):
    permission_classes = [IsReviewer]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status != Order.PENDING:
            return fail(400, "仅待审核商单可审核，请勿重复审核")
        serializer = ReviewInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        approved = data["action"] == "approve"
        order.status = Order.ONLINE if approved else Order.REJECTED
        order.save(update_fields=["status", "updated"])
        Review.objects.create(
            target_type=Review.ORDER, target_id=order.id, reviewer=request.user,
            action=Review.APPROVE if approved else Review.REJECT, opinion=data["opinion"],
        )
        return ok({"order": order_data(order)}, message="审核成功")


class AdminOrderApplicationsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request, order_id):
        if not Order.objects.filter(pk=order_id).exists():
            return fail(404, "商单不存在")
        applications = OrderApplication.objects.filter(order_id=order_id).select_related("creator").order_by("id")
        paginator = OrderPagination()
        page = paginator.paginate_queryset(applications, request)
        return ok(paginated_envelope(
            paginator, [application_data(a) for a in page], alias="applications",
        ))


class AdminOrderSelectView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, order_id, application_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status not in (Order.ONLINE, Order.PROGRESS):
            return fail(400, "仅已上线或进行中商单可选中参与者")
        try:
            application = OrderApplication.objects.select_for_update().select_related("creator").get(
                pk=application_id, order_id=order.id,
            )
        except OrderApplication.DoesNotExist:
            return fail(404, "报名记录不存在")
        if application.selected:
            return fail(400, "该参与者已选中，请勿重复操作")
        application.selected = True
        application.save(update_fields=["selected"])
        order.status = Order.PROGRESS
        order.save(update_fields=["status", "updated"])
        return ok({"application": application_data(application), "order": order_data(order)})


class AdminOrderAssignView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status not in (Order.ONLINE, Order.PROGRESS):
            return fail(400, "仅已上线或进行中商单可指派参与者")

        try:
            creator_id = int(request.data.get("creator_id"))
        except (TypeError, ValueError):
            return fail(400, "请提供有效的创作者")

        from apps.users.models import User
        try:
            creator = User.objects.get(pk=creator_id)
        except User.DoesNotExist:
            return fail(404, "创作者不存在")
        if creator.role != 3:
            return fail(400, "仅可指派普通用户为创作者")

        application = order.applications.filter(creator_id=creator_id).first()
        if application and application.selected:
            return fail(400, "该参与者已选中，请勿重复操作")
        if application:
            application.selected = True
            application.save(update_fields=["selected"])
        else:
            try:
                application = OrderApplication.objects.create(
                    order=order, creator=creator, proposal="", selected=True,
                )
            except IntegrityError:
                return fail(400, "该创作者已有报名记录，请勿重复操作")
        order.status = Order.PROGRESS
        order.save(update_fields=["status", "updated"])
        return ok({"application": application_data(application), "order": order_data(order)})


class PendingDeliveryListView(APIView):
    permission_classes = [IsReviewer]

    def get(self, request):
        deliveries = OrderDelivery.objects.filter(
            status=OrderDelivery.PENDING, order__status=Order.PROGRESS,
        ).select_related("order", "creator").order_by("id")
        paginator = OrderPagination()
        page = paginator.paginate_queryset(deliveries, request)
        return ok(paginated_envelope(
            paginator, [delivery_data(d, request=request) for d in page], alias="deliveries",
        ))


class DeliverReviewView(APIView):
    permission_classes = [IsReviewer]

    @transaction.atomic
    def post(self, request, delivery_id):
        order_id = OrderDelivery.objects.filter(pk=delivery_id).values_list("order_id", flat=True).first()
        if order_id is None:
            return fail(404, "短剧不存在")
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
            delivery = OrderDelivery.objects.select_for_update().get(pk=delivery_id, order_id=order.id)
        except (Order.DoesNotExist, OrderDelivery.DoesNotExist):
            return fail(404, "短剧不存在")
        if delivery.status != OrderDelivery.PENDING:
            return fail(400, "仅待审核交付可审核，请勿重复审核")
        if order.status != Order.PROGRESS:
            return fail(400, "仅进行中商单的交付可审核")
        serializer = ReviewInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        approved = data["action"] == "approve"
        delivery.status = OrderDelivery.APPROVED if approved else OrderDelivery.RETURNED
        delivery.save(update_fields=["status"])
        Review.objects.create(
            target_type=Review.DELIVERY, target_id=delivery.id, reviewer=request.user,
            action=Review.APPROVE if approved else Review.REJECT, opinion=data["opinion"],
        )
        return ok(message="审核成功")


def _visible_creator_orders(user):
    return Order.objects.filter(
        Q(status__in=(Order.ONLINE, Order.PROGRESS)) |
        Q(applications__creator=user)
    ).distinct()


def _creator_order_brief(order, user):
    application = order.applications.filter(creator=user).first()
    is_applied = application is not None
    is_selected = bool(application and application.selected)
    has_pending = order.deliveries.filter(creator=user, status=OrderDelivery.PENDING).exists()
    has_approved = order.deliveries.filter(creator=user, status=OrderDelivery.APPROVED).exists()
    data = order_data(order)
    data.update({
        "is_applied": is_applied,
        "is_selected": is_selected,
        "can_apply": order.status == Order.ONLINE and not is_applied,
        "can_deliver": (order.status == Order.PROGRESS and is_selected
                        and not has_pending and not has_approved),
    })
    return data


class CreatorOrderListView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        orders = _visible_creator_orders(request.user).order_by("-created", "-id")
        status = request.query_params.get("status", "")
        if status != "":
            try:
                status = int(status)
            except (TypeError, ValueError):
                return fail(400, "商单状态无效")
            if status not in dict(Order.STATUS_CHOICES):
                return fail(400, "商单状态无效")
            orders = orders.filter(status=status)
        category = request.query_params.get("category")
        search = request.query_params.get("search")
        if category:
            orders = orders.filter(category=category)
        if search:
            orders = orders.filter(title__icontains=search)
        paginator = OrderPagination()
        page = paginator.paginate_queryset(orders, request)
        return ok(paginated_envelope(
            paginator, [_creator_order_brief(o, request.user) for o in page],
        ))


class CreatorOrderDetailView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, order_id):
        try:
            order = _visible_creator_orders(request.user).get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        application = order.applications.filter(creator=request.user).first()
        is_applied = application is not None
        is_selected = bool(application and application.selected)
        has_pending = order.deliveries.filter(creator=request.user, status=OrderDelivery.PENDING).exists()
        has_approved = order.deliveries.filter(creator=request.user, status=OrderDelivery.APPROVED).exists()
        deliveries = order.deliveries.filter(creator=request.user).select_related("creator", "order").order_by("-created_at", "-id")
        return ok({
            "order": order_data(order),
            "is_applied": is_applied,
            "is_selected": is_selected,
            "can_apply": order.status == Order.ONLINE and not is_applied,
            "can_deliver": (order.status == Order.PROGRESS and is_selected
                            and not has_pending and not has_approved),
            "application": application_data(application) if application else None,
            "deliveries": [delivery_data(d, request=request, with_reviews=True) for d in deliveries],
        })


class CreatorOrderApplyView(APIView):
    permission_classes = [IsCreator]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status != Order.ONLINE:
            return fail(400, "仅已上线商单可报名")
        if order.applications.filter(creator=request.user).exists():
            return fail(400, "您已报名该商单，请勿重复报名")
        proposal = (request.data.get("proposal") or "").strip()
        if len(proposal) > 2000:
            return fail(400, "报名说明不能超过 2000 个字符")
        try:
            application = OrderApplication.objects.create(
                order=order, creator=request.user, proposal=proposal,
            )
        except IntegrityError:
            return fail(400, "您已报名该商单，请勿重复报名")
        return ok({"application": application_data(application)}, message="报名成功")


class CreatorOrderDeliverView(APIView):
    permission_classes = [IsCreator]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return fail(404, "商单不存在")
        if order.status != Order.PROGRESS:
            return fail(400, "仅进行中商单可提交交付")
        if not order.applications.filter(creator=request.user, selected=True).exists():
            return fail(403, "仅入选创作者可提交交付")
        if order.deliveries.filter(creator=request.user, status=OrderDelivery.PENDING).exists():
            return fail(400, "已有待审核交付，请勿重复提交")
        if order.deliveries.filter(creator=request.user, status=OrderDelivery.APPROVED).exists():
            return fail(400, "已有审核通过的交付，请勿重复提交")

        delivery_type = request.data.get("delivery_type")
        if delivery_type == "video":
            video_file = request.FILES.get("video_file")
            if not video_file:
                return fail(400, "视频模式必须上传 video_file")
            if request.data.get("video_url"):
                return fail(400, "视频与外链只能二选一")
            rel_path = validate_and_save_video(video_file)
            delivery = OrderDelivery.objects.create(
                order=order, creator=request.user, delivery_type=OrderDelivery.VIDEO,
                video_file=rel_path, video_url=None,
                note=(request.data.get("note") or "").strip(),
            )
        elif delivery_type == "link":
            if request.FILES.get("video_file"):
                return fail(400, "视频与外链只能二选一")
            video_url = validate_video_url(request.data.get("video_url"))
            delivery = OrderDelivery.objects.create(
                order=order, creator=request.user, delivery_type=OrderDelivery.LINK,
                video_url=video_url,
                note=(request.data.get("note") or "").strip(),
            )
        else:
            return fail(400, "delivery_type 仅支持 video 或 link")

        return ok({"delivery": delivery_data(delivery, request=request)}, message="交付已提交")

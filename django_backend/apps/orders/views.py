from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from apps.common.response import fail, ok
from apps.orders.models import Order, OrderApplication, OrderDelivery, Review
from apps.users.permissions import IsAdminStaff, IsReviewer


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "role", None) in (0, 1))


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


def delivery_data(delivery):
    return {
        "id": delivery.id, "order": delivery.order.title,
        "order_id": delivery.order_id, "creator": delivery.creator.username,
        "creator_id": delivery.creator_id, "delivery_type": delivery.delivery_type,
        "video_file": delivery.video_file.url if delivery.video_file else None,
        "video_url": delivery.video_url, "note": delivery.note,
        "status": delivery.status, "created_at": delivery.created_at,
    }


def order_data(order, detail=False):
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
            delivery_data(d) for d in order.deliveries.select_related("creator", "order").order_by("id")
        ]
    return data


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


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
        return ok({
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(), "previous": paginator.get_previous_link(),
            "results": [order_data(order) for order in page],
        })

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
        return ok({"order": order_data(order, detail=True)})

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
            if not order.deliveries.filter(status=OrderDelivery.APPROVED).exists():
                return fail(400, "商单须有审核通过的交付才可结单")
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
        return ok({"applications": [application_data(a) for a in applications]})


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


class PendingDeliveryListView(APIView):
    """保留既有待审交付接口与 deliveries 字段。"""
    permission_classes = [IsReviewer]

    def get(self, request):
        deliveries = OrderDelivery.objects.filter(status=OrderDelivery.PENDING).select_related(
            "order", "creator",
        ).order_by("id")
        return ok({"deliveries": [delivery_data(d) for d in deliveries]})


class DeliverReviewView(APIView):
    permission_classes = [IsReviewer]

    @transaction.atomic
    def post(self, request, delivery_id):
        # 所有交付变更先锁商单，再锁交付，与结单/关闭使用同一个串行化入口。
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

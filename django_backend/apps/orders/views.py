from rest_framework.views import APIView
from rest_framework.response import Response
from apps.orders.models import OrderDelivery, Review
from apps.users.permissions import IsReviewer
from rest_framework import status

# Create your views here.

class PendingDeliveryListView(APIView):
    """GET /api/admin/reviews/deliveries/ - 待审核的成品短剧列表。"""
    permission_classes = [IsReviewer]

    def get(self,request):
        """获取所有为"""
        delivers = OrderDelivery.objects.filter(
            status = OrderDelivery.PENDING,
        )
        data = [
            {
                "id":d.id,
                "order":d.order.title,
                "creator": d.creator.username,
                "delivery_type": d.delivery_type,
                "note": d.note,
            }

            for d in delivers
        ]
        return Response({"success":True,"deliveries":data})


class DeliverReviewView(APIView):
    """POST /api/admin/deliveries/{id}/review/ - 审核成品:通过或驳回,并留痕。"""
    permission_classes = [IsReviewer]

    def post(self,request,delivery_id):
        try:
            delivery = OrderDelivery.objects.get(id=delivery_id)
        except OrderDelivery.DoesNotExist:
            return Response({"success":False,"message":"短剧不存在"},status=status.HTTP_404_NOT_FOUND)
        action = request.data.get('action')
        opinion = request.data.get('opinion' or "").strip()

        if action == 'approve':
            delivery.status = OrderDelivery.STATUS_APPROVED
        elif action == 'reject':
            delivery.status = OrderDelivery.STATUS_REJECTED
        else:
            return Response({"success":False,"message":"审核类型错误"})
        delivery.save()

        Review.objects.create(
            target_type = Review.DELIVERY,
            target_id = delivery_id,
            reviewer = request.user,
            action = action,
            opinion = opinion,
        )
        return Response({"success":True,"message":"审核成功"})
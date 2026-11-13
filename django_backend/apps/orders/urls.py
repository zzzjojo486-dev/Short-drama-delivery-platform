from django.urls import path
from .views import (
    AdminOrderApplicationsView, AdminOrderAssignView, AdminOrderDetailView,
    AdminOrderListView, AdminOrderReviewView, AdminOrderSelectView,
    AdminOrderTransitionView, CreatorOrderApplyView, CreatorOrderDeliverView,
    CreatorOrderDetailView, CreatorOrderListView, DeliverReviewView,
    PendingDeliveryListView,
)

urlpatterns = [
    path("admin/orders/", AdminOrderListView.as_view()),
    path("admin/orders/<int:order_id>/", AdminOrderDetailView.as_view()),
    path("admin/orders/<int:order_id>/submit/", AdminOrderTransitionView.as_view(transition="submit")),
    path("admin/orders/<int:order_id>/review/", AdminOrderReviewView.as_view()),
    path("admin/orders/<int:order_id>/complete/", AdminOrderTransitionView.as_view(transition="complete")),
    path("admin/orders/<int:order_id>/close/", AdminOrderTransitionView.as_view(transition="close")),
    path("admin/orders/<int:order_id>/applications/", AdminOrderApplicationsView.as_view()),
    path("admin/orders/<int:order_id>/applications/<int:application_id>/select/", AdminOrderSelectView.as_view()),
    path("admin/orders/<int:order_id>/assign/", AdminOrderAssignView.as_view()),
    path("admin/reviews/deliveries/", PendingDeliveryListView.as_view()),
    path("admin/deliveries/<int:delivery_id>/review/", DeliverReviewView.as_view()),
    # 创作者端接口(无 admin 前缀)
    path("orders/", CreatorOrderListView.as_view()),
    path("orders/<int:order_id>/", CreatorOrderDetailView.as_view()),
    path("orders/<int:order_id>/apply/", CreatorOrderApplyView.as_view()),
    path("orders/<int:order_id>/deliver/", CreatorOrderDeliverView.as_view()),
]

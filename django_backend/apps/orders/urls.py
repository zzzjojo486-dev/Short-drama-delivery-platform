from django.urls import path
from .views import (
    AdminOrderApplicationsView, AdminOrderDetailView, AdminOrderListView,
    AdminOrderReviewView, AdminOrderSelectView, AdminOrderTransitionView,
    DeliverReviewView, PendingDeliveryListView,
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
    path("admin/reviews/deliveries/", PendingDeliveryListView.as_view()),
    path("admin/deliveries/<int:delivery_id>/review/", DeliverReviewView.as_view()),
]

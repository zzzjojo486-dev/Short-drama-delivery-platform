from django.urls import path
from .views import PendingDeliveryListView, DeliverReviewView

urlpatterns = [
    path("admin/reviews/deliveries/", PendingDeliveryListView.as_view()),
    path("admin/deliveries/<int:delivery_id>/review/", DeliverReviewView.as_view()),
]

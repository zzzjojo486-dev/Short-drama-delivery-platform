from django.urls import path

from .views import LoginView, ProfileView, PublicUserView, RegisterView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("register", RegisterView.as_view(), name="register"),
    path("user/profile", ProfileView.as_view(), name="profile"),
    path("users/<int:user_id>", PublicUserView.as_view(), name="public-user"),
]

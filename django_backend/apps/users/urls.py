from django.urls import path

from .views import LoginView, ProfileView, PublicUserView, RegisterView, AdminListView, AdminUserRoleView, \
    AdminLoginView

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("admin/login", AdminLoginView.as_view(), name="adminlogin"),
    path("register", RegisterView.as_view(), name="register"),
    path("user/profile", ProfileView.as_view(), name="profile"),
    path("users/<int:user_id>", PublicUserView.as_view(), name="public-user"),
    path("admin/users", AdminListView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/role", AdminUserRoleView.as_view(), name="admin-users-role"),
]

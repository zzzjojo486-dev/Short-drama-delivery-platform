from django.urls import path

from .views import (AdminListView, AdminLoginView, AdminUserRoleView, AIPolishView,
                    ConversationMessagesView, ConversationsView, FollowCountsView,
                    FollowersView, FollowView, FollowingView, IsFollowingView, LoginView,
                    MarkMessagesReadView, MarkNotificationsReadView, NotificationsView,
                    ProfileView, PublicUserView, RegisterView, SendMessageView,
                    UnfollowView, UnreadCountView)

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
    path("admin/login", AdminLoginView.as_view(), name="adminlogin"),
    path("register", RegisterView.as_view(), name="register"),
    path("user/profile", ProfileView.as_view(), name="profile"),
    path("users/<int:user_id>", PublicUserView.as_view(), name="public-user"),
    # 关注块(B)
    path("users/<int:user_id>/follow", FollowView.as_view(), name="follow"),
    path("users/<int:user_id>/unfollow", UnfollowView.as_view(), name="unfollow"),
    path("users/<int:user_id>/is_following", IsFollowingView.as_view(), name="is-following"),
    path("users/<int:user_id>/followers", FollowersView.as_view(), name="followers"),
    path("users/<int:user_id>/following", FollowingView.as_view(), name="following"),
    path("users/<int:user_id>/counts", FollowCountsView.as_view(), name="follow-counts"),
    # 私信块(C)
    path("messages", SendMessageView.as_view(), name="send-message"),
    path("messages/conversations", ConversationsView.as_view(), name="conversations"),
    path("messages/conversation/<int:other_user_id>", ConversationMessagesView.as_view(), name="conversation"),
    path("messages/read", MarkMessagesReadView.as_view(), name="messages-read"),
    path("messages/unread/count", UnreadCountView.as_view(), name="unread-count"),
    # 通知(C)
    path("notifications", NotificationsView.as_view(), name="notifications"),
    path("notifications/read", MarkNotificationsReadView.as_view(), name="notifications-read"),
    # AI 润色(D)
    path("ai/polish", AIPolishView.as_view(), name="ai-polish"),
    path("admin/users/", AdminListView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/role/", AdminUserRoleView.as_view(), name="admin-users-role"),
]

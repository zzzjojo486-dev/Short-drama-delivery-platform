from django.urls import path

from .views import (
    CommentLikeView,
    CommentListCreateView,
    PostCollectView,
    PostDetailDeleteView,
    PostLikeView,
    PostListCreateView,
    PostVisibilityView,
    UserCollectedPostListView,
    UserLikedPostListView,
    UserPostListView,
)

# 前缀 "api/" 由 config/urls.py 统一挂入,此处只写 /posts 及以下路径。
# 注意:user/ 具体路由须在 <int:post_id> 之前声明。
urlpatterns = [
    path("posts", PostListCreateView.as_view()),
    path("posts/user/<int:user_id>", UserPostListView.as_view()),
    path("posts/user/<int:user_id>/liked", UserLikedPostListView.as_view()),
    path("posts/user/<int:user_id>/collected", UserCollectedPostListView.as_view()),
    path("posts/<int:post_id>/visibility", PostVisibilityView.as_view()),
    path("posts/<int:post_id>/like", PostLikeView.as_view()),
    path("posts/<int:post_id>/collect", PostCollectView.as_view()),
    path("posts/<int:post_id>/comments", CommentListCreateView.as_view()),
    path("posts/<int:post_id>", PostDetailDeleteView.as_view()),
    path("comments/<int:comment_id>/like", CommentLikeView.as_view()),
]

"""
帖子/评论/点赞/收藏接口:移植自原 FastAPI 的 backend/post_service.py + server.py 路由。

通过 body/query 里的 user_id 定位当前用户;响应统一三层 {code, message, data}。
"""
import os

from django.conf import settings
from django.db.models import Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.common.response import fail, ok
from apps.post.models import Collection, Comment, CommentLike, Like, Notification, Post, PostImage
from apps.users.utils import save_image, save_video


def _post_to_dict(p):
    """单个帖子行 → dict,字段名对齐原版 SELECT p.*, u.nickname, u.avatar_url。"""
    return {
        "id": p.id,
        "user_id": p.user_id_id,
        "title": p.title,
        "content": p.content,
        "image_url": p.image_url,
        "likes_count": p.likes_count,
        "created_at": p.created_at,
        "category": p.category,
        "is_private": p.is_private,
        "video_url": p.video_url,
        "nickname": p.user_id.nickname,
        "avatar_url": p.user_id.avatar_url,
    }


def _comment_to_dict(c):
    """单个评论行 → dict,对齐原版 SELECT c.*, u.nickname, u.avatar_url, is_liked。"""
    return {
        "id": c.id,
        "post_id": c.post_id_id,
        "user_id": c.user_id_id,
        "content": c.content,
        "likes_count": c.likes_count,
        "created_at": c.created_at,
        "nickname": c.user_id.nickname,
        "avatar_url": c.user_id.avatar_url,
        "is_liked": c.is_liked,
    }


class PostListView(APIView):
    """GET /api/posts - 帖子流(搜索/分类/随机)。"""

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 20))
            offset = int(request.query_params.get("offset", 0))
        except (TypeError, ValueError):
            return fail(400, "参数错误")

        search = request.query_params.get("search")
        category = request.query_params.get("category")

        qs = Post.objects.filter(is_private=False).select_related("user_id")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        if category and category != "推荐":
            qs = qs.filter(category=category)

        if (not category or category == "推荐") and not search:
            qs = qs.order_by("?")  # 对应 ORDER BY RAND()
        else:
            qs = qs.order_by("-created_at")

        posts = list(qs[offset: offset + limit])
        return ok([_post_to_dict(p) for p in posts])


class UserPostListView(APIView):
    """GET /api/posts/user/{user_id} - 某用户的帖子。"""

    def get(self, request, user_id):
        current_user_id = request.query_params.get("current_user_id")
        qs = Post.objects.filter(user_id=user_id).select_related("user_id")
        if str(user_id) != str(current_user_id):
            qs = qs.filter(is_private=False)
        qs = qs.order_by("-created_at")
        return ok([_post_to_dict(p) for p in qs])


class UserLikedPostListView(APIView):
    """GET /api/posts/user/{user_id}/liked - 用户点赞的帖子。"""

    def get(self, request, user_id):
        qs = (
            Post.objects.filter(likes__user_id=user_id, is_private=False)
            .select_related("user_id")
            .order_by("-likes__created_at")
        )
        return ok([_post_to_dict(p) for p in qs])


class UserCollectedPostListView(APIView):
    """GET /api/posts/user/{user_id}/collected - 用户收藏的帖子。"""

    def get(self, request, user_id):
        qs = (
            Post.objects.filter(collections__user_id=user_id, is_private=False)
            .select_related("user_id")
            .order_by("-collections__created_at")
        )
        return ok([_post_to_dict(p) for p in qs])


class PostDetailView(APIView):
    """GET /api/posts/{post_id} - 帖子详情(带 images/is_liked/is_collected)。"""

    def get(self, request, post_id):
        user_id = request.query_params.get("user_id")
        try:
            p = Post.objects.select_related("user_id").get(id=post_id)
        except Post.DoesNotExist:
            return fail(404, "Post not found")

        if p.is_private and (not user_id or p.user_id_id != int(user_id)):
            return fail(404, "Post not found")

        data = _post_to_dict(p)

        # 多图:post_images 按 sort_order,取不到则回退封面
        images = list(
            PostImage.objects.filter(post_id=p.id).order_by("sort_order").values_list("image_url", flat=True)
        )
        if not images and p.image_url:
            images = [p.image_url]
        data["images"] = images

        data["is_liked"] = False
        data["is_collected"] = False
        if user_id:
            data["is_liked"] = Like.objects.filter(user_id=user_id, post_id=p.id).exists()
            data["is_collected"] = Collection.objects.filter(user_id=user_id, post_id=p.id).exists()

        return ok(data)


class PostCreateView(APIView):
    """POST /api/posts - 新建帖子(多图 + 封面,可选视频)。multipart。"""

    def post(self, request):
        user_id = request.data.get("user_id")
        title = request.data.get("title")
        content = request.data.get("content")
        category = request.data.get("category") or "推荐"
        image_files = request.FILES.getlist("images")
        video_file = request.FILES.get("video")

        if not image_files and not video_file:
            return fail(400, "Images or Video required")

        try:
            user = get_object_or_404(User, id=user_id)
        except (TypeError, ValueError):
            return fail(400, "用户不存在")

        title = title.strip() if title else ""
        if not title:
            return fail(400, "标题不能为空")
        if len(title) > 100:
            return fail(400, "标题不能超过100个字符")
        if content and len(content) > 10000:
            return fail(400, "内容不能超过10000个字符")
        if category and len(category) > 50:
            return fail(400, "分类名称过长")

        try:
            # 保存多图,首图为封面
            image_urls = []
            for img in image_files:
                image_urls.append(save_image(img))
            if not image_urls:
                return fail(400, "必须上传封面图片")

            video_url = None
            if video_file:
                video_url = save_video(video_file)

            post = Post.objects.create(
                user_id=user,
                title=title,
                content=content.strip() if content else None,
                image_url=image_urls[0],
                video_url=video_url,
                category=category,
                is_private=False,
            )
            for idx, url in enumerate(image_urls):
                PostImage.objects.create(post_id=post, image_url=url, sort_order=idx)

        except ValueError as e:
            return fail(400, str(e))
        except Exception:
            return fail(400, "Failed to create post")

        return ok(message="Post created successfully")


class PostDeleteView(APIView):
    """DELETE /api/posts/{post_id} - 删除帖子及其物理文件。body: {user_id}。"""

    def delete(self, request, post_id):
        user_id = request.data.get("user_id")
        try:
            p = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return fail(404, "Post not found")
        if p.user_id_id != int(user_id):
            return fail(403, "Permission denied")

        # 收集需删除的物理文件
        files_to_delete = []
        if p.image_url:
            files_to_delete.append(p.image_url)
        if p.video_url:
            files_to_delete.append(p.video_url)
        for url in PostImage.objects.filter(post_id=p.id).values_list("image_url", flat=True):
            if url:
                files_to_delete.append(url)

        for file_path in files_to_delete:
            try:
                if file_path and file_path.startswith("assets/"):
                    abs_path = settings.ASSETS_DIR / os.path.basename(file_path)
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
            except Exception:
                pass  # 文件删除失败不阻断

        p.delete()  # CASCADE 清理关联
        return ok(message="Post deleted successfully")


class PostVisibilityView(APIView):
    """PUT /api/posts/{post_id}/visibility - 公开/私密。body: {user_id, is_private}。"""

    def put(self, request, post_id):
        user_id = request.data.get("user_id")
        is_private = request.data.get("is_private")
        try:
            p = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return fail(404, "Post not found")
        if p.user_id_id != int(user_id):
            return fail(403, "Permission denied")

        p.is_private = bool(is_private)
        p.save(update_fields=["is_private"])
        return ok(message="Visibility updated successfully")


class PostLikeView(APIView):
    """POST /api/posts/{post_id}/like - 点赞/取消点赞。body: {user_id}。"""

    def post(self, request, post_id):
        user_id = request.data.get("user_id")
        if not user_id:
            return fail(400, "User ID required")

        try:
            p = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return fail(404, "帖子不存在")

        existing = Like.objects.filter(user_id=user_id, post_id=p.id)
        if existing.exists():
            existing.delete()
            Post.objects.filter(id=p.id).update(likes_count=F("likes_count") - 1)
            return ok(message="Unliked")
        else:
            Like.objects.create(user_id_id=user_id, post_id=p)
            Post.objects.filter(id=p.id).update(likes_count=F("likes_count") + 1)

            # 通知帖子作者(自己赞自己不通知),与原版一致
            if p.user_id_id != int(user_id):
                try:
                    Notification.objects.create(
                        receiver_id=p.user_id,
                        sender_id_id=int(user_id),
                        type="like_post",
                        target_id=p.id,
                        content=f"赞了你的帖子《{p.title}》",
                    )
                except Exception:
                    pass  # 通知失败不阻断点赞
            return ok(message="Liked")


class PostCollectView(APIView):
    """POST /api/posts/{post_id}/collect - 收藏/取消收藏。body: {user_id}。"""

    def post(self, request, post_id):
        user_id = request.data.get("user_id")
        if not user_id:
            return fail(400, "User ID required")

        try:
            p = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return fail(404, "帖子不存在")

        existing = Collection.objects.filter(user_id=user_id, post_id=p.id)
        if existing.exists():
            existing.delete()
            return ok(message="Uncollected")
        else:
            Collection.objects.create(user_id_id=user_id, post_id=p)
            return ok(message="Collected")


class CommentListView(APIView):
    """GET /api/posts/{post_id}/comments - 帖子评论(带 is_liked)。"""

    def get(self, request, post_id):
        current_user_id = request.query_params.get("user_id")
        qs = Comment.objects.filter(post_id=post_id).select_related("user_id").order_by("created_at")
        if current_user_id:
            liked = CommentLike.objects.filter(comment_id=OuterRef("pk"), user_id=current_user_id)
            qs = qs.annotate(is_liked=Exists(liked))
        else:
            qs = qs.annotate(is_liked=Exists(CommentLike.objects.none()))
        return ok([_comment_to_dict(c) for c in qs])


class CommentCreateView(APIView):
    """POST /api/posts/{post_id}/comments - 发表评论。body: {user_id, content}。"""

    def post(self, request, post_id):
        user_id = request.data.get("user_id")
        content = (request.data.get("content") or "").strip()
        if not content:
            return fail(400, "评论内容不能为空")
        if len(content) > 1000:
            return fail(400, "评论内容不能超过1000个字符")

        if not Post.objects.filter(id=post_id).exists():
            return fail(404, "帖子不存在")

        Comment.objects.create(post_id_id=int(post_id), user_id_id=int(user_id), content=content)
        return ok(message="评论成功")


class CommentLikeView(APIView):
    """POST /api/comments/{comment_id}/like - 评论点赞/取消。body: {user_id}。"""

    def post(self, request, comment_id):
        user_id = request.data.get("user_id")
        if not user_id:
            return fail(400, "User ID required")

        try:
            c = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return fail(404, "评论不存在")

        existing = CommentLike.objects.filter(user_id=user_id, comment_id=c.id)
        if existing.exists():
            existing.delete()
            Comment.objects.filter(id=c.id).update(likes_count=F("likes_count") - 1)
            return ok(message="Unliked")
        else:
            CommentLike.objects.create(user_id_id=user_id, comment_id=c)
            Comment.objects.filter(id=c.id).update(likes_count=F("likes_count") + 1)
            return ok(message="Liked")


# --- 同 URL 不同 HTTP 方法的合并视图(DRF 路由按 URL 首个匹配,单视图承载多方法) ---
class PostListCreateView(PostListView, PostCreateView):
    """GET /api/posts 列表 + POST /api/posts 新建。"""


class PostDetailDeleteView(PostDetailView, PostDeleteView):
    """GET /api/posts/{id} 详情 + DELETE /api/posts/{id} 删除。"""


class CommentListCreateView(CommentListView, CommentCreateView):
    """GET /api/posts/{id}/comments + POST /api/posts/{id}/comments。"""


# 供 PostCreateView 使用的 User 模型(自定义 AUTH_USER_MODEL)
from django.contrib.auth import get_user_model

User = get_user_model()

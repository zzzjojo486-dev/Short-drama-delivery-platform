from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        verbose_name="发布用户ID"
    )
    title = models.CharField(max_length=255, verbose_name="帖子标题")
    content = models.TextField(verbose_name="帖子正文内容")
    image_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="封面图地址")
    likes_count = models.IntegerField(default=0, verbose_name="点赞数量")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="帖子分类")
    is_private = models.BooleanField(default=False, verbose_name="是否私密帖子")
    video_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="视频链接地址")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "posts"
        verbose_name = "帖子"
        verbose_name_plural = "帖子"


class PostImage(models.Model):
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_column="post_id", verbose_name="所属帖子ID")
    image_url = models.CharField(max_length=500, verbose_name="图片地址")
    sort_order = models.IntegerField(default=0, verbose_name="排序序号")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "post_images"
        verbose_name = "帖子附图"
        verbose_name_plural = "帖子附图"


class Comment(models.Model):
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_column="post_id", verbose_name="所属帖子ID")
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        verbose_name="发布用户ID"
    )
    content = models.TextField(verbose_name="评论内容")
    likes_count = models.IntegerField(default=0,verbose_name='点赞数')
    created_at = models.DateTimeField(verbose_name='创建时间',auto_now_add=True)
    class Meta:
        db_table = "comments"
        verbose_name = "评论"
        verbose_name_plural = "评论"


class Like(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        verbose_name="发布用户ID"
    )
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_column="post_id", verbose_name="被点赞帖子ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "likes"
        verbose_name = "帖子点赞记录"
        verbose_name_plural = "帖子点赞记录"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "post_id"], name="unique_user_post_like",
                                    violation_error_message="同一用户不能重复点赞同一个帖子")
        ]


class Collection(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        verbose_name="发布用户ID"
    )
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_column="post_id", verbose_name="被收藏帖子ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "collections"
        verbose_name = "帖子收藏记录"
        verbose_name_plural = "帖子收藏记录"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "post_id"], name="unique_user_post_collection",
                                    violation_error_message="同一用户不能重复收藏同一个帖子")
        ]


class CommentLike(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        verbose_name="发布用户ID"
    )
    comment_id = models.ForeignKey(Comment, on_delete=models.CASCADE, db_column="comment_id", verbose_name="被点赞评论ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "comment_likes"
        verbose_name = "评论点赞记录"
        verbose_name_plural = "评论点赞记录"
        constraints = [
            models.UniqueConstraint(fields=["user_id", "comment_id"], name="unique_user_comment_like",
                                    violation_error_message="同一用户不能重复点赞同一条评论")
        ]

class Notification(models.Model):
    receiver_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="receiver_id",
        related_name="receive_notifications",
        verbose_name="接收用户ID"
    )
    sender_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="sender_id",
        related_name="send_notifications",
        verbose_name="发送用户ID"
    )
    type = models.CharField(max_length=20, verbose_name="通知类型")
    target_id = models.IntegerField(null=True, blank=True, verbose_name="目标ID")
    content = models.CharField(max_length=255, blank=True, null=True, verbose_name="通知内容")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "notifications"

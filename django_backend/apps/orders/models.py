from django.db import models
from django.conf import settings

# Create your models here.
class Order(models.Model):
    """商单主表"""
    DRAFT = 0  # 草稿(刚创建,未提交)
    PENDING = 1  # 待审核
    REJECTED = 2  # 已驳回
    ONLINE = 3  # 已上线(开放报名)
    PROGRESS = 4  # 进行中(已有选定创作者)
    COMPLETED = 5  # 已完成(结单)
    CLOSED = 6  # 已关闭(终止)

    STATUS_CHOICES = (
        (DRAFT, "草稿"), (PENDING, "待审核"), (REJECTED, "已驳回"),
        (ONLINE, "已上线"), (PROGRESS, "进行中"),
        (COMPLETED, "已完成"), (CLOSED, "已关闭"),    )

    title = models.CharField(max_length=100,verbose_name='标题')
    brief = models.TextField(blank=True,verbose_name='需求秒速')
    requirement = models.TextField(blank=True,verbose_name='交付要求')
    category = models.CharField(max_length=32,blank=True,verbose_name='分类')
    budget = models.CharField(max_length=32,blank=True,verbose_name='预算')
    status = models.IntegerField(
        choices=STATUS_CHOICES,default=0,
    )
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="publisher_orders",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order'
        verbose_name = '商单表'

class OrderApplication(models.Model):
    """创作者报名记录。"""
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="applications",verbose_name='关联订单')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,verbose_name='发布人')
    proposal = models.TextField(blank=True,verbose_name="报名说明")   # 报名说明
    selected = models.BooleanField(default=False,verbose_name='是否成功')  # 是否被运营选中
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')

    class Meta:
        db_table = "order_applications"
        verbose_name = "商单报名表"

class OrderDelivery(models.Model):
    """成品交付记录。视频上传 或 外链,二选一。"""
    VIDEO = 0   # 视频短剧提交(上传文件)
    LINK = 1    # 链接短剧提交(填外链)
    PENDING = 0     # 待审核
    APPROVED = 1    # 已通过
    RETURNED = 2    # 退回修改

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="deliveries")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    delivery_type = models.IntegerField(choices=[(VIDEO, "视频"), (LINK, "链接")], default=VIDEO)
    video_file = models.FileField(upload_to="deliveries/", null=True, blank=True)  # 上传的视频
    video_url = models.CharField(max_length=500, null=True, blank=True)            # 外链
    note = models.TextField(blank=True)                     # 交付说明
    status = models.IntegerField(
        choices=[(PENDING, "待审核"), (APPROVED, "已通过"), (RETURNED, "退回修改")], default=PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_deliveries"
        verbose_name = "订单交付表"


class Review(models.Model):
    "同一审查记录表"
    ORDER = 'order'
    DELIVERY = 'delivery'
    POST = 'post'
    COMMENT = 'comment'

    APPROVE = 1 #通过
    REJECT = 2  #驳回

    target_type = models.CharField(max_length=30,verbose_name='对象储存')
    target_id = models.IntegerField(verbose_name='对象ID')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    action = models.IntegerField(
        choices=[(APPROVE, "通过"), (REJECT, "驳回/退回")]

    )
    opinion = models.TextField(blank=True)  # 审核意见
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        verbose_name = '审核表'


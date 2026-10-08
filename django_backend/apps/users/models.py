from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """用户管理器,create_user 对应原 auth_service.register_user 的写入逻辑。"""

    use_in_migrations = True

    def create_user(self, username, password, nickname=None, avatar_url=None):
        user = self.model(username=username, nickname=nickname, avatar_url=avatar_url)
        # Django BCryptPasswordHasher,12 轮,与原 FastAPI 的 bcrypt.gensalt() 一致
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """对应原 schema.sql 的 users 表,字段完全对齐,可直接复用旧库数据。

    注意:password 列在数据库中名为 password_hash(通过 db_column 映射)。
    """

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255, db_column="password_hash")
    nickname = models.CharField(max_length=50, null=True, blank=True)
    avatar_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # users 表没有 last_login 列,移除 AbstractBaseUser 的该 DB 字段
    last_login = None
    # is_active 为类属性(非 DB 字段),users 表也没有此列
    is_active = True

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"

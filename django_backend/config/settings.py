"""
Django settings for the Mini-RedNote backend.

环境变量从仓库根目录的 .env 读取(DB_HOST/DB_USER/DB_PASSWORD/DB_NAME/DB_PORT),
变量名与原 FastAPI 后端(backend/database.py)保持一致。
"""
import sys
from pathlib import Path

import environ

# BASE_DIR = django_backend/,PROJECT_ROOT = 仓库根(存放 .env 与 assets/)
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, True),
    DJANGO_SECRET_KEY=(str, "django-insecure-mini-rednote-dev-key-change-in-production"),
)
environ.Env.read_env(PROJECT_ROOT / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "corsheaders",
    "apps.users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- 数据库:MySQL,配置与原 FastAPI 后端完全一致 ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="mini_redbook"),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# 测试使用 sqlite,不依赖 MySQL 也能跑测试
if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

AUTH_USER_MODEL = "users.User"

# 与原 FastAPI 后端一致:bcrypt 12 轮。
# 旧库中的裸 $2b$12$ 哈希由 apps/users/views.py 的 verify_password 兜底校验。
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = False  # 与原 PyMySQL 返回 naive 本地时间的展示行为一致

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# --- 上传与静态资源 ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# 头像等上传与原 FastAPI 共用仓库根 assets/ 目录,旧图片立即可用
ASSETS_DIR = PROJECT_ROOT / "assets"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.auth.BearerTokenAuthentication",
    ],
    # 原 FastAPI 接口从不强制鉴权(前端靠 body 里的 user_id),保持一致
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "UNAUTHENTICATED_USER": None,
}

# --- CORS:允许来源与原 server.py 一致 ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

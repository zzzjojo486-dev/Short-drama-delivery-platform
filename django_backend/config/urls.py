"""总路由入口:API 前缀 /api/,静态资源前缀 /assets/."""
from django.urls import include, path

from apps.users.views import serve_asset

urlpatterns = [
    path("api/", include("apps.users.urls")),
    # 与原 FastAPI 的 /assets/{filename} 路由保持一致
    path("assets/<str:filename>", serve_asset, name="asset"),
]

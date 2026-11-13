"""总路由入口:API 前缀 /api/,静态资源前缀 /assets/,媒体资源前缀 /media/."""
import mimetypes
import os
import re

from django.conf import settings
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.urls import include, path

from apps.users.views import serve_asset

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def _iter_file(path, start, end):
    with open(path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            chunk = f.read(min(64 * 1024, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def serve_media(request, path):
    """范围感知的媒体文件服务(支持视频 Range 请求,便于预览与拖拽播放)。"""
    media_root = os.path.abspath(str(settings.MEDIA_ROOT))
    full = os.path.abspath(os.path.join(media_root, path))
    if not full.startswith(media_root + os.sep):
        return HttpResponse(status=404)
    if not os.path.isfile(full):
        return HttpResponse(status=404)

    size = os.path.getsize(full)
    content_type = mimetypes.guess_type(full)[0] or "application/octet-stream"
    range_header = request.META.get("HTTP_RANGE")
    if range_header:
        match = RANGE_RE.match(range_header)
        if match:
            start_s, end_s = match.groups()
            if start_s == "":
                length = int(end_s)
                start = max(0, size - length)
                end = size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)
            if start > end or start >= size:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{size}"
                return response
            response = StreamingHttpResponse(
                _iter_file(full, start, end), status=206, content_type=content_type,
            )
            response["Content-Range"] = f"bytes {start}-{end}/{size}"
            response["Content-Length"] = str(end - start + 1)
            response["Accept-Ranges"] = "bytes"
            return response
    response = FileResponse(open(full, "rb"), content_type=content_type)
    response["Content-Length"] = str(size)
    response["Accept-Ranges"] = "bytes"
    return response


urlpatterns = [
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.post.urls")),
    # 与原 FastAPI 的 /assets/{filename} 路由保持一致
    path("assets/<str:filename>", serve_asset, name="asset"),
    # 媒体资源(商单成品视频等)范围感知访问
    path("media/<path:path>", serve_media, name="media"),
]

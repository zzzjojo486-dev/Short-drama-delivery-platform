"""
用户与认证模块视图。

响应格式与原 FastAPI(server.py + backend/auth_service.py)完全对齐:
- 业务错误:HTTP 200 + {"success": false, "message": "..."}
- 资源不存在:404 + {"detail": "..."}
"""
import os

import bcrypt
from django.conf import settings
from django.db import OperationalError
from django.http import FileResponse, JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import create_access_token
from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .utils import save_image


def verify_password(user, raw_password):
    """校验密码,兼容旧库裸 $2b$ 哈希(原 FastAPI 用 bcrypt 直接生成,无 Django 前缀)。"""
    # Django 自带 BCryptPasswordHasher(支持 bcrypt$ 前缀格式)
    if user.check_password(raw_password):
        return True
    # 兜底:直接按 bcrypt 校验,保证旧数据一定验证通过
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), user.password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def first_error(serializer):
    """取序列化器的第一条错误信息,以 {"success": false, "message": ...} 返回。"""
    for errors in serializer.errors.values():
        if isinstance(errors, list) and errors:
            return str(errors[0])
        return str(errors)
    return "请求参数错误"


class LoginView(APIView):
    """POST /api/login - 用户登录(JSON body: username/password)。"""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": first_error(serializer)})

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.filter(username=username).first()
        except OperationalError:
            return Response({"success": False, "message": "Database connection failed"})

        if user and verify_password(user, password):
            # 与原版一致返回用户对象;token 为规范要求的附加字段(前端忽略不影响)
            token = create_access_token(data={"sub": str(user.id)})
            return Response({
                "success": True,
                "user": UserSerializer(user).data,
                "token": token,
            })
        return Response({"success": False, "message": "用户名或密码错误"})


class RegisterView(APIView):
    """POST /api/register - 用户注册(multipart form,头像必填)。"""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": first_error(serializer)})

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        nickname = serializer.validated_data.get("nickname")

        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            return Response({"success": False, "message": "请上传头像"})

        # 与原版顺序一致:先保存头像,再检查用户名是否已存在
        try:
            avatar_url = save_image(avatar_file)
        except ValueError as e:
            return Response({"success": False, "message": str(e)})
        except Exception:
            return Response({"success": False, "message": "头像上传失败"})

        # 昵称缺省为用户名(与原版一致)
        nickname = (nickname or username).strip()

        try:
            if User.objects.filter(username=username).exists():
                return Response({"success": False, "message": "用户名已存在，请选择其他用户名"})
            User.objects.create_user(
                username=username, password=password, nickname=nickname, avatar_url=avatar_url
            )
        except OperationalError:
            return Response({"success": False, "message": "Database connection failed"})
        except Exception:
            return Response({"success": False, "message": "Registration failed"})

        return Response({"success": True, "message": "Registration successful"})


class ProfileView(APIView):
    """PUT /api/user/profile - 更新个人资料(multipart form:user_id、nickname、avatar 可选)。"""

    def put(self, request):
        user_id = request.data.get("user_id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return Response({"success": False, "message": "用户不存在"})

        nickname = (request.data.get("nickname") or "").strip()
        avatar_file = request.FILES.get("avatar")

        # 输入验证(与原 update_user_profile 一致)
        if len(nickname) < 1:
            return Response({"success": False, "message": "昵称不能为空"})
        if len(nickname) > 50:
            return Response({"success": False, "message": "昵称不能超过50个字符"})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success": False, "message": "用户不存在"})
        except OperationalError:
            return Response({"success": False, "message": "Database connection failed"})

        if avatar_file:
            try:
                user.avatar_url = save_image(avatar_file)
            except ValueError as e:
                return Response({"success": False, "message": str(e)})
            except Exception:
                return Response({"success": False, "message": "Update failed"})

        user.nickname = nickname
        try:
            user.save()
        except OperationalError:
            return Response({"success": False, "message": "Database connection failed"})
        except Exception:
            return Response({"success": False, "message": "Update failed"})

        return Response({"success": True, "user": UserSerializer(user).data})


class PublicUserView(APIView):
    """GET /api/users/{user_id} - 用户公开资料。"""

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound(detail="User not found")
        return Response({"success": True, "user": UserSerializer(user).data})


def serve_asset(request, filename):
    """GET /assets/{filename} - 与原 FastAPI 静态文件路由一致,取仓库根 assets/ 目录文件。"""
    path = os.path.join(str(settings.ASSETS_DIR), os.path.basename(filename))
    if os.path.isfile(path):
        response = FileResponse(open(path, "rb"))
        response["Access-Control-Allow-Origin"] = "*"
        return response
    return JsonResponse({"detail": "Image not found"}, status=404)

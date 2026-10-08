"""
用户认证模块测试。

重点覆盖与原 FastAPI 的兼容性:
- 旧库裸 $2b$12$ bcrypt 哈希可直接登录(数据复用)
- 注册校验消息与响应格式逐字一致
"""
import io
import os
import tempfile
from unittest.mock import patch

import bcrypt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework import exceptions
from rest_framework.test import APIClient, APIRequestFactory

from .auth import BearerTokenAuthentication, create_access_token
from .models import User
from .utils import save_image


def make_avatar(name="avatar.jpg", content_type="image/jpeg", fmt="JPEG"):
    img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=content_type)


class AuthApiTests(TestCase):
    """登录/注册/资料接口:响应格式与原 FastAPI 对齐。"""

    def setUp(self):
        self.client = APIClient()

    def register(self, username="testuser", password="password123", nickname=None, avatar=True):
        data = {"username": username, "password": password}
        if nickname:
            data["nickname"] = nickname
        if avatar:
            data["avatar"] = make_avatar()
        return self.client.post("/api/register", data, format="multipart")

    def test_register_missing_avatar(self):
        res = self.register(avatar=False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"success": False, "message": "请上传头像"})

    def test_register_username_too_short(self):
        res = self.register(username="ab")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["message"], "用户名至少需要3个字符")

    def test_register_password_too_short(self):
        res = self.register(password="123")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["message"], "密码至少需要6个字符")

    def test_register_unsupported_extension(self):
        bad = SimpleUploadedFile("avatar.txt", b"hello world", content_type="text/plain")
        res = self.client.post(
            "/api/register",
            {"username": "testuser", "password": "password123", "avatar": bad},
            format="multipart",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["message"].startswith("不支持的文件类型"))

    def test_register_duplicate_username(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register()
            res = self.register()
        self.assertEqual(res.data, {"success": False, "message": "用户名已存在，请选择其他用户名"})

    def test_register_success(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            res = self.register(username="newuser", nickname="小新")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"success": True, "message": "Registration successful"})
        user = User.objects.get(username="newuser")
        self.assertEqual(user.nickname, "小新")
        self.assertEqual(user.avatar_url, "assets/test-avatar.jpg")

    def test_register_nickname_defaults_to_username(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register(username="newuser")
        self.assertEqual(User.objects.get(username="newuser").nickname, "newuser")

    def test_login_success(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register(username="loginuser", nickname="登录用户")
        res = self.client.post("/api/login", {"username": "loginuser", "password": "password123"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["user"], {
            "id": User.objects.get(username="loginuser").id,
            "username": "loginuser",
            "nickname": "登录用户",
            "avatar_url": "assets/test-avatar.jpg",
        })
        self.assertTrue(res.data.get("token"))  # 规范要求的 token 附加字段

    def test_login_wrong_password(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register()
        res = self.client.post("/api/login", {"username": "testuser", "password": "wrongpass"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"success": False, "message": "用户名或密码错误"})

    def test_login_unknown_user(self):
        res = self.client.post("/api/login", {"username": "nobody", "password": "password123"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"success": False, "message": "用户名或密码错误"})

    def test_login_with_legacy_bcrypt_hash(self):
        """旧 FastAPI 写入的裸 $2b$12$ 哈希(无 Django 前缀)必须能直接验证通过。"""
        user = User.objects.create_user("legacyuser", "password123", nickname="旧用户")
        raw_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
        User.objects.filter(id=user.id).update(password=raw_hash)  # 绕过 set_password,模拟旧数据

        res = self.client.post("/api/login", {"username": "legacyuser", "password": "password123"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["user"]["nickname"], "旧用户")

    def test_profile_update(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register(username="profileuser", nickname="原名")
        user_id = User.objects.get(username="profileuser").id

        with patch("apps.users.views.save_image", return_value="assets/new-avatar.jpg"):
            res = self.client.put(
                "/api/user/profile",
                {"user_id": user_id, "nickname": "新名字", "avatar": make_avatar()},
                format="multipart",
            )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["user"]["nickname"], "新名字")
        self.assertEqual(res.data["user"]["avatar_url"], "assets/new-avatar.jpg")

    def test_profile_update_without_avatar(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register(username="profileuser2", nickname="原名")
        user_id = User.objects.get(username="profileuser2").id

        res = self.client.put("/api/user/profile", {"user_id": user_id, "nickname": "新名字"}, format="multipart")
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["user"]["nickname"], "新名字")
        self.assertEqual(res.data["user"]["avatar_url"], "assets/test-avatar.jpg")  # 头像不变

    def test_profile_nickname_empty(self):
        res = self.client.put("/api/user/profile", {"user_id": 1, "nickname": ""}, format="multipart")
        self.assertEqual(res.data, {"success": False, "message": "昵称不能为空"})

    def test_profile_user_not_found(self):
        res = self.client.put("/api/user/profile", {"user_id": 99999, "nickname": "新名字"}, format="multipart")
        self.assertEqual(res.data, {"success": False, "message": "用户不存在"})

    def test_public_user_profile(self):
        with patch("apps.users.views.save_image", return_value="assets/test-avatar.jpg"):
            self.register(username="pubuser", nickname="公开用户")
        user_id = User.objects.get(username="pubuser").id

        res = self.client.get(f"/api/users/{user_id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["user"]["username"], "pubuser")

        res = self.client.get("/api/users/99999")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"detail": "User not found"})


class AssetServingTests(TestCase):
    """/assets/{filename} 静态文件路由,与原 FastAPI 行为一致。"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        with open(os.path.join(self.tmp_dir, "pic.jpg"), "wb") as f:
            f.write(b"fake-image-bytes")

    def test_asset_found(self):
        with override_settings(ASSETS_DIR=self.tmp_dir):
            res = self.client.get("/assets/pic.jpg")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"".join(res.streaming_content), b"fake-image-bytes")

    def test_asset_not_found(self):
        with override_settings(ASSETS_DIR=self.tmp_dir):
            res = self.client.get("/assets/missing.jpg")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {"detail": "Image not found"})

    def test_asset_path_traversal_blocked(self):
        """文件名含路径时只取 basename,不能越出 assets 目录。"""
        with override_settings(ASSETS_DIR=self.tmp_dir):
            res = self.client.get("/assets/../manage.py")
        # basename 为 manage.py,不存在于 assets 目录 → 404
        self.assertEqual(res.status_code, 404)


class SaveImageTests(TestCase):
    """utils.save_image:行为与原 backend/utils.py 一致。"""

    def test_save_image_returns_relative_path_and_writes_file(self):
        tmp_dir = tempfile.mkdtemp()
        with override_settings(ASSETS_DIR=tmp_dir):
            path = save_image(make_avatar(name="photo.png", fmt="PNG", content_type="image/png"))
        self.assertTrue(path.startswith("assets/"))
        self.assertTrue(path.endswith(".png"))
        saved = os.path.join(tmp_dir, os.path.basename(path))
        self.assertTrue(os.path.exists(saved))
        # 保存内容必须是合法图片(转 RGB 存 JPEG 后仍可被 PIL 打开)
        with Image.open(saved) as img:
            self.assertEqual(img.format, "JPEG")

    def test_save_image_rejects_bad_file(self):
        tmp_dir = tempfile.mkdtemp()
        with override_settings(ASSETS_DIR=tmp_dir):
            with self.assertRaises(ValueError) as ctx:
                save_image(SimpleUploadedFile("a.txt", b"not an image", content_type="text/plain"))
        self.assertTrue(str(ctx.exception).startswith("不支持的文件类型"))


class BearerAuthTests(TestCase):
    """BearerTokenAuthentication:JWT 解析与 401 行为。"""

    def setUp(self):
        self.user = User.objects.create_user("authuser", "password123")
        self.factory = APIRequestFactory()

    def test_valid_bearer_token(self):
        token = create_access_token({"sub": str(self.user.id)})
        request = self.factory.get("/api/users/1", HTTP_AUTHORIZATION=f"Bearer {token}")
        auth_user, _ = BearerTokenAuthentication().authenticate(request)
        self.assertEqual(auth_user, self.user)

    def test_no_header_returns_none(self):
        request = self.factory.get("/api/users/1")
        self.assertIsNone(BearerTokenAuthentication().authenticate(request))

    def test_invalid_token_raises_401(self):
        request = self.factory.get("/api/users/1", HTTP_AUTHORIZATION="Bearer garbage")
        with self.assertRaises(exceptions.AuthenticationFailed):
            BearerTokenAuthentication().authenticate(request)

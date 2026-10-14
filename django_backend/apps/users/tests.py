"""
用户模块测试
"""
from django.test import TestCase, tag

from rest_framework.test import APIClient
from apps.users.models import User

@tag("db")
class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='zzy',password='zzy123456')

    def test_login_success(self):
        client = APIClient()
        resp =client.post("/api/login",{"username":"zzy","password":"zzy123456"},format="json")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(data["success"],True)
        self.assertIn( "token",data)

    def test_login_wrong_pwd(self):
        """错误密码"""
        client = APIClient()
        resp = client.post("/api/login",{"username":"zzy","password":"123"},format="json")
        data = resp.json()
        self.assertFalse(data["success"])
        self.assertIn("用户名或密码错误",data["message"])

    def test_login_wrong_username(self):
        """不存在的账号"""
        client = APIClient()
        resp = client.post("/api/login",{"username":"zz33y","password":"1323zt"},format="json")
        data = resp.json()
        self.assertFalse(data["success"])
        self.assertIn("用户名或密码错误",data["message"])

    def test_login_missing_field(self):
        """缺少 password:校验失败。"""

        client = APIClient()
        resp = client.post("/api/login", {"username": "zzy"}, format="json")
        data = resp.json()
        self.assertFalse(data["success"])



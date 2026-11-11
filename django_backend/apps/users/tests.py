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
        resp = client.post("/api/login", {"username":"zzy","password":"zzy123456"}, format="json")
        data = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["code"], 200)
        self.assertEqual(set(data), {"code", "message", "data"})
        self.assertIn("token", data["data"])

    def test_admin_login_and_user_routes(self):
        user = User.objects.get(username='zzy')
        client = APIClient()
        credentials = {"username": "zzy", "password": "zzy123456"}
        self.assertEqual(client.post('/api/admin/login', credentials, format='json').status_code, 403)
        user.role = 0
        user.save(update_fields=['role'])
        response = client.post('/api/admin/login', credentials, format='json')
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['data']['token'])
        self.assertEqual(client.get('/api/admin/users/').status_code, 200)
        response = client.patch(f'/api/admin/users/{user.id}/role/', {'role': 0}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 200)

    def test_empty_success_payload_is_object(self):
        from apps.common.response import ok
        self.assertEqual(ok().data, {'code': 200, 'message': '操作成功', 'data': {}})

    def test_login_wrong_pwd(self):
        """错误密码"""
        client = APIClient()
        resp = client.post("/api/login", {"username":"zzy","password":"123"}, format="json")
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(data["code"], 400)
        self.assertIn("用户名或密码错误", data["message"])

    def test_login_wrong_username(self):
        """不存在的账号"""
        client = APIClient()
        resp = client.post("/api/login", {"username":"zz33y","password":"1323zt"}, format="json")
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(data["code"], 400)
        self.assertIn("用户名或密码错误", data["message"])

    def test_login_missing_field(self):
        """缺少 password:校验失败。"""

        client = APIClient()
        resp = client.post("/api/login", {"username": "zzy"}, format="json")
        data = resp.json()
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(data["code"], 200)



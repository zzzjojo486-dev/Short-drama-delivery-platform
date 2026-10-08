"""
JWT 认证:移植自原 backend/jwt_auth.py(HS256、有效期 7 天、sub=user id),
以 DRF 认证类形式接入,兼容 Authorization: Bearer <token> 请求头。
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from jose import JWTError, jwt
from rest_framework import authentication, exceptions

# 与原 jwt_auth.py 保持一致的配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT 访问令牌。"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT 令牌,失败返回 None。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class BearerTokenAuthentication(authentication.BaseAuthentication):
    """解析 Authorization: Bearer <token>(兼容 Token <token>),注入 request.user。

    原 FastAPI 接口从不强制鉴权(全局 AllowAny),该认证仅在请求带头时生效;
    无效令牌返回 401 {"detail": "无效的认证令牌"},与原 jwt_auth.py 行为一致。
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8", errors="ignore")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] not in ("Bearer", "Token"):
            return None

        token = parts[1]
        payload = verify_token(token)
        if payload is None:
            raise exceptions.AuthenticationFailed("无效的认证令牌")

        # python-jose 要求 sub 为字符串,签发时已转 str,这里转回 int
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise exceptions.AuthenticationFailed("无效的认证令牌")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist:
            raise exceptions.AuthenticationFailed("用户不存在")
        return user, token

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """用户公开信息(id/username/nickname/avatar_url),与原接口响应字段一致。"""

    class Meta:
        model = User
        fields = ("id", "username", "nickname", "avatar_url")


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    """注册请求(multipart form)。校验消息与原 auth_service.register_user 逐字一致。"""

    username = serializers.CharField()
    password = serializers.CharField()
    nickname = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        username = value.strip()
        if len(username) < 3:
            raise serializers.ValidationError("用户名至少需要3个字符")
        if len(username) > 50:
            raise serializers.ValidationError("用户名不能超过50个字符")
        return username

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("密码至少需要6个字符")
        if len(value) > 128:
            raise serializers.ValidationError("密码不能超过128个字符")
        return value

    def validate_nickname(self, value):
        if value:
            nickname = value.strip()
            if len(nickname) > 50:
                raise serializers.ValidationError("昵称不能超过50个字符")
            return nickname
        return value

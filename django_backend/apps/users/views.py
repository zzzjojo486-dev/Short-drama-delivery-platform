"""
用户与认证模块视图。

所有接口统一三层响应 {code, message, data}:code 与 HTTP 状态码一致。
- 成功:HTTP 200 + {code:200, message, data}
- 业务/参数错误:HTTP 400;无权限 403;不存在 404;认证失败 401
"""
import json
import os

import bcrypt
import httpx
from django.conf import settings
from django.db import OperationalError
from django.db.models import Q
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
from rest_framework.views import APIView

from apps.common.response import fail, ok

from apps.post.models import Notification, Post
from .auth import create_access_token
from .models import Follow, Message, User
from .permissions import IsAdminStaff, STAFF_ROLES, IsSuperAdminStaff
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
    """取序列化器的第一条错误信息,作为三层响应的 message 文本。"""
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
            return fail(400, first_error(serializer))

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.filter(username=username).first()
        except OperationalError:
            return fail(400, "用户不存在")

        if user and verify_password(user, password):
            token = create_access_token(data={"sub": str(user.id)})
            return ok({"user": UserSerializer(user).data, "token": token}, message="登录成功")
        return fail(400, "用户名或密码错误")

class AdminLoginView(APIView):
    """POST /api/admin/login - 后台登录(JSON body: username/password)。"""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return fail(400, first_error(serializer))

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.filter(username=username).first()

        except OperationalError:
            return fail(400, "用户不存在")

        if user and verify_password(user, password):
            if user.role not in STAFF_ROLES:
                return fail(403, '用户权限不足')
            token = create_access_token(data={"sub": str(user.id)})
            return ok({"user": UserSerializer(user).data, "token": token}, message="登录成功")
        return fail(400, "用户名或密码错误")



class RegisterView(APIView):
    """POST /api/register - 用户注册(multipart form,头像必填)。"""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return fail(400, first_error(serializer))

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        nickname = serializer.validated_data.get("nickname")

        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            return fail(400, "请上传头像")

        # 与原版顺序一致:先保存头像,再检查用户名是否已存在
        try:
            avatar_url = save_image(avatar_file)
        except ValueError as e:
            return fail(400, str(e))
        except Exception:
            return fail(400, "头像上传失败")

        # 昵称缺省为用户名(与原版一致)
        nickname = (nickname or username).strip()

        try:
            if User.objects.filter(username=username).exists():
                return fail(400, "用户名已存在，请选择其他用户名")
            User.objects.create_user(
                username=username, password=password, nickname=nickname, avatar_url=avatar_url
            )
        except OperationalError:
            return fail(400, "Database connection failed")
        except Exception:
            return fail(400, "Registration failed")

        return ok(message="注册成功")


class ProfileView(APIView):
    """PUT /api/user/profile - 更新个人资料(multipart form:user_id、nickname、avatar 可选)。"""

    def put(self, request):
        user_id = request.data.get("user_id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return fail(400, "用户不存在")

        nickname = (request.data.get("nickname") or "").strip()
        avatar_file = request.FILES.get("avatar")

        # 输入验证(与原 update_user_profile 一致)
        if len(nickname) < 1:
            return fail(400, "昵称不能为空")
        if len(nickname) > 50:
            return fail(400, "昵称不能超过50个字符")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return fail(404, "用户不存在")
        except OperationalError:
            return fail(400, "Database connection failed")

        if avatar_file:
            try:
                user.avatar_url = save_image(avatar_file)
            except ValueError as e:
                return fail(400, str(e))
            except Exception:
                return fail(400, "Update failed")

        user.nickname = nickname
        try:
            user.save()
        except OperationalError:
            return fail(400, "Database connection failed")
        except Exception:
            return fail(400, "Update failed")

        return ok({"user": UserSerializer(user).data}, message="资料更新成功")


class PublicUserView(APIView):
    """GET /api/users/{user_id} - 用户公开资料。"""

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return fail(404, "User not found")
        return ok({"user": UserSerializer(user).data})


def serve_asset(request, filename):
    """GET /assets/{filename} - 与原 FastAPI 静态文件路由一致,取仓库根 assets/ 目录文件。"""
    path = os.path.join(str(settings.ASSETS_DIR), os.path.basename(filename))
    if os.path.isfile(path):
        response = FileResponse(open(path, "rb"))
        response["Access-Control-Allow-Origin"] = "*"
        return response
    return JsonResponse({"detail": "Image not found"}, status=404)


"""后台"""

class AdminListView(APIView):
    """GET /api/admin/users/ - 后台用户列表,仅后台角色可访问。"""
    permission_classes = [IsAdminStaff]
    def get(self, request):
        users = User.objects.all().order_by('-id')
        return ok({"users": UserSerializer(users, many=True).data})

class AdminUserRoleView(APIView):
    permission_classes = [IsSuperAdminStaff]

    def patch(self, request,user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return fail(404, "用户不存在")

        role = request.data.get("role")
        try:
            role = int(role)
        except (TypeError, ValueError):
            return fail(400, "角色权限参数错误")

        if role not in (0,1,2,3):
            return fail(400, '取值错误')
        user.role = role
        user.save()
        return ok({"user": UserSerializer(user).data}, message="角色已更新")


"""关注块(B):移植自原 backend/user_service.py + server.py 路由。"""

class FollowView(APIView):
    """POST /api/users/{user_id}/follow - 关注。body:{user_id(发起者)}。"""
    def post(self, request, user_id):
        follower_id = request.data.get("user_id")
        try:
            follower_id = int(follower_id)
        except (TypeError, ValueError):
            return fail(400, "用户不存在")
        if follower_id == user_id:
            return fail(400, "Cannot follow yourself")
        if Follow.objects.filter(follower_id=follower_id, followed_id=user_id).exists():
            return fail(400, "Already following")
        Follow.objects.create(follower_id_id=follower_id, followed_id_id=user_id)
        return ok(message="Followed successfully")

class UnfollowView(APIView):
    """POST /api/users/{user_id}/unfollow - 取消关注。body:{user_id}。"""
    def post(self, request, user_id):
        follower_id = request.data.get("user_id")
        Follow.objects.filter(follower_id=follower_id, followed_id=user_id).delete()
        return ok(message="Unfollowed successfully")

class IsFollowingView(APIView):
    """GET /api/users/{user_id}/is_following - 是否已关注。query:current_user_id。"""
    def get(self, request, user_id):
        follower_id = request.query_params.get("current_user_id")
        following = bool(follower_id and
                         Follow.objects.filter(follower_id=follower_id, followed_id=user_id).exists())
        return ok({"is_following": following})

class FollowersView(APIView):
    """GET /api/users/{user_id}/followers - 粉丝列表。query:current_user_id。"""
    def get(self, request, user_id):
        current_user_id = request.query_params.get("current_user_id")
        qs = Follow.objects.filter(followed_id=user_id).select_related("follower_id").order_by("-created_at")
        data = []
        for f in qs:
            u = f.follower_id
            is_following = False
            if current_user_id:
                is_following = Follow.objects.filter(
                    follower_id=current_user_id, followed_id=u.id).exists()
            data.append({
                "id": u.id, "username": u.username, "nickname": u.nickname,
                "avatar_url": u.avatar_url, "is_following": is_following,
            })
        return ok({"followers": data})

class FollowingView(APIView):
    """GET /api/users/{user_id}/following - 关注列表。query:current_user_id。"""
    def get(self, request, user_id):
        current_user_id = request.query_params.get("current_user_id")
        qs = Follow.objects.filter(follower_id=user_id).select_related("followed_id").order_by("-created_at")
        data = []
        for f in qs:
            u = f.followed_id
            is_following = False
            if current_user_id:
                is_following = Follow.objects.filter(
                    follower_id=current_user_id, followed_id=u.id).exists()
            data.append({
                "id": u.id, "username": u.username, "nickname": u.nickname,
                "avatar_url": u.avatar_url, "is_following": is_following,
            })
        return ok({"following": data})

class FollowCountsView(APIView):
    """GET /api/users/{user_id}/counts - 粉丝/关注数。"""
    def get(self, request, user_id):
        return ok({"counts": {
            "followers": Follow.objects.filter(followed_id=user_id).count(),
            "following": Follow.objects.filter(follower_id=user_id).count(),
        }})


"""私信+通知块(C):移植自原 backend/message_service.py + server.py 路由。"""

class SendMessageView(APIView):
    """POST /api/messages - 发私信。body:{sender_id, receiver_id, content}。"""
    def post(self, request):
        sender_id = request.data.get("sender_id")
        receiver_id = request.data.get("receiver_id")
        content = (request.data.get("content") or "").strip()
        if not content:
            return fail(400, "消息内容不能为空")
        if len(content) > 5000:
            return fail(400, "消息内容不能超过5000个字符")
        if sender_id == receiver_id:
            return fail(400, "不能给自己发消息")
        if not User.objects.filter(id=receiver_id).exists():
            return fail(404, "接收者不存在")
        Message.objects.create(sender_id_id=sender_id, receiver_id_id=receiver_id, content=content)
        return ok(message="Message sent successfully")

class ConversationMessagesView(APIView):
    """GET /api/messages/conversation/{other_user_id} - 与某人的历史私信。query:user_id,limit,offset。"""
    def get(self, request, other_user_id):
        user_id = request.query_params.get("user_id")
        try:
            limit = int(request.query_params.get("limit", 50))
            offset = int(request.query_params.get("offset", 0))
        except (TypeError, ValueError):
            limit, offset = 50, 0
        qs = Message.objects.filter(
            Q(sender_id=user_id, receiver_id=other_user_id) |
            Q(sender_id=other_user_id, receiver_id=user_id)
        ).select_related("sender_id", "receiver_id").order_by("-created_at")
        msgs = list(qs[offset:offset + limit])
        msgs.reverse()  # 按时间正序返回(与原版一致)
        data = []
        for m in msgs:
            data.append({
                "id": m.id,
                "sender_id": m.sender_id_id,
                "receiver_id": m.receiver_id_id,
                "content": m.content,
                "is_read": m.is_read,
                "created_at": m.created_at,
                "sender_name": m.sender_id.nickname,
                "sender_avatar": m.sender_id.avatar_url,
                "receiver_name": m.receiver_id.nickname,
                "receiver_avatar": m.receiver_id.avatar_url,
            })
        return ok({"messages": data})

class ConversationsView(APIView):
    """GET /api/messages/conversations - 会话列表。query:user_id。"""
    def get(self, request):
        user_id = int(request.query_params.get("user_id"))
        msgs = list(Message.objects.filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).select_related("sender_id", "receiver_id").order_by("-created_at"))
        # 每会话取最新一条(desc 下首见即最新),保持 desc 顺序
        latest_by_other = {}
        for m in msgs:
            other = m.receiver_id_id if m.sender_id_id == user_id else m.sender_id_id
            if other not in latest_by_other:
                latest_by_other[other] = m
        results = []
        for other_id, last in latest_by_other.items():
            other_user = User.objects.filter(id=other_id).values("id", "username", "nickname", "avatar_url").first()
            unread = Message.objects.filter(sender_id=other_id, receiver_id=user_id, is_read=False).count()
            results.append({
                "user": other_user,
                "last_message": {"content": last.content, "is_read": last.is_read, "sender_id": last.sender_id_id},
                "unread_count": unread,
                "timestamp": last.created_at,
            })
        return ok({"conversations": results})

class MarkMessagesReadView(APIView):
    """PUT /api/messages/read - 已读该 sender 发来的消息。body:{user_id, sender_id}。"""
    def put(self, request):
        user_id = request.data.get("user_id")
        sender_id = request.data.get("sender_id")
        Message.objects.filter(sender_id=sender_id, receiver_id=user_id, is_read=False).update(is_read=True)
        return ok()

class UnreadCountView(APIView):
    """GET /api/messages/unread/count - 未读私信+未读通知总数。query:user_id。"""
    def get(self, request):
        user_id = request.query_params.get("user_id")
        msg = Message.objects.filter(receiver_id=user_id, is_read=False).count()
        ntfy = Notification.objects.filter(receiver_id=user_id, is_read=False).count()
        return ok({"count": msg + ntfy})

class NotificationsView(APIView):
    """GET /api/notifications - 通知列表。query:user_id。"""
    def get(self, request):
        user_id = request.query_params.get("user_id")
        qs = Notification.objects.filter(receiver_id=user_id).select_related("sender_id").order_by("-created_at")
        data = []
        for n in qs:
            post = None
            if n.target_id:
                post = Post.objects.filter(id=n.target_id).values("title", "image_url").first()
            data.append({
                "id": n.id,
                "receiver_id": n.receiver_id_id,
                "sender_id": n.sender_id_id,
                "type": n.type,
                "target_id": n.target_id,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "sender_name": n.sender_id.nickname,
                "sender_avatar": n.sender_id.avatar_url,
                "post_title": post["title"] if post else None,
                "post_image": post["image_url"] if post else None,
            })
        return ok({"notifications": data})

class MarkNotificationsReadView(APIView):
    """PUT /api/notifications/read - 通知全部已读。body:{user_id}。"""
    def put(self, request):
        user_id = request.data.get("user_id")
        Notification.objects.filter(receiver_id=user_id, is_read=False).update(is_read=True)
        return ok()


"""AI 润色块(D):移植自原 server.py 的 ai/polish(流式转发 Ollama)。"""

class AIPolishView(APIView):
    """POST /api/ai/polish - 流式拉取 Ollama 改写文案。body:{content}。"""
    def post(self, request):
        content = (request.data.get("content") or "").strip()
        if not content:
            return fail(400, "Content is required")
        prompt = f"""请将以下文本改写成典型的小红书文案风格：
1. 标题要吸引眼球，使用爆款关键词
2. 正文包含大量Emoji表情
3. 语气活泼、热情、真诚，像在和闺蜜聊天
4. 适当添加标签（hashtags）
5. 排版清晰，分段友好

原文内容：
{content}

请直接输出改写后的文案，不要包含其他解释性文字。"""

        def generate():
            try:
                with httpx.Client() as client:
                    with client.stream(
                        "POST",
                        "http://localhost:11434/api/generate",
                        json={"model": "gemma3n:e4b", "prompt": prompt, "stream": True},
                        timeout=60.0,
                    ) as response:
                        if response.status_code != 200:
                            yield f"Error: Ollama returned status {response.status_code}"
                            return
                        for line in response.iter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
            except httpx.ConnectError:
                yield "Error: Could not connect to local Ollama service."
            except Exception as e:
                yield f"Error: {str(e)}"

        return StreamingHttpResponse(generate(), content_type="text/plain")


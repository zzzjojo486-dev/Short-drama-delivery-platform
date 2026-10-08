from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx
import json
from backend.auth_service import AuthService
from backend.post_service import PostService
from backend.message_service import MessageService
from backend.user_service import UserService
from backend.database import db
from backend.utils import save_image

app = FastAPI()

# Enable CORS for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Default Vite port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic Models
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    nickname: Optional[str] = None

class CommentCreate(BaseModel):
    user_id: int
    content: str

class InteractionCreate(BaseModel):
    user_id: int

class DeletePost(BaseModel):
    user_id: int

class UpdateVisibility(BaseModel):
    user_id: int
    is_private: bool

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MarkRead(BaseModel):
    user_id: int
    sender_id: int

class AIPolishRequest(BaseModel):
    content: str

# --- Auth Routes ---
@app.post("/api/login")
async def login(user_data: UserLogin):
    user, msg = AuthService.login_user(user_data.username, user_data.password)
    if user:
        # 生成JWT令牌（可选，如果前端需要）
        from backend.jwt_auth import create_access_token
        token = create_access_token(data={"sub": user["id"]})
        # return {"success": True, "user": user, "token": token}
        return {"success": True, "user": user}
    return {"success": False, "message": msg}

@app.post("/api/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    nickname: Optional[str] = Form(None),
    avatar: UploadFile = File(...)
):
    success, msg = AuthService.register_user(username, password, nickname, avatar)
    return {"success": success, "message": msg}

@app.put("/api/user/profile")
async def update_profile(
    user_id: int = Form(...), 
    nickname: str = Form(...), 
    avatar: UploadFile = File(None)
):
    success, msg = AuthService.update_user_profile(user_id, nickname, avatar)
    if success:
        user = AuthService.get_user_by_id(user_id)
        return {"success": True, "user": user}
    return {"success": False, "message": msg}

# --- Post Routes ---
@app.get("/api/posts")
async def get_posts(
    limit: int = 20, 
    offset: int = 0, 
    search: Optional[str] = None, 
    category: Optional[str] = None
):
    return PostService.get_posts(limit, offset, search, category)

@app.get("/api/posts/{post_id}")
async def get_post_detail(post_id: int, user_id: Optional[int] = None):
    try:
        post = PostService.get_post_by_id(post_id, user_id)
        if not post:
            print(f"Post {post_id} not found (user_id: {user_id})")
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_post_detail: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/posts")
async def create_post(
    user_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    images: List[UploadFile] = File(None),
    video: UploadFile = File(None)
):
    # Ensure at least images or video + cover image is provided
    if not images and not video:
        raise HTTPException(status_code=400, detail="Images or Video required")

    success, msg = PostService.create_post(user_id, title, content, images, category, video)
    return {"success": success, "message": msg}

@app.get("/api/posts/user/{user_id}")
async def get_user_posts(user_id: int, current_user_id: Optional[int] = None):
    return PostService.get_user_posts(user_id, current_user_id)

@app.get("/api/posts/user/{user_id}/liked")
async def get_user_liked_posts(user_id: int):
    return PostService.get_user_liked_posts(user_id)

@app.get("/api/posts/user/{user_id}/collected")
async def get_user_collected_posts(user_id: int):
    return PostService.get_user_collected_posts(user_id)

# New routes for deletion and visibility
@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int, user_data: DeletePost):
    success, msg = PostService.delete_post(post_id, user_data.user_id)
    return {"success": success, "message": msg}

@app.put("/api/posts/{post_id}/visibility")
async def update_visibility(post_id: int, data: UpdateVisibility):
    success, msg = PostService.update_post_visibility(post_id, data.user_id, data.is_private)
    return {"success": success, "message": msg}


# --- Interaction Routes ---
@app.post("/api/posts/{post_id}/like")
async def toggle_like(post_id: int, user_id_data: InteractionCreate):
    # Expecting JSON body: {"user_id": 123}
    user_id = user_id_data.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
        
    success, msg = PostService.toggle_like(user_id, post_id)
    return {"success": success, "message": msg}

@app.post("/api/posts/{post_id}/collect")
async def toggle_collection(post_id: int, user_id_data: InteractionCreate):
    user_id = user_id_data.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
        
    success, msg = PostService.toggle_collection(user_id, post_id)
    return {"success": success, "message": msg}

@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: int, user_id: Optional[int] = None):
    return PostService.get_comments(post_id, user_id)

@app.post("/api/posts/{post_id}/comments")
async def add_comment(post_id: int, comment_data: CommentCreate):
    success = PostService.add_comment(comment_data.user_id, post_id, comment_data.content)
    return {"success": success}

@app.post("/api/comments/{comment_id}/like")
async def toggle_comment_like(comment_id: int, user_id_data: InteractionCreate):
    user_id = user_id_data.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
        
    success, msg = PostService.toggle_comment_like(user_id, comment_id)
    return {"success": success, "message": msg}

# --- Static Files ---
@app.get("/assets/{filename}")
async def get_image(filename: str):
    path = f"assets/{filename}"
    if os.path.exists(path):
        response = FileResponse(path)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    raise HTTPException(status_code=404, detail="Image not found")

# --- User Routes ---
@app.get("/api/users/{user_id}")
async def get_public_user_profile(user_id: int):
    user = AuthService.get_user_by_id(user_id)
    if user:
        # Remove sensitive info if any (though get_user_by_id currently only returns safe fields)
        return {"success": True, "user": user}
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/{user_id}/follow")
async def follow_user(user_id: int, interaction: InteractionCreate):
    follower_id = interaction.user_id
    success, msg = UserService.follow_user(follower_id, user_id)
    return {"success": success, "message": msg}

@app.post("/api/users/{user_id}/unfollow")
async def unfollow_user(user_id: int, interaction: InteractionCreate):
    follower_id = interaction.user_id
    success, msg = UserService.unfollow_user(follower_id, user_id)
    return {"success": success, "message": msg}

@app.get("/api/users/{user_id}/is_following")
async def is_following(user_id: int, current_user_id: int):
    is_following = UserService.is_following(current_user_id, user_id)
    return {"success": True, "is_following": is_following}

@app.get("/api/users/{user_id}/followers")
async def get_followers(user_id: int, current_user_id: Optional[int] = None):
    followers = UserService.get_followers(user_id, current_user_id)
    return {"success": True, "followers": followers}

@app.get("/api/users/{user_id}/following")
async def get_following(user_id: int, current_user_id: Optional[int] = None):
    following = UserService.get_following(user_id, current_user_id)
    return {"success": True, "following": following}

@app.get("/api/users/{user_id}/counts")
async def get_follow_counts(user_id: int):
    counts = UserService.get_follow_counts(user_id)
    return {"success": True, "counts": counts}

# --- Message Routes ---
@app.post("/api/messages")
async def send_message(msg_data: MessageCreate):
    success, msg = MessageService.send_message(msg_data.sender_id, msg_data.receiver_id, msg_data.content)
    return {"success": success, "message": msg}

@app.get("/api/messages/conversations")
async def get_conversations(user_id: int):
    conversations = MessageService.get_conversations(user_id)
    return {"success": True, "conversations": conversations}

@app.get("/api/messages/conversation/{other_user_id}")
async def get_conversation(other_user_id: int, user_id: int, limit: int = 50, offset: int = 0):
    messages = MessageService.get_conversation(user_id, other_user_id, limit, offset)
    return {"success": True, "messages": messages}

@app.put("/api/messages/read")
async def mark_messages_read(data: MarkRead):
    success = MessageService.mark_messages_read(data.user_id, data.sender_id)
    return {"success": success}

@app.get("/api/messages/unread/count")
async def get_unread_count(user_id: int):
    count = MessageService.get_total_unread_count(user_id)
    return {"success": True, "count": count}

@app.get("/api/notifications")
async def get_notifications(user_id: int):
    notifications = MessageService.get_notifications(user_id)
    return {"success": True, "notifications": notifications}

@app.put("/api/notifications/read")
async def mark_notifications_read(data: InteractionCreate):
    # Reusing InteractionCreate just for user_id
    success = MessageService.mark_notifications_read(data.user_id)
    return {"success": success}

# --- AI Polish Route ---
@app.post("/api/ai/polish")
async def ai_polish(request: AIPolishRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")

    prompt = f"""请将以下文本改写成典型的小红书文案风格：
1. 标题要吸引眼球，使用爆款关键词
2. 正文包含大量Emoji表情
3. 语气活泼、热情、真诚，像在和闺蜜聊天
4. 适当添加标签（hashtags）
5. 排版清晰，分段友好

原文内容：
{request.content}

请直接输出改写后的文案，不要包含其他解释性文字。"""

    async def generate():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "gemma3n:e4b",
                        "prompt": prompt,
                        "stream": True
                    },
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        yield f"Error: Ollama returned status {response.status_code}"
                        return

                    async for line in response.aiter_lines():
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

    return StreamingResponse(generate(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

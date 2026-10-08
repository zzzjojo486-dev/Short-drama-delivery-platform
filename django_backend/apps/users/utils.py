"""
图片校验与保存:移植自原 backend/utils.py,适配 Django 的 UploadedFile。

保持与原 FastAPI 后端完全一致的行为:
- 扩展名白名单 {.jpg, .jpeg, .png, .gif, .webp},大小 ≤100MB
- PIL 校验图片内容,扩展名与内容匹配
- UUID 文件名,统一转 RGB 存 JPEG(quality=85),存入仓库根 assets/ 目录
- 返回相对路径 "assets/<uuid>.<ext>"(DB 存储格式与原版一致)
"""
import os
import uuid

from django.conf import settings
from PIL import Image

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


def validate_image_file(uploaded_file):
    """Validate uploaded image file."""
    # 检查文件名
    if not uploaded_file.name:
        return False, "文件名不能为空"

    # 检查文件扩展名
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"

    # 检查文件大小
    file_content = uploaded_file.read()
    uploaded_file.seek(0)  # 重置文件指针

    if len(file_content) > MAX_FILE_SIZE:
        return False, f"图片大小不能超过 {MAX_FILE_SIZE // (1024 * 1024)}MB"

    if len(file_content) == 0:
        return False, "文件不能为空"

    # 验证文件内容(检查是否为真实图片)
    try:
        # 使用 PIL 验证图片
        img = Image.open(uploaded_file)
        img.verify()

        # 使用 format 进行格式检查
        image_type = img.format.lower() if img.format else None

        uploaded_file.seek(0)  # 重置文件指针

        # 检查 MIME 类型
        if uploaded_file.content_type and uploaded_file.content_type not in ALLOWED_MIME_TYPES:
            return False, "文件类型不匹配"

        if not image_type:
            return False, "无法识别图片格式"

        # 验证扩展名与内容匹配
        ext_to_type = {
            '.jpg': 'jpeg', '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.webp': 'webp'
        }
        expected_type = ext_to_type.get(file_ext)
        if expected_type and image_type != expected_type:
            return False, "文件扩展名与内容不匹配"

    except Exception as e:
        return False, f"无效的图片文件: {str(e)}"

    return True, "验证通过"


def save_image(uploaded_file):
    """Save uploaded image to assets directory and return the relative path."""
    # 验证文件
    is_valid, message = validate_image_file(uploaded_file)
    if not is_valid:
        raise ValueError(message)

    image_dir = str(settings.ASSETS_DIR)
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # 使用安全的文件名(只保留扩展名)
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    # 确保扩展名在允许列表中
    if file_ext not in ALLOWED_EXTENSIONS:
        file_ext = '.jpg'  # 默认扩展名

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(image_dir, unique_filename)

    # 重新打开并保存图片(确保是有效图片)
    try:
        img = Image.open(uploaded_file)
        # 转换为 RGB 模式(处理 RGBA 等)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 保存图片
        img.save(file_path, 'JPEG', quality=85, optimize=True)
    except Exception:
        # 如果处理失败,尝试直接保存
        uploaded_file.seek(0)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

    # 与原版一致:DB 中存相对路径(统一正斜杠,兼容前端与 Streamlit)
    return f"assets/{unique_filename}"

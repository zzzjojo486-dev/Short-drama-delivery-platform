import streamlit as st
import base64
import os

def render_card(post, click_handler=None):
    """
    Render a single post card with Xiaohongshu style.
    """
    image_url = post.get('image_url')
    # Fix path for local Windows environment if needed, or use relative path
    # Assuming 'assets/filename.jpg'
    
    # Convert local image to base64 for embedding in HTML
    img_base64 = ""
    if image_url and os.path.exists(image_url):
        with open(image_url, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        img_src = f"data:image/jpeg;base64,{img_base64}"
    else:
        img_src = "https://via.placeholder.com/300x400?text=No+Image"
        
    user_avatar = "https://via.placeholder.com/24?text=U" # Default
    if post.get('avatar_url') and os.path.exists(post['avatar_url']):
         with open(post['avatar_url'], "rb") as f:
            avatar_base64 = base64.b64encode(f.read()).decode()
         user_avatar = f"data:image/jpeg;base64,{avatar_base64}"

    # Generate unique ID for the button
    btn_key = f"card_btn_{post['id']}"

    # Xiaohongshu-like Card HTML with strict layout control
    card_html = f"""
    <div class="xhs-card">
        <div class="card-image-container">
            <img src="{img_src}" class="card-img">
        </div>
        <div class="card-content">
            <div class="card-title">{post['title']}</div>
            <div class="card-footer">
                <div class="user-info">
                    <img src="{user_avatar}" class="avatar">
                    <span class="nickname">{post['nickname']}</span>
                </div>
                <div class="likes">
                    <span class="heart">🤍</span> {post['likes_count']}
                </div>
            </div>
        </div>
    </div>
    """
    
    # Inject CSS directly here if strict scoping is needed, but relying on app.py is cleaner.
    # However, to fix specific issues immediately:
    st.markdown("""
    <style>
    .xhs-card {
        background: #fff;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #f0f0f0;
        margin-bottom: 10px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .card-image-container {
        width: 100%;
        padding-top: 133%; /* 3:4 Aspect Ratio */
        position: relative;
        background: #f8f8f8;
    }
    .card-img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .card-content {
        padding: 8px 8px 12px 8px;
    }
    .card-title {
        font-size: 14px;
        font-weight: 500;
        color: #333;
        line-height: 1.4;
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 40px; /* Fixed height for 2 lines roughly */
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: #999;
    }
    .user-info {
        display: flex;
        align-items: center;
        flex: 1;
        overflow: hidden;
    }
    .avatar {
        width: 16px !important; /* Force small size */
        height: 16px !important;
        border-radius: 50%;
        margin-right: 4px;
        flex-shrink: 0;
        object-fit: cover;
        border: 1px solid #eee;
    }
    .nickname {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #666;
        font-size: 11px;
    }
    .likes {
        display: flex;
        align-items: center;
        margin-left: 4px;
        color: #666;
    }
    .heart {
        margin-right: 2px;
        font-size: 12px;
    }
    /* Customizing the Streamlit button to look like a transparent overlay or minimal link */
    div[data-testid="stHorizontalBlock"] button {
        border: none;
        background: transparent;
        color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(card_html, unsafe_allow_html=True)
    
    # Using a cleaner button below
    # To make it look integrated, we can use a full width button with minimal styling
    # or just "Check" icon.
    # For MVP, let's keep the "View" button but style it to be full width and subtle
    if st.button("查看详情", key=btn_key, use_container_width=True):
        if click_handler:
            click_handler(post['id'])


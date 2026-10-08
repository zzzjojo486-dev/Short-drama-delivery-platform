import streamlit as st
from streamlit_option_menu import option_menu
import os
import extra_streamlit_components as stx
from backend.database import db
from backend.auth_service import AuthService
from backend.post_service import PostService
from backend.user_service import UserService
from components.card import render_card

# Page Config
st.set_page_config(page_title="Mini-RedBook", page_icon="📕", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Global Settings */
    .stApp {
        background-color: #fbfbfb; /* Light gray background like XHS */
    }
    
    /* Move content up */
    .block-container {
        padding-top: 1rem !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #f0f0f0;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Button Styling */
    .stButton>button {
        background-color: white;
        color: #333;
        border: 1px solid #e6e6e6;
        border-radius: 20px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #f5f5f5;
        color: #ff2442;
        border-color: #ff2442;
    }
    
    /* Primary Action Button (Red) */
    .primary-btn button {
        background-color: #ff2442 !important;
        color: white !important;
        border: none !important;
    }
    
    /* XHS Card CSS */
    .xhs-card {
        background-color: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 8px;
        cursor: pointer;
    }
    .xhs-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .card-image-container {
        position: relative;
        width: 100%;
        padding-top: 133%; /* 3:4 Aspect Ratio placeholder, but img will override */
        overflow: hidden;
    }
    .card-img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover; /* Ensure image fills */
    }
    .xhs-card img {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 12px 12px 0 0; /* Only top corners rounded if we used explicit height */
    }
    /* Since we can't easily control aspect ratio with just img tag in simple HTML without container tricks,
       let's just let image flow naturally but limit max-height if needed */
    .card-image-container {
        padding-top: 0;
        height: auto;
    }
    .card-img {
        position: relative;
        height: auto;
    }
    
    .card-content {
        padding: 12px;
    }
    .card-title {
        font-size: 14px;
        font-weight: 600;
        color: #333;
        line-height: 1.4;
        margin-bottom: 8px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #666;
    }
    .user-info {
        display: flex;
        align-items: center;
    }
    .avatar {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 6px;
        object-fit: cover;
    }
    .nickname {
        max-width: 80px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .likes {
        display: flex;
        align-items: center;
    }
    .heart {
        color: #999;
        margin-right: 2px;
    }
    
    /* Search Input Styling */
    /* Target the container of the input to handle border and radius */
    div[data-baseweb="input"] {
        border-radius: 20px !important;
        background-color: #f5f5f5 !important;
        border: 1px solid transparent !important; 
    }
    
    /* Remove inner input styling conflicts */
    div[data-baseweb="input"] input {
        background-color: transparent !important;
    }
    
    /* Focus state */
    div[data-baseweb="input"]:focus-within {
        border-color: #ff2442 !important;
        background-color: white !important;
    }
    
    /* Form Submit Button Red */
    div[data-testid="stForm"] button {
        background-color: #ff2442;
        color: white;
        border: none;
    }
    
</style>
""", unsafe_allow_html=True)

# Cookie Manager for persistent session
cookie_manager = stx.CookieManager()

# Initialize Session State Logic
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'selected_post_id' not in st.session_state:
    st.session_state['selected_post_id'] = None
if 'show_login_view' not in st.session_state:
    st.session_state['show_login_view'] = False

# Check cookies for existing session
if not st.session_state['is_logged_in']:
    user_id_cookie = cookie_manager.get(cookie="user_id")
    if user_id_cookie:
        user = AuthService.get_user_by_id(user_id_cookie)
        if user:
            st.session_state['is_logged_in'] = True
            st.session_state['user_info'] = user

# --- Helper Functions ---
def init_db():
    """Initialize database tables from schema.sql"""
    conn = db.connect()
    if conn:
        try:
            with open('schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
            # Split by command (simple split by semicolon might be fragile but works for this schema)
            commands = schema.split(';')
            with conn.cursor() as cursor:
                for cmd in commands:
                    if cmd.strip():
                        cursor.execute(cmd)
            st.success("数据库初始化成功！")
        except Exception as e:
            st.error(f"数据库初始化失败: {e}")

def view_post_details(post_id):
    st.session_state['selected_post_id'] = post_id
    st.rerun()

def go_back_home():
    st.session_state['selected_post_id'] = None
    st.rerun()

def trigger_login_view():
    st.session_state['show_login_view'] = True
    # No rerun needed strictly if using the state in the render loop below, 
    # but rerun ensures immediate update.
    # However, option_menu might override if we are not careful.
    # We will use 'show_login_view' to override 'selected' variable logic.

# --- Sidebar ---
with st.sidebar:
    # XHS Logo Style
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #ff2442; font-family: sans-serif; font-size: 32px;">小红书</h1>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state['is_logged_in']:
        # Display User Avatar and Nickname centered
        user = st.session_state['user_info']
        
        # Use columns to center content roughly
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
             if user.get('avatar_url') and os.path.exists(user['avatar_url']):
                st.image(user['avatar_url'], width=80, use_container_width=False)
             else:
                st.markdown("<div style='font-size: 50px; text-align: center;'>👤</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='text-align: center; margin-bottom: 20px; font-weight: bold;'>{user['nickname']}</div>", unsafe_allow_html=True)
            
        
        selected = option_menu(
            menu_title=None, # Hide title
            options=["发现", "发布笔记", "个人中心"],
            icons=["house", "plus-circle", "person"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff"},
                "icon": {"color": "#666", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#f5f5f5", "color": "#333"},
                "nav-link-selected": {"background-color": "#fff", "color": "#ff2442", "font-weight": "bold", "border-left": "3px solid #ff2442"},
            }
        )
        
        st.markdown("---")
        if st.button("退出登录"):
            st.session_state['is_logged_in'] = False
            st.session_state['user_info'] = None
            cookie_manager.delete("user_id")
            st.rerun()
            
    else:
        # Guest Mode Sidebar
        st.markdown("""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; color: #666; font-size: 14px;">
            登录后可以发布笔记、评论和点赞哦
        </div>
        """, unsafe_allow_html=True)
        
        # Custom Red Login Button
        if st.button("立即登录 / 注册", type="primary", use_container_width=True):
             st.session_state['show_login_view'] = True
             st.rerun()

        selected = option_menu(
            menu_title=None,
            options=["发现", "登录/注册"],
            icons=["house", "person-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff"},
                "icon": {"color": "#666", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#f5f5f5", "color": "#333"},
                "nav-link-selected": {"background-color": "#fff", "color": "#ff2442", "font-weight": "bold", "border-left": "3px solid #ff2442"},
            }
        )

# --- Main Content ---

# 1. Detail Page View (Overrides other views if a post is selected)
if st.session_state['selected_post_id']:
    if st.button("← 返回首页"):
        go_back_home()
        
    post = PostService.get_post_by_id(st.session_state['selected_post_id'])
    if post:
        col1, col2 = st.columns([1, 1])
        with col1:
            if post['image_url'] and os.path.exists(post['image_url']):
                st.image(post['image_url'])
            else:
                st.image("https://via.placeholder.com/400x500?text=No+Image")
        
        with col2:
            st.title(post['title'])
            st.markdown(f"**作者:** {post['nickname']}")
            st.markdown(f"**时间:** {post['created_at']}")
            
            # Follow Button
            if st.session_state['is_logged_in'] and post['user_id'] != st.session_state['user_info']['id']:
                is_following = UserService.is_following(st.session_state['user_info']['id'], post['user_id'])
                col_btn, _ = st.columns([1, 3])
                with col_btn:
                    if is_following:
                        if st.button("已关注", key=f"unfollow_{post['user_id']}"):
                             UserService.unfollow_user(st.session_state['user_info']['id'], post['user_id'])
                             st.rerun()
                    else:
                        if st.button("关注", key=f"follow_{post['user_id']}", type="primary"):
                             UserService.follow_user(st.session_state['user_info']['id'], post['user_id'])
                             st.rerun()

            st.write(post['content'])
            
            st.markdown(f"### ❤️ {post['likes_count']} 点赞")
            if st.session_state['is_logged_in']:
                if st.button("点赞 / 取消点赞"):
                    success, msg = PostService.toggle_like(st.session_state['user_info']['id'], post['id'])
                    if success:
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("---")
            st.subheader("评论")
            comments = PostService.get_comments(post['id'])
            for c in comments:
                st.markdown(f"**{c['nickname']}:** {c['content']}")
            
            if st.session_state['is_logged_in']:
                with st.form("comment_form"):
                    new_comment = st.text_area("发表评论")
                    if st.form_submit_button("发送"):
                        if new_comment:
                            if PostService.add_comment(st.session_state['user_info']['id'], post['id'], new_comment):
                                st.success("评论成功！")
                                st.rerun()
                            else:
                                st.error("评论失败")
    else:
        st.error("笔记未找到")
        if st.button("返回"):
            go_back_home()

# 2. Normal Navigation Views
else:
    # Logic to handle Login view override
    if st.session_state.get('show_login_view', False):
        selected = "登录/注册"

    if selected == "发现":
        # Top Search Bar Area
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            search_query = st.text_input("", placeholder="探索更多内容", label_visibility="collapsed")
        
        # Categories
        categories = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]
        
        # Use option_menu horizontal for a cleaner tab-like look without radio circles
        selected_category = option_menu(
            None, 
            categories, 
            icons=None, 
            menu_icon=None, 
            default_index=0, 
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent", "margin": "0px"},
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "center", 
                    "margin": "0px 5px", 
                    "--hover-color": "#f0f0f0", 
                    "padding": "5px 12px", 
                    "color": "#666",
                    "border-radius": "15px", # Pill shape background on hover/selection if desired, or just text
                    "width": "auto"
                },
                "nav-link-selected": {
                    "background-color": "#f5f5f5", # Subtle background for selection
                    "color": "#333", 
                    "font-weight": "bold", 
                    "border-radius": "15px"
                },
            }
        )
        
        st.markdown("---")
        
        # Waterfall Layout
        # If "推荐" (Recommend) is selected, we show all posts (or recommendation logic), 
        # for others we filter.
        # Since we default new posts to '推荐' but conceptually that means 'All' or 'General', 
        # let's pass it to get_posts.
        posts = PostService.get_posts(
            search_query=search_query if search_query else None,
            category=selected_category
        )
        
        if not posts:
             st.info(f"暂无【{selected_category}】分类的笔记，快去发布第一篇吧！")
        else:
            # Increased columns to 5 for better scaling on wide screens (like official web UI)
            cols = st.columns(5) 
            for idx, post in enumerate(posts):
                with cols[idx % 5]:
                    render_card(post, click_handler=view_post_details)

    elif selected == "发布笔记":
        st.title("发布笔记 ✍️")
        if not st.session_state['is_logged_in']:
            st.warning("请先登录")
        else:
            with st.form("create_post_form"):
                title = st.text_input("标题")
                content = st.text_area("正文")
                
                # Category Selection
                categories = ["推荐", "穿搭", "美食", "彩妆", "影视", "职场", "情感", "家居", "游戏", "旅行", "健身"]
                category = st.selectbox("选择分类", categories)
                
                uploaded_file = st.file_uploader("上传图片", type=['jpg', 'png', 'jpeg'])
                
                submitted = st.form_submit_button("发布")
                if submitted:
                    if not title or not uploaded_file:
                        st.error("标题和图片是必填项！")
                    else:
                        success, msg = PostService.create_post(
                            st.session_state['user_info']['id'],
                            title,
                            content,
                            uploaded_file,
                            category
                        )
                        if success:
                            st.success("发布成功！")
                        else:
                            st.error(msg)

    elif selected == "个人中心":
        st.title("个人中心 👤")
        user = st.session_state['user_info']
        
        # Display current avatar
        col_left, col_right = st.columns([1, 3])
        with col_left:
            if user.get('avatar_url') and os.path.exists(user['avatar_url']):
                st.image(user['avatar_url'], width=150)
            else:
                st.image("https://via.placeholder.com/150", width=150)
            
            # Display Follow Counts
            counts = UserService.get_follow_counts(user['id'])
            st.markdown(f"**关注:** {counts['following']}  |  **粉丝:** {counts['followers']}")
        
        with col_right:
            with st.expander("编辑资料", expanded=False):
                with st.form("profile_form"):
                    new_nickname = st.text_input("昵称", value=user['nickname'])
                    uploaded_avatar = st.file_uploader("更换头像", type=['jpg', 'png', 'jpeg'])
                    
                    if st.form_submit_button("保存修改"):
                        success, msg = AuthService.update_user_profile(user['id'], new_nickname, uploaded_avatar)
                        if success:
                            st.success("修改成功，正在刷新...")
                            # Update session state immediately for better UX
                            updated_user = AuthService.get_user_by_id(user['id'])
                            st.session_state['user_info'] = updated_user
                            st.rerun()
                        else:
                            st.error(msg)
        
        st.markdown("---")
        
        tab_posts, tab_following, tab_followers = st.tabs(["我的发布", "我的关注", "我的粉丝"])
        
        with tab_posts:
            my_posts = PostService.get_user_posts(user['id'])
            if my_posts:
                cols = st.columns(5) # Consistent 5 columns
                for idx, post in enumerate(my_posts):
                    with cols[idx % 5]:
                        post['nickname'] = user['nickname'] 
                        render_card(post, click_handler=view_post_details)
            else:
                st.info("还没有发布过笔记")
        
        with tab_following:
            following = UserService.get_following(user['id'])
            if following:
                for f_user in following:
                    c1, c2, c3 = st.columns([1, 4, 2])
                    with c1:
                        if f_user.get('avatar_url') and os.path.exists(f_user['avatar_url']):
                             st.image(f_user['avatar_url'], width=50)
                        else:
                             st.markdown("👤")
                    with c2:
                        st.write(f"**{f_user['nickname']}**")
                    with c3:
                        if st.button("取消关注", key=f"unfollow_list_{f_user['id']}"):
                             UserService.unfollow_user(user['id'], f_user['id'])
                             st.rerun()
                    st.divider()
            else:
                st.info("还没有关注任何人")

        with tab_followers:
            followers = UserService.get_followers(user['id'])
            if followers:
                for f_user in followers:
                    c1, c2, c3 = st.columns([1, 4, 2])
                    with c1:
                        if f_user.get('avatar_url') and os.path.exists(f_user['avatar_url']):
                             st.image(f_user['avatar_url'], width=50)
                        else:
                             st.markdown("👤")
                    with c2:
                         st.write(f"**{f_user['nickname']}**")
                    with c3:
                         # Check if I follow them back?
                         if UserService.is_following(user['id'], f_user['id']):
                             st.button("互相关注", disabled=True, key=f"mutual_{f_user['id']}")
                         else:
                             if st.button("回粉", key=f"follow_back_{f_user['id']}", type="primary"):
                                 UserService.follow_user(user['id'], f_user['id'])
                                 st.rerun()
                    st.divider()
            else:
                st.info("还没有粉丝")

    elif selected == "登录/注册":
        # Reset the show login flag so we don't get stuck here if user clicks menu elsewhere later
        # Actually, we should only reset if user successfully logs in or we navigate away.
        # But option_menu handles 'selected' state naturally if user clicks.
        # The override only happens if show_login_view is True.
        # We can reset it when entering this block to let menu selection take over?
        # If we reset it here, hitting rerun (e.g. on tab switch) might switch back if we are not careful?
        # No, if 'selected' is "登录/注册", we are fine. 
        # But if 'selected' was "发现" and we forced it via flag...
        # It's safer to reset the flag if the actual menu selection matches, OR just keep it simple.
        
        if st.session_state.get('show_login_view'):
             # If we forced view, we are here. User can click menu to leave.
             # But if user clicks "登录/注册" menu item, selected is correct.
             pass

        # We also need to allow user to exit this view by clicking menu.
        # If user clicks menu, 'selected' changes. We should respect 'selected'.
        # So the logic above `if st.session_state.get('show_login_view', False): selected = "登录/注册"`
        # is too strong if it persists.
        # Better: use a callback on the button to set index? No, option_menu doesn't support external set easily without key change.
        # Solution: Just treat the button click as a one-time navigation event.
        # But Streamlit reruns from top.
        # Let's try: If button clicked -> set flag. If flag is True -> render Login.
        # BUT we need to clear the flag if user clicks something else?
        # Actually, simpler: If user is NOT logged in, 'selected' defaults to '发现'.
        # If button clicked, we want to render the Login content.
        
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            st.header("登录")
            with st.form("login_form"):
                username = st.text_input("用户名")
                password = st.text_input("密码", type="password")
                submit = st.form_submit_button("登录")
                
                if submit:
                    user, msg = AuthService.login_user(username, password)
                    if user:
                        st.session_state['is_logged_in'] = True
                        st.session_state['user_info'] = user
                        st.session_state['show_login_view'] = False # Clear flag
                        cookie_manager.set("user_id", user['id'], expires_at=None)
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error(msg)
        
        with tab2:
            st.header("注册")
            with st.form("register_form"):
                new_user = st.text_input("用户名")
                new_pass = st.text_input("密码", type="password")
                new_nick = st.text_input("昵称 (可选)")
                reg_submit = st.form_submit_button("注册")
                
                if reg_submit:
                    if not new_user or not new_pass:
                        st.error("用户名和密码必填")
                    else:
                        success, msg = AuthService.register_user(new_user, new_pass, new_nick)
                        if success:
                            st.success("注册成功，请去登录")
                        else:
                            st.error(msg)

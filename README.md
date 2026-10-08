# 📕 小红书 (Mini-RedNote)

一个功能完整的社交分享平台，灵感来源于小红书，支持用户发布图文笔记、互动交流、关注粉丝等核心社交功能。

## ✨ 项目简介

本项目是一个前后端分离的现代化社交分享平台，采用 Vue 3 + FastAPI 技术栈构建。用户可以发布图文笔记、浏览内容、点赞收藏、评论互动、关注用户、私信聊天等，提供了完整的社交网络体验。

## 🎯 核心功能

### 👤 用户系统
- **用户注册/登录**：支持用户名密码注册登录，密码使用 bcrypt 加密存储
- **个人资料管理**：支持修改昵称、上传头像
- **用户主页**：查看用户发布的笔记、点赞的笔记、收藏的笔记
- **关注系统**：关注/取消关注用户，查看关注列表和粉丝列表

### 📝 内容发布
- **发布笔记**：支持标题、正文、图片上传
- **视频发布**：支持视频笔记发布，可上传视频文件（MP4、MOV、WebM格式）和视频封面
- **分类管理**：笔记支持多种分类（推荐、穿搭、美食、彩妆、影视、职场、情感、家居、游戏、旅行、健身等）
- **隐私设置**：支持公开/私密笔记设置
- **内容管理**：用户可以删除自己发布的笔记

### 🏠 内容浏览
- **瀑布流布局**：美观的卡片式瀑布流展示
- **分类筛选**：按分类浏览不同内容
- **搜索功能**：支持标题和内容搜索
- **详情页**：查看笔记完整内容、作者信息、互动数据

### 💬 互动功能
- **点赞系统**：对笔记和评论进行点赞/取消点赞
- **收藏功能**：收藏喜欢的笔记，方便后续查看
- **评论系统**：对笔记发表评论，支持评论点赞
- **实时统计**：实时显示点赞数、评论数等数据

### 💌 社交功能
- **私信系统**：用户之间可以发送私信
- **会话列表**：查看所有对话列表
- **消息已读**：支持消息已读状态标记
- **未读提醒**：显示未读消息数量

### 🔔 通知系统
- **互动通知**：点赞、评论等互动通知
- **关注通知**：新粉丝关注通知
- **通知管理**：查看和管理所有通知

## 🛠️ 技术栈

### 后端技术
- **框架**：FastAPI - 现代化的 Python Web 框架，高性能异步支持
- **数据库**：MySQL - 关系型数据库，存储用户、笔记、互动等数据
- **ORM**：PyMySQL - Python MySQL 数据库连接库
- **认证**：bcrypt - 密码加密存储
- **文件处理**：Pillow - 图片处理
- **环境管理**：python-dotenv - 环境变量管理
- **服务器**：Uvicorn - ASGI 服务器

### 前端技术
- **框架**：Vue 3 - 渐进式 JavaScript 框架
- **构建工具**：Vite - 下一代前端构建工具
- **路由**：Vue Router 4 - 官方路由管理器
- **状态管理**：Pinia - Vue 官方状态管理库
- **UI 组件库**：Element Plus - 基于 Vue 3 的组件库
- **CSS 框架**：Tailwind CSS - 实用优先的 CSS 框架
- **HTTP 客户端**：Axios - 基于 Promise 的 HTTP 库
- **工具库**：
  - moment.js - 日期时间处理
  - html2canvas - 图片生成

### 开发工具
- **Python 版本**：Python 3.12+
- **Node.js 版本**：Node.js 16+
- **数据库**：MySQL 5.7+ / MySQL 8.0+

## 📁 项目结构

```
xiaohongshu/
├── backend/                 # 后端服务模块
│   ├── __init__.py
│   ├── auth_service.py      # 用户认证服务
│   ├── database.py          # 数据库连接管理
│   ├── message_service.py   # 消息服务
│   ├── post_service.py      # 笔记服务
│   ├── user_service.py      # 用户服务
│   └── utils.py             # 工具函数
├── frontend/                # 前端项目
│   ├── public/              # 静态资源
│   ├── src/
│   │   ├── api/             # API 接口封装
│   │   │   └── index.js
│   │   ├── assets/          # 资源文件
│   │   ├── components/      # Vue 组件
│   │   │   ├── NavBar.vue
│   │   │   └── WaterfallCard.vue
│   │   ├── router/          # 路由配置
│   │   │   └── index.js
│   │   ├── stores/          # Pinia 状态管理
│   │   │   ├── transition.js
│   │   │   └── user.js
│   │   ├── views/           # 页面视图
│   │   │   ├── ChatView.vue
│   │   │   ├── HomeView.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── MessageIndexView.vue
│   │   │   ├── PostDetailView.vue
│   │   │   ├── ProfileView.vue
│   │   │   └── PublishView.vue
│   │   ├── App.vue          # 根组件
│   │   └── main.js          # 入口文件
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js       # Vite 配置
│   └── tailwind.config.js   # Tailwind 配置
├── assets/                  # 上传的图片资源
├── venv/                    # Python 虚拟环境
├── server.py                # FastAPI 服务器主文件
├── init_db.py               # 数据库初始化脚本
├── schema.sql               # 数据库表结构
├── requirements.txt         # Python 依赖
├── package.json             # 根目录 package.json
├── 一键运行后端.bat         # Windows 快速启动脚本
└── README.md                # 项目说明文档
```

## 🗄️ 数据库设计

### 核心数据表

1. **users** - 用户表
   - 存储用户基本信息（用户名、密码哈希、昵称、头像等）

2. **posts** - 笔记表
   - 存储笔记内容（标题、正文、图片、分类、点赞数、隐私设置等）

3. **comments** - 评论表
   - 存储评论内容（笔记ID、用户ID、内容、点赞数等）

4. **likes** - 点赞表
   - 记录用户对笔记的点赞关系（防止重复点赞）

5. **collections** - 收藏表
   - 记录用户收藏的笔记

6. **follows** - 关注表
   - 记录用户之间的关注关系

7. **messages** - 私信表
   - 存储用户之间的私信内容

8. **notifications** - 通知表
   - 存储系统通知（点赞、评论、关注等）

9. **comment_likes** - 评论点赞表
   - 记录用户对评论的点赞关系

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 16+
- MySQL 5.7+ / MySQL 8.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd mini-rednote
```

### 2. 数据库配置

#### 创建数据库

```sql
CREATE DATABASE mini_redbook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mini_redbook
DB_PORT=3306
```

#### 初始化数据库

```bash
python init_db.py
```

或者直接执行 SQL 文件：

```bash
mysql -u root -p mini_redbook < schema.sql
```

### 3. 后端配置

#### 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 启动后端服务

**方式一：使用批处理文件（Windows）**

```bash
一键运行后端.bat
```

**方式二：手动启动**

```bash
# 激活虚拟环境后
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 `http://localhost:8000` 启动

### 4. 前端配置

#### 安装依赖

```bash
cd frontend
npm install
```

#### 启动开发服务器

```bash
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 5. 访问应用

打开浏览器访问：`http://localhost:5173`

## 📡 API 接口文档

### 认证相关

- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `PUT /api/user/profile` - 更新用户资料

### 笔记相关

- `GET /api/posts` - 获取笔记列表（支持分页、搜索、分类筛选）
- `GET /api/posts/{post_id}` - 获取笔记详情
- `POST /api/posts` - 创建笔记
- `DELETE /api/posts/{post_id}` - 删除笔记
- `PUT /api/posts/{post_id}/visibility` - 更新笔记可见性
- `GET /api/posts/user/{user_id}` - 获取用户发布的笔记
- `GET /api/posts/user/{user_id}/liked` - 获取用户点赞的笔记
- `GET /api/posts/user/{user_id}/collected` - 获取用户收藏的笔记

### 互动相关

- `POST /api/posts/{post_id}/like` - 点赞/取消点赞笔记
- `POST /api/posts/{post_id}/collect` - 收藏/取消收藏笔记
- `GET /api/posts/{post_id}/comments` - 获取评论列表
- `POST /api/posts/{post_id}/comments` - 添加评论
- `POST /api/comments/{comment_id}/like` - 点赞/取消点赞评论

### 用户相关

- `GET /api/users/{user_id}` - 获取用户公开信息
- `POST /api/users/{user_id}/follow` - 关注用户
- `POST /api/users/{user_id}/unfollow` - 取消关注
- `GET /api/users/{user_id}/is_following` - 检查是否关注
- `GET /api/users/{user_id}/followers` - 获取粉丝列表
- `GET /api/users/{user_id}/following` - 获取关注列表
- `GET /api/users/{user_id}/counts` - 获取关注/粉丝数量

### 消息相关

- `POST /api/messages` - 发送私信
- `GET /api/messages/conversations` - 获取会话列表
- `GET /api/messages/conversation/{other_user_id}` - 获取对话消息
- `PUT /api/messages/read` - 标记消息已读
- `GET /api/messages/unread/count` - 获取未读消息数

### 通知相关

- `GET /api/notifications` - 获取通知列表
- `PUT /api/notifications/read` - 标记通知已读

### 静态资源

- `GET /assets/{filename}` - 获取上传的图片

## 🎨 功能特性详解

### 1. 瀑布流布局

前端采用响应式瀑布流布局，自动适配不同屏幕尺寸，提供流畅的浏览体验。

### 2. 文件上传与存储

#### 图片上传
- 支持 JPG、PNG、JPEG 格式
- 图片自动保存到 `assets/` 目录
- 使用 UUID 生成唯一文件名，避免冲突

#### 视频上传
- 支持 MP4、MOV、WebM 格式
- 视频文件大小限制：前端限制 500MB，后端支持最大 10GB
- 视频笔记必须同时上传视频文件和封面图片
- 视频文件自动保存到 `assets/` 目录
- 使用 UUID 生成唯一文件名，避免冲突

### 3. 密码安全

- 使用 bcrypt 进行密码哈希加密

### 4. 数据验证

- 后端使用 Pydantic 进行数据模型验证
- 前端使用 Element Plus 表单验证

### 5. CORS 配置

后端已配置 CORS 中间件，支持跨域请求，方便前后端分离开发。

### 6. 错误处理

- 统一的错误响应格式
- 详细的错误信息返回
- 前端友好的错误提示

### 7. 移动端网页 UI 适配

本项目针对移动端设备进行了全面的 UI 适配优化，确保在手机、平板等移动设备上提供良好的用户体验。

#### Viewport 配置
- 在 `index.html` 中配置了标准的 viewport meta 标签，确保页面在移动设备上正确缩放
- 设置 `width=device-width, initial-scale=1.0` 实现自适应布局

#### 响应式布局设计
- **瀑布流列数自适应**：根据屏幕宽度自动调整瀑布流列数
  - 移动端（< 768px）：2 列布局
  - 平板端（768px - 1024px）：3 列布局
  - 桌面端（1024px - 1280px）：4 列布局
  - 大屏桌面（≥ 1280px）：5 列布局
- **导航栏响应式**：桌面端显示完整导航栏，移动端显示简化版导航栏
- **搜索框适配**：移动端和桌面端采用不同的搜索框布局和交互方式

#### 移动端专属组件
- **底部导航栏（MobileTabBar）**：仅在移动端显示（`md:hidden`），提供首页、分区、发布、消息、我的等核心功能入口
- **安全区域适配**：使用 `env(safe-area-inset-bottom)` CSS 变量适配 iPhone 等设备的底部安全区域，避免内容被系统 UI 遮挡

#### 响应式样式实现
- 使用 **Tailwind CSS** 的响应式工具类（如 `md:`, `lg:`, `xl:` 等前缀）实现断点式响应式设计
- 移动端优先的设计理念，通过媒体查询逐步增强桌面端体验
- 统一的间距、字体大小等设计规范，确保跨设备的一致性

#### 触摸交互优化
- 按钮和可点击元素具有合适的触摸目标尺寸（最小 44x44px）
- 优化了移动端的滚动体验和手势交互
- 适配移动端浏览器的默认行为（如阻止双击缩放等）

## 🔧 开发说明

### 后端开发

1. **服务层架构**：采用服务层模式，将业务逻辑封装在 `backend/` 目录下的各个服务文件中
2. **数据库连接**：使用单例模式管理数据库连接，确保连接复用
3. **文件上传**：使用 FastAPI 的 `UploadFile` 处理文件上传
4. **API 设计**：遵循 RESTful 设计规范

### 前端开发

1. **组件化开发**：使用 Vue 3 Composition API 进行组件开发
2. **状态管理**：使用 Pinia 管理全局状态（用户信息、过渡动画等）
3. **路由守卫**：使用 Vue Router 的导航守卫实现权限控制
4. **响应式设计**：使用 Tailwind CSS 实现响应式布局

### 代码规范

- Python：遵循 PEP 8 代码规范
- JavaScript：使用 ESLint 进行代码检查（可配置）
- 注释：关键函数和类需要添加文档字符串

## 📝 待办事项 / 未来计划

- [ ] 添加图片压缩功能，优化存储空间
- [ ] 实现图片懒加载，提升页面性能
- [ ] 实现推荐算法，个性化内容推荐
- [ ] 添加标签系统，支持多标签分类
- [ ] 添加消息推送功能（WebSocket）
- [ ] 实现内容审核功能
- [ ] 添加数据统计和分析功能
- [ ] 支持多语言国际化

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者

- 项目创建者：chyinan

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 组件库
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的 CSS 框架

---

**注意**：本项目仅用于学习和研究目的，请勿用于商业用途。



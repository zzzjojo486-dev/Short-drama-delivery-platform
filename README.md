# 🎬 短剧交付平台 (Short Drama Delivery Platform)

用于社区交流，以及短剧订单的发布与交付。当前项目已完成基于 **Django REST Framework (DRF)** 的后端重构与登录功能，采用前后端分离架构。

## 📋 项目简介

本项目是一个前后端分离的短剧交付平台，后端基于 **Django REST Framework (DRF)** 构建，前端基于 **Vue 3 + Vite** 构建，数据存储使用 **MySQL**。

目前已完成 **用户认证模块** 的 DRF 化改造，包括：

- 用户注册（含头像上传）
- 用户登录（签发 JWT 令牌）
- 个人资料查看与更新
- 用户公开资料查询
- 静态资源（头像图片等）访问

> 说明：本 README 仅描述已转换到 DRF 的内容。发布、订单、互动等模块仍在持续开发中。

## 🛠️ 技术栈

### 后端（Django REST Framework）

| 组件 | 技术 | 用途 |
|------|------|------|
| 框架 | Django 4.2 + DRF 3.17 | Web / REST API |
| 数据库 | MySQL 5.7+ / 8.0+ | 数据存储 |
| 驱动 | PyMySQL | MySQL 连接 |
| 认证 | JWT (python-jose) | Bearer Token 鉴权 |
| 密码 | bcrypt | 密码安全加密 |
| 图片 | Pillow | 图片处理 |
| 配置 | django-environ | 读取 `.env` 环境变量 |
| CORS | django-cors-headers | 跨域请求支持 |

### 前端（Vue 3）

| 组件 | 技术 |
|------|------|
| 框架 | Vue 3 |
| 构建 | Vite |
| 路由 | Vue Router 4 |
| 状态管理 | Pinia |
| UI 组件 | Element Plus |
| HTTP 客户端 | Axios |

### 运行环境

- Python 3.10+
- Node.js 16+
- MySQL 5.7+ / 8.0+

## 📁 项目结构

```
Short-drama-delivery-platform/
├── django_backend/              # DRF 后端
│   ├── manage.py
│   ├── requirements.txt         # 后端依赖
│   ├── config/                  # Django 项目配置
│   │   ├── settings.py          # 全局配置（数据库/DRF/CORS）
│   │   ├── urls.py              # 总路由（/api/、/assets/）
│   │   ├── wsgi.py              # 生产 WSGI 入口
│   │   └── asgi.py
│   └── apps/
│       └── users/               # 用户与认证模块
│           ├── models.py        # User 模型（映射 users 表）
│           ├── serializers.py   # 序列化器
│           ├── views.py         # 视图（登录/注册/资料）
│           ├── auth.py          # JWT 认证类
│           ├── urls.py          # 模块路由
│           └── migrations/      # 数据库迁移
├── frontend/                    # 前端项目（Vue 3 + Vite）
│   └── src/
│       ├── api/index.js         # API 接口封装
│       ├── router/              # 路由配置
│       ├── stores/              # Pinia 状态管理
│       ├── components/          # 公共组件
│       └── views/               # 页面视图
├── schema.sql                   # 数据库建表脚本
├── .env                         # 环境变量配置
├── 一键运行Django后端.bat       # 后端一键启动脚本
└── frontend/package.json        # 前端依赖
```

## 🚀 快速开始

### 1. 环境准备

- 安装 Python 3.10+ 与 Node.js 16+
- 准备 MySQL 数据库，并创建 `schema.sql` 中定义的数据表（或使用迁移自动建表）

### 2. 配置环境变量

在项目根目录的 `.env` 文件中配置数据库连接：

```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=123456
DB_NAME=short_drama
DB_PORT=3306
```

`django_backend/config/settings.py` 会自动读取该文件中的配置。

### 3. 初始化数据库

方式一（推荐）：使用 Django 迁移自动建表。

```bash
cd django_backend
..\venv\Scripts\python.exe manage.py migrate
```

方式二：执行 `schema.sql` 手动建表。

```bash
mysql -u root -p < schema.sql
```

### 4. 启动后端（DRF）

方式一（Windows 一键脚本）：双击「一键运行Django后端.bat」

方式二（命令行）：

```bash
cd django_backend
venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

后端运行后监听 `http://localhost:8000`，API 前缀为 `/api/`。

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行后，浏览器访问 `http://localhost:5173`。

## 🔧 已实现 API 接口

API 统一前缀 `/api/`，返回格式与数据表对齐 `schema.sql`。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/login` | 用户登录，返回用户对象与 JWT Token |
| POST | `/api/register` | 用户注册（multipart，头像必填） |
| PUT | `/api/user/profile` | 更新个人资料（昵称、头像） |
| GET | `/api/users/{user_id}` | 查询用户公开资料 |
| GET | `/assets/{filename}` | 访问静态资源（头像等） |

### 登录示例

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "123456"}'
```

响应示例：

```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "demo",
    "nickname": "demo",
    "avatar_url": "assets/avatar_demo.jpg"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 鉴权方式

接口默认不对请求强制鉴权（与原有行为保持一致）。当请求携带有效的 JWT 令牌时，后端会解析并注入当前用户：

```
Authorization: Bearer <token>
```

令牌有效期 7 天，算法为 HS256。

## 🔐 安全特性

- **密码加密**：使用 bcrypt 12 轮对密码进行哈希，兼容旧库中的 bcrypt 哈希
- **令牌认证**：JWT Bearer Token，HS256 签名，7 天有效期
- **输入校验**：注册、资料更新等均进行字段长度与合法性校验
- **路径安全**：静态资源使用 `os.path.basename()` 防止路径穿越

## 🗄️ 数据库设计

数据库表结构定义见 `schema.sql`，核心表包括：

- `users`：用户表（用户名、密码哈希、昵称、头像）
- `posts`：内容/订单帖子表
- `comments`：评论表
- `likes`：点赞表
- `collections`：收藏表
- `messages`：私信表

## 🌐 部署方式

### 开发模式部署

见上文「快速开始」，开发环境前后端分离：

- 后端：`python manage.py runserver 0.0.0.0:8000`
- 前端：`npm run dev`（Vite 开发服务器，端口 5173，已配置 CORS）

### 生产模式部署

生产环境建议使用 Gunicorn + Nginx 部署后端，Vite 构建前端静态文件后由 Nginx 托管。

#### 后端部署（Gunicorn）

```bash
# 安装 Gunicorn
pip install gunicorn

# 收集静态文件
cd django_backend
python manage.py collectstatic --noinput

# 启动 Gunicorn（4 个 worker，绑定 8000 端口）
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

> 注意：生产环境需修改 `django_backend/config/settings.py`：
> - 将 `DEBUG` 设为 `False`
> - 设置 `DJANGO_SECRET_KEY` 为随机安全值
> - 按需收紧 `ALLOWED_HOSTS`

#### 前端构建

```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/`，由 Nginx 托管。

#### Nginx 配置示例

```nginx
# 前端静态资源
server {
    listen 80;
    server_name example.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri /index.html;
    }

    # 反向代理到 Django 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态资源（头像等）
    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 整体部署流程

1. 配置 `.env` 环境变量（数据库、密钥）
2. 执行 `manage.py migrate` 初始化数据库
3. 构建前端：`frontend` 下执行 `npm run build`，产物放入 Nginx 静态目录
4. 启动后端：Gunicorn 托管 `config.wsgi:application`
5. 配置 Nginx 反向代理 `/api/` 与 `/assets/` 到后端

## 🧪 测试

后端测试使用 SQLite 内存库，不依赖 MySQL 即可运行：

```bash
cd django_backend
..\venv\Scripts\python.exe manage.py test
```

## 📝 更新日志

- **v0.1.0**：基于 Django REST Framework 重构后端，实现登录功能（前端 + 后端 + 数据库）。

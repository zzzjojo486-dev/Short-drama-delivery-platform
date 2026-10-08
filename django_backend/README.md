# Mini-RedNote Django 后端(django_backend)

小红书复刻项目后端的 Django + DRF 重构版本。目标:与原 FastAPI 后端**接口完全兼容**,前端 Vue3 代码零修改。

当前进度:**第一阶段 — 项目骨架 + 用户认证模块**。

## 目录结构

```
django_backend/
├── manage.py               # Django 项目管理脚本
├── config/                 # 项目配置(settings/urls/wsgi/asgi)
├── apps/
│   └── users/              # 用户与认证模块
│       ├── models.py       # User 模型(映射原 users 表)
│       ├── serializers.py  # 请求校验 + 响应格式化
│       ├── views.py        # 登录/注册/资料/公开资料/assets 视图
│       ├── urls.py         # 模块路由
│       ├── auth.py         # JWT 签发/校验 + BearerTokenAuthentication
│       ├── utils.py        # 图片校验与保存(移植自原 backend/utils.py)
│       ├── tests.py        # 单元测试
│       └── migrations/     # 数据库迁移文件
├── media/                  # 上传目录(后续笔记模块使用)
└── requirements.txt
```

## 环境搭建

1. Python 3.12(项目 venv 已存在,位于仓库根 `venv/`)
2. MySQL 8.x(数据库 `mini_redbook`,配置在仓库根 `.env`)

安装依赖(venv 内):

```bash
venv\Scripts\activate
pip install -r requirements.txt
```

## 数据库初始化

配置从**仓库根目录的 `.env`** 读取(`DB_HOST`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`/`DB_PORT`),变量名与原 FastAPI 后端一致。

**场景一:复用旧数据库(users 表已存在,保留原数据)**

```bash
python manage.py migrate --fake-initial
```

`--fake-initial` 会把 users 表的初始迁移标记为已应用,不动表结构和旧数据;Django 自身的 django_migrations 等新表正常创建。旧数据中的 bcrypt 密码哈希(裸 `$2b$12$` 格式)可直接登录。

**场景二:全新数据库**

```bash
python manage.py migrate
```

一键创建 users 表(结构与原 schema.sql 对齐)及 Django 基础表。

## 启动

```bash
python manage.py runserver 0.0.0.0:8000
```

或直接双击仓库根的 `一键运行Django后端.bat`。

服务地址:`http://localhost:8000`(与原 uvicorn 端口一致,前端无需改配置;新旧后端不能同时占用 8000 端口)。

## 已实现接口(与原 FastAPI 完全对齐)

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/login` | POST | 登录,JSON body `{username, password}`,成功返回 `{success, user, token}` |
| `/api/register` | POST | 注册,multipart form(username/password/nickname?/avatar 必填) |
| `/api/user/profile` | PUT | 更新资料,multipart form(user_id/nickname/avatar?) |
| `/api/users/{user_id}` | GET | 用户公开资料 |
| `/assets/{filename}` | GET | 静态图片(仓库根 assets/ 目录,与旧版共用) |

响应格式与原版一致:业务错误为 HTTP 200 + `{"success": false, "message": "..."}`,资源不存在为 404 + `{"detail": "..."}`。

## 认证

登录响应中携带 JWT token(HS256,7 天)。请求头 `Authorization: Bearer <token>` 会被解析并注入 request.user,但接口不强制鉴权(与原版一致,前端通过 body 里的 user_id 传递身份)。

## 测试

```bash
python manage.py test
```

测试使用 sqlite 内存库,不依赖 MySQL。重点覆盖:旧格式 bcrypt 哈希登录兼容、注册校验消息、登录注册全流程、资料修改、assets 静态文件访问、JWT 认证。

## 前端联调

```bash
cd frontend && npm run dev   # Vite,默认 5173 端口
```

前端 baseURL 为 `http://localhost:8000/api`,CORS 已放行 `localhost:5173`,无需任何修改。

## 待实现(后续阶段)

- 笔记模块(posts/post_images:列表/详情/发布/删除/可见性)
- 互动模块(likes/collections/comments/comment_likes)
- 关注模块(follows)
- 私信与通知模块(messages/notifications)
- AI 文案润色接口

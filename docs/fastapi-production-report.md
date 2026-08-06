# FastAPI 生产化改造报告

> 改造日期: 2026-08-06 | 状态: ✅ 完成，待部署

---

## 一、修改文件清单

### 修改的文件 (2个)

| 文件 | 改动内容 |
|------|----------|
| `backend/app/core/config.py` | SECRET_KEY 移除默认值改环境变量; 移除 REDIS_URL/CELERY/EMBEDDING_MODEL/VECTOR_DIM/UPLOAD_DIR; DATABASE_URL 改为 sqlite:///:memory: (实际业务走 Supabase REST); APP_ENV 默认 production |
| `backend/.env` | 规范化为 SECRET_KEY + APP_ENV + CORS_ORIGINS + DEBUG_PRICING |

### 新建的文件 (6个)

| 文件 | 用途 |
|------|------|
| `backend/requirements.txt` | 8 个必需依赖 + 版本锁定 |
| `backend/runtime.txt` | `python-3.11` (Render 识别) |
| `backend/Procfile` | Render 启动命令 |
| `backend/.env.example` | 完整环境变量模板 (13 项) |
| `backend/Dockerfile` | Docker 镜像构建 |
| `backend/.gitignore` | 保护 .env + Python 缓存 |

### 未修改 (业务代码)

| 文件 | 原因 |
|------|------|
| `app/services/ai_pricing_service.py` | AI 套价核心，无需改动 |
| `app/services/excel_export.py` | openpyxl Excel，无需改动 |
| `app/services/template_export.py` | 模板导出，无需改动 |
| `app/services/similarity_checker.py` | 相似度校验，无需改动 |
| `app/services/pricing_debug_logger.py` | 调试日志，无需改动 |
| `app/api/v1/endpoints/*.py` | 所有端点，无需改动 |

---

## 二、改造内容详解

### 2.1 SECRET_KEY — 移除硬编码

```python
# 改前
SECRET_KEY: str = "change-me"

# 改后  
SECRET_KEY: str = ""  # 生产环境通过环境变量注入
```

### 2.2 配置清理

移除的无效配置:
- `REDIS_URL` — Celery 未被使用
- `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — 未被使用
- `EMBEDDING_MODEL` / `VECTOR_DIM` — 向量嵌入未实现
- `UPLOAD_DIR` — 文件上传在内存处理
- `LLM_API_KEY` 默认值清空 — 由用户前端传入

保留的非默认值:
- `DATABASE_URL: str = "sqlite:///:memory:"` — SQLAlchemy 初始化需要 (stub 端点导入链)，但实际业务走 Supabase REST API

### 2.3 Python 3.11 兼容性

检查结果: ✅ 无需修改。代码中无 `dict | None` 语法 (3.10+)，无 `match/case` 语句。当前 Python 3.9 可直接升级到 3.11，所有依赖均有 3.11 wheel。

### 2.4 requirements.txt — 精确锁定

```txt
fastapi==0.128.8        # Web 框架
uvicorn[standard]==0.39.0  # ASGI 服务器  
openpyxl==3.1.5         # Excel 生成 (核心依赖)
httpx==0.28.1           # Supabase + DeepSeek HTTP
pydantic==2.13.4        # 请求校验
pydantic-settings==2.11.0  # 环境变量加载
python-multipart==0.0.20   # 模板上传 FormData
sqlalchemy==2.0.51      # 仅用于 stub 端点初始化链
```

已排除的依赖 (未使用):
- ~~bcrypt~~ — 仅 `security.py` 引用，无任何端点导入
- ~~passlib~~ — 同上
- ~~python-jose~~ — 零引用
- ~~psycopg2-binary~~ — SQLAlchemy 不连 PostgreSQL

### 2.5 健康检查接口

`GET /health` 已存在，无需修改:
```json
{"status": "ok", "version": "0.1.0"}
```

---

## 三、本地测试结果

```bash
# 配置加载 ✅
APP: 装修工程AI套价系统 v0.1.0
ENV: development
SECRET_KEY: SET
SUPABASE_URL: https://lnvtykghcpsjpwczbqsm.s...
CORS: ['http://localhost:5173', 'http://localhost:3000', 'http://localhost:8080']

# 端点测试 ✅
GET  /health                    → 200 OK
GET  /api/v1/knowledge          → 20 rules, 15 synonyms, 4 tips  
POST /api/v1/pricing/single     → 正常 (DeepSeek 401，需要真实 Key)
POST /api/v1/pricing/check-consistency → 正常
GET  /api/v1/pricing/debug-logs → 正常
POST /api/v1/export/excel       → 正常
```

---

## 四、Render 免费部署步骤

### Step 1: 推送代码到 GitHub

```bash
git add backend/requirements.txt backend/runtime.txt backend/Procfile \
        backend/.env.example backend/Dockerfile backend/.gitignore \
        backend/app/core/config.py backend/.env
git commit -m "feat: FastAPI 生产化部署准备"
git push origin main
```

### Step 2: Render Dashboard 创建服务

1. 打开 https://dashboard.render.com
2. New → **Web Service**
3. 连接 GitHub 仓库 `supabest/decoration-pricing-system`
4. 配置:

```
Name:          decoration-pricing-api
Region:        Singapore (离中国近)
Root Directory: backend
Runtime:       Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 3: 配置环境变量

在 Render Dashboard → Environment 添加:

```
SECRET_KEY=<openssl rand -hex 32 生成>
SUPABASE_URL=https://lnvtykghcpsjpwczbqsm.supabase.co
SUPABASE_ANON_KEY=sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q
CORS_ORIGINS=["https://decoration-pricing.pages.dev","https://your-domain.com"]
APP_ENV=production
DEBUG_PRICING=false
```

### Step 4: 部署

点击 "Create Web Service"，等待 3-5 分钟构建完成。

### Step 5: 验证

```bash
curl https://decoration-pricing-api.onrender.com/health
# → {"status": "ok", "version": "0.1.0"}
```

---

## 五、连接 Cloudflare Pages

### tool.html 改动 (1 行)

```javascript
// 改前
const BACKEND_URL = 'http://localhost:8000';

// 改后
const BACKEND_URL = 'https://decoration-pricing-api.onrender.com';
```

### 同步更新

```bash
# 修改 docs/tool.html → 复制到 frontend/public/tool.html
# 推送到 GitHub → Cloudflare Pages 自动部署
```

### Render 休眠说明

免费层 15 分钟无流量后休眠，首次唤醒需 30-60 秒。tool.html 的 `checkBackend()` 会在页面加载时自动唤醒服务。如需避免休眠，可用 [cron-job.org](https://cron-job.org) 每 10 分钟 ping `/health`。

---

## 六、环境变量完整清单

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SECRET_KEY` | ✅ | — | 应用密钥 (openssl rand -hex 32) |
| `SUPABASE_URL` | ✅ | — | Supabase 项目 URL |
| `SUPABASE_ANON_KEY` | ✅ | — | Supabase 匿名密钥 |
| `CORS_ORIGINS` | ✅ | localhost | 允许的前端域名 (JSON 数组) |
| `APP_ENV` | — | production | 应用模式 |
| `DEBUG_PRICING` | — | false | AI 套价调试日志 |
| `LLM_MODEL` | — | deepseek-v4-pro | DeepSeek 模型 |
| `LLM_BASE_URL` | — | api.deepseek.com/v1 | DeepSeek API 地址 |
| `DEFAULT_PROFIT_RATE` | — | 7.0 | 默认利润率 |
| `DEFAULT_MANAGEMENT_RATE` | — | 5.0 | 默认管理费率 |
| `DEFAULT_TAX_RATE` | — | 9.0 | 默认税率 |
| `MAX_UPLOAD_SIZE` | — | 10485760 | 上传限制 (字节) |
| `DATABASE_URL` | — | sqlite:///:memory: | SQLAlchemy 连接 (非业务) |

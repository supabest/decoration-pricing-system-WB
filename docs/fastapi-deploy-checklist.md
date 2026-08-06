# FastAPI 公网部署检查报告

> 检查日期: 2026-08-06 | 检查对象: `/backend/` | Python 3.9.6

---

## 一、逐项检查结果

### 1. 项目入口文件 ✅

`backend/app/main.py` (59行) — 结构完整。

```python
app = FastAPI(title="装修工程AI套价系统", version="0.1.0")
app.add_middleware(CORSMiddleware, ...)
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
```

**问题**: 无。lifespan、异常处理、中间件都已就绪。

### 2. requirements.txt ❌ 缺失

```
backend/
├── requirements.txt   ← 不存在
├── Pipfile            ← 不存在
└── pyproject.toml     ← 不存在
```

当前依赖全靠系统 pip 全局安装。Render/Fly.io 部署时不知道要安装什么。

**实际需要的依赖** (从代码分析):

| 依赖 | 用途 | 是否必需 |
|------|------|----------|
| `fastapi` | Web 框架 | ✅ |
| `uvicorn` | ASGI 服务器 | ✅ |
| `openpyxl` | Excel 生成 | ✅ |
| `httpx` | Supabase/DeepSeek HTTP | ✅ |
| `pydantic` | 请求校验 | ✅ |
| `pydantic-settings` | 环境变量加载 | ✅ |
| `python-multipart` | 模板上传 FormData | ✅ |
| `SQLAlchemy` | — | ❌ 未被任何端点使用 |
| `bcrypt` | — | ❌ 未被任何端点使用 |
| `passlib` | — | ❌ 未被任何端点使用 |
| `python-jose` | — | ❌ 未被任何端点使用 |

**需新增**: `requirements.txt`，只包含必需依赖 + 版本锁定。

### 3. Python 版本 ⚠️

```
Python 3.9.6
```

**问题**: 3.9 不支持 `dict | None` 语法 (3.10+)，之前 `pricing_debug_logger.py` 因此崩溃，已修复为 `Optional[dict]`。但后续开发可能再次踩坑。

**建议**: 部署时使用 Python 3.10+。Render 默认支持 3.10-3.13。

### 4. 环境变量配置 ⚠️

`.env` 文件内容:
```
DEBUG_PRICING=true
```

**问题清单**:

| 问题 | 严重度 | 说明 |
|------|--------|------|
| SECRET_KEY 硬编码 | 🔴 高 | `"change-me"` — 生产环境必须改为随机字符串 |
| DATABASE_URL 无用 | 🟡 中 | `postgresql://user:password@localhost` — 真实端点不用 SQLAlchemy |
| REDIS_URL 无用 | 🟡 中 | Celery 未被使用 |
| CORS_ORIGINS 仅 localhost | 🔴 高 | Cloudflare Pages 域名不在白名单 |
| DEBUG_PRICING=true | 🟡 中 | 生产环境应关闭 |
| LLM_API_KEY 为空 | 🟢 低 | DeepSeek Key 由前端每次传入，服务端不需要 |

### 5. Supabase 连接方式 ✅

所有端点通过 `httpx` → Supabase REST API 直连，REST key 已正确配置:
```python
SUPABASE_URL = "https://lnvtykghcpsjpwczbqsm.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_..."
```

**问题**: 无。REST API + anon key 可公网访问，不依赖本地数据库。

### 6. DeepSeek Key 管理方式 ✅

DeepSeek API Key 由用户在前端 `#aiKey` 输入框填写，每次请求传入:
```python
# tool.html → FastAPI
POST /api/v1/pricing/single
Body: { "item": {...}, "api_key": "sk-user-provided-key" }
```

服务端不存储 Key，不存在泄露风险。

### 7. CORS 配置 ❌ 问题严重

```python
# config.py
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080"
]
```

**问题**: 只允许 localhost 来源。Cloudflare Pages 域名 (如 `decoration-pricing.pages.dev`) 不在白名单，浏览器会拦截跨域请求。

**修复**: 添加 Cloudflare Pages 域名 + 管理面板域名。

### 8. 文件上传接口 ✅

```python
@router.post("/template")
async def export_template(
    template: UploadFile = File(...),   # Excel 模板文件
    data: str = Form(...),              # JSON 数据
):
    template_bytes = await template.read()  # 读入内存，不存磁盘
```

**问题**: 无。文件直接在内存中处理 (`BytesIO`)，不依赖 `uploads/` 目录。Render 的文件系统是临时的 (ephemeral)，内存处理恰好适配。

### 9. Excel openpyxl 生成接口 ✅

完整的企业级 Excel 生成:
- 方式一: `POST /export/excel` — 全新生成
- 方式二: `POST /export/template` — 模板填充

两者都通过 `StreamingResponse` + `BytesIO` 返回，无需磁盘 I/O。

**问题**: 无。功能完整，适配无状态部署。

---

## 二、当前存在的问题汇总

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| 1 | **缺少 requirements.txt** | 🔴 阻断 | 无法部署 |
| 2 | **CORS 仅 localhost** | 🔴 阻断 | Pages 域名被拦截 |
| 3 | **SECRET_KEY = "change-me"** | 🔴 安全 | 生产风险 |
| 4 | **Python 3.9 语法限制** | 🟡 建议 | 后续开发不便 |
| 5 | **无用依赖 (SQLAlchemy, bcrypt 等)** | 🟡 冗余 | 增加冷启动时间 |
| 6 | **缺少 .gitignore 保护 .env** | 🟡 安全 | .env 可能被提交 |
| 7 | **缺少部署配置 (Procfile/render.yaml)** | 🟡 便利 | 手动配置 |
| 8 | **DATABASE_URL / REDIS_URL 空占位** | 🟢 无害 | 但不干净 |

---

## 三、需要新增的文件

| 文件 | 内容 |
|------|------|
| `backend/requirements.txt` | 7 个必需依赖 + 版本锁定 |
| `backend/runtime.txt` | `python-3.11` (Render 识别) |
| `backend/Procfile` | `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `backend/.gitignore` | `.env`, `__pycache__/`, `uploads/` |

---

## 四、需要修改的文件

| 文件 | 改动 |
|------|------|
| `backend/app/core/config.py` | CORS_ORIGINS 增加 Pages 域名; SECRET_KEY 从环境变量读取; 移除未使用的 DATABASE_URL/REDIS_URL/EMBEDDING_MODEL/VECTOR_DIM/CELERY; DEBUG_PRICING 默认 false |
| `backend/.env` | 添加 SECRET_KEY, CORS_ORIGINS; 移除 DEBUG_PRICING |

---

## 五、推荐免费部署方案

| 平台 | 免费额度 | 适合 | 限制 |
|------|----------|------|------|
| **Render** 🥇 | 750h/月 | Web Service | 15 分钟无流量休眠 |
| Fly.io | $5/月信用 | 全球边缘 | 需要信用卡 |
| Railway | $5/月 | 简单易用 | 免费额度已缩紧 |

**推荐 Render**:
- 免费层 750h/月 ≈ 31 天，单实例够用
- 自动 HTTPS + 自定义域名
- 从 GitHub 自动部署
- 无需信用卡
- 支持 `requirements.txt` 自动安装
- 环境变量 Web UI 配置

---

## 六、部署步骤 (预览)

```
Step 1: 新增 requirements.txt + runtime.txt + Procfile
Step 2: 修改 config.py — CORS + SECRET_KEY
Step 3: 修改 tool.html — BACKEND_URL 指向 Render URL
Step 4: git push → GitHub
Step 5: Render Dashboard → New Web Service → 连接 GitHub 仓库
Step 6: 配置环境变量 (SECRET_KEY, SUPABASE_URL, CORS_ORIGINS)
Step 7: 等待部署完成 → 获取 Render URL
Step 8: 测试: curl https://xxx.onrender.com/health
```

---

## 七、部署后 tool.html 改动

```javascript
// 改前
const BACKEND_URL = 'http://localhost:8000';

// 改后
const BACKEND_URL = 'https://decoration-pricing.onrender.com';
```

只有 1 行。同时上传到 Cloudflare Pages。

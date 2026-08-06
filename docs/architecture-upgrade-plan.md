# 装修工程AI套价系统 — 企业多人在线平台架构升级方案

> 版本: v1.0 | 日期: 2026-08-06 | 状态: 分析阶段，不修改代码

---

## 一、当前系统架构分析

### 1.1 部署拓扑

```
┌─────────────────────────────────────────────────────────┐
│ 用户浏览器                                               │
│  https://decoration-pricing.pages.dev/tool.html          │
│  (Cloudflare Pages — 全球 CDN)                           │
└──────────┬──────────────────────────────────────────────┘
           │ fetch()
           │
    ┌──────┴──────┐          ┌──────────────┐
    │ Supabase    │          │ DeepSeek API  │
    │ (云端)      │          │ (云端)        │
    │ ✅ 多人可用 │          │ ✅ 多人可用   │
    └─────────────┘          └──────────────┘
           ▲                       ▲
           │                       │
    ┌──────┴──────────────────────┴──┐
    │  FastAPI localhost:8000         │
    │  ❌ 仅本机可访问                │
    │  ❌ 无认证/安全层               │
    │  ❌ 无速率限制                   │
    │  ❌ 无日志/监控                 │
    └─────────────────────────────────┘
```

**核心问题**：`tool.html` 的 `BACKEND_URL = 'http://localhost:8000'` 导致除开发者外的所有用户无法使用 AI 套价和 Excel 导出。

### 1.2 tool.html ↔ 后端调用关系

```
tool.html 页面加载:
  ├── GET /health                          → 检测后端状态 (显示 🖥️/⚠️)
  ├── GET /api/v1/knowledge                → 加载知识库 (tips/synonyms/rules)

tool.html AI 套价流程:
  ├── POST /api/v1/pricing/single          → 每条清单 × 1 次
  │    入参: {item: {name, spec, unit}, api_key}
  │    出参: {matched: [{id, sheet, confidence, reason}], overall_confidence, note}
  └── POST /api/v1/pricing/check-consistency → 套完后 1 次 (相似清单校验+自动补全)

tool.html Excel 导出:
  ├── POST /api/v1/export/excel            → 方式一: 配置导出 (生成全新 Excel)
  └── POST /api/v1/export/template         → 方式二: 模板导出 (读入用户模板填入数据)

tool.html 其他:
  ├── POST /api/v1/knowledge               → 记录 AI 学习到的规则
  └── GET /api/v1/pricing/debug-logs       → 查看调试日志
```

### 1.3 FastAPI 当前功能矩阵

| 类别 | 端点 | 行数 | 核心依赖 | 可迁移性 |
|------|------|------|----------|----------|
| **AI 套价** | `POST /pricing/single` | 349 | httpx, re, json | 🟢 Workers |
| | `POST /pricing/batch` | | | 🟢 Workers |
| **候选匹配** | `build_candidates()` | 349 内 | 2-gram 分词+评分 | 🟢 Workers |
| **知识库** | `GET/POST /knowledge` | 78 | httpx, Supabase | 🟢 Workers |
| **相似度校验** | `POST /pricing/check-consistency` | 283 | Jaccard 算法 | 🟢 Workers |
| **调试日志** | `GET /pricing/debug-logs` | 131 | httpx, Supabase | 🟢 Workers |
| **Excel 导出** | `POST /export/excel` | 490 | **openpyxl** | 🔴 必须 Python |
| | `POST /export/template` | 394 | **openpyxl** | 🔴 必须 Python |
| **空壳端点** | 8 个 CRUD 端点 | ~350 | — | ⬜ 直接删除 |

### 1.4 数据流详解

#### AI 套价流程 (price_single)

```
输入: {name, spec, unit, api_key}
  │
  ├─1─ load_benchmark_data()  ──── Supabase REST (497条) ──┬── 缓存 24h
  │                                                         │
  ├─2─ load_knowledge()        ──── Supabase REST ──────────┘    fallback: JSON
  │
  ├─3─ route_teams()           ──── 8组关键词 → 班组列表
  │    例: "大板砖+背胶" → ["泥水班组"]
  │
  ├─4─ build_candidates()      ──── 2-gram 分词 + 评分 → Top 80
  │    评分规则: 名称匹配+2, spec匹配+1, 单位匹配+3, 工艺关键词+4
  │
  ├─5─ engineering_parse()     ──── 提取: 班组+工艺+材料类型
  │
  ├─6─ build_system_prompt()   ──── 知识库 + 工序拆解原则 → 系统Prompt
  │
  ├─7─ build_user_prompt()     ──── 候选子目列表 → 用户Prompt
  │
  ├─8─ call_deepseek()         ──── POST api.deepseek.com (max_tokens=2000)
  │
  ├─9─ parse_ai_response()     ──── 提取 JSON + 校验子目真实存在
  │
  └─10─ save_debug_log()       ──── Supabase ai_pricing_logs (条件: DEBUG_PRICING=true)
```

#### Excel 导出流程

```
前端 collectExportData()
  │
  │  收集所有 BOQ 行、子目、分部、列映射
  │
  ├── 方式一: POST /export/excel
  │     ├── ExcelExporter (490 行)
  │     │   ├── 创建 Workbook
  │     │   ├── 写入标题行(合并单元格)
  │     │   ├── 写入表头
  │     │   ├── 逐行写入数据+子目
  │     │   ├── 设置 Excel 公式 (SUM/管理费/利润/合价)
  │     │   ├── 设置样式 (字体/边框/颜色/对齐)
  │     │   ├── 设置折叠 (分组+大纲级别)
  │     │   ├── 计算行高 (中文宽度估算)
  │     │   └── 返回 .xlsx 二进制流
  │     └── openpyxl 专属功能:
  │         • ws.merge_cells() — 合并单元格
  │         • ws.row_dimensions.group() — 分组折叠
  │         • ws.sheet_properties.outlinePr — 大纲方向
  │         • Font(name='微软雅黑') — 中文字体
  │         • Border/Side/PatternFill — 企业格式
  │         • 公式字符串 (SUM/IF/四则运算)
  │
  └── 方式二: POST /export/template
        ├── TemplateExcelExporter (394 行)
        │   ├── load_workbook() 读取用户模板
        │   ├── insert_rows() 动态插入子目行
        │   ├── _copy_row_style() 复制父行格式到子行
        │   ├── 按列映射填入数据
        │   └── 同方式一的样式+公式+折叠
        └── openpyxl 额外需求:
            • ws.insert_rows() — 行插入
            • ws.cell().font/border/fill 复制
```

---

## 二、目标架构设计

### 2.1 部署拓扑

```
用户 (多人, 全球)
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ Cloudflare Pages                                        │
│  tool.html + admin.html + React 前端                     │
│  BACKEND_URL = https://api.decoration-pricing.workers.dev│
└──────────┬──────────────────────────────────────────────┘
           │ HTTPS
           ▼
┌──────────────────────────────────────────────────────────┐
│ Cloudflare Workers (API 网关 + 安全层)                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 安全层                                           │   │
│  │  • API Key 验证 (JWT / HMAC)                     │   │
│  │  • 速率限制 (Rate Limiting)                      │   │
│  │  • CORS 管理                                     │   │
│  │  • 请求日志                                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 业务路由                                         │   │
│  │  • POST /api/v1/pricing/single ──────┐           │   │
│  │  • POST /api/v1/pricing/check-...  ──┤           │   │
│  │  • GET/POST /api/v1/knowledge ───────┤ Workers   │   │
│  │  • GET /api/v1/pricing/debug-logs ───┤ 直接处理  │   │
│  │  • POST /api/v1/export/* ────────────┼───┐       │   │
│  └──────────────────────────────────────┘   │       │   │
│                                              │       │   │
└──────────────────────────────────────────────┼───────┼───┘
                                               │       │
                          ┌────────────────────┘       │
                          ▼                            ▼
                    ┌──────────┐              ┌──────────────┐
                    │ Supabase │              │ DeepSeek API  │
                    │ (云端)   │              │ (云端)        │
                    └──────────┘              └──────────────┘
                          ▲
                          │
┌─────────────────────────┼──────────────────────────────┐
│ FastAPI (工程计算服务)   │                              │
│  可部署: Render / Fly.io / 阿里云 ECS                    │
│                                                         │
│  POST /api/v1/export/excel    ← Workers 转发            │
│  POST /api/v1/export/template ← Workers 转发            │
│                                                         │
│  其他功能已迁移到 Workers，FastAPI 仅保留 Excel 生成     │
│  (880 行 → ~100 行，仅保留 openpyxl 核心)               │
└─────────────────────────────────────────────────────────┘
```

### 2.2 职责划分

| 层 | 职责 | 技术 |
|----|------|------|
| **Cloudflare Pages** | 静态前端托管、CDN 加速 | HTML/JS |
| **Cloudflare Workers** | API 网关、认证、速率限制、AI 套价、知识库、相似度校验、调试日志 | TypeScript |
| **FastAPI** | Excel 生成 (openpyxl) | Python |
| **Supabase** | 数据持久化、RLS 权限 | PostgreSQL |
| **DeepSeek** | AI 推理 | API |

### 2.3 Workers API 端点设计

```
# === Workers 直接处理 (从 FastAPI 迁移) ===
GET  /health                              → {status:"ok"}
POST /api/v1/pricing/single               → AI 单行套价
POST /api/v1/pricing/check-consistency    → 相似清单校验+自动补全
GET  /api/v1/knowledge                    → 知识库查询
POST /api/v1/knowledge                    → 知识库新增
GET  /api/v1/pricing/debug-logs           → 调试日志查看

# === Workers 代理转发 (保留 Python) ===
POST /api/v1/export/excel                 → 转发 FastAPI
POST /api/v1/export/template              → 转发 FastAPI
```

### 2.4 数据流变更

```
迁移前:
  tool.html ──fetch──▶ localhost:8000 ──httpx──▶ Supabase
                      localhost:8000 ──httpx──▶ DeepSeek

迁移后:
  tool.html ──fetch──▶ api.xxx.workers.dev ──fetch──▶ Supabase
                      api.xxx.workers.dev ──fetch──▶ DeepSeek
                      api.xxx.workers.dev ──fetch──▶ FastAPI (Excel only)
```

---

## 三、迁移分析 — 逐功能

### 3.1 AI 套价核心 (price_single) → Workers

| Python 函数 | 行数 | TS 等效实现 |
|-------------|------|------------|
| `route_teams()` | 10 | `routeTeams()` — `Array.some()` + `Set` |
| `build_candidates()` | 40 | `buildCandidates()` — 2-gram + 评分，JS 更简洁 |
| `engineering_parse()` | 25 | `engineeringParse()` — 同上 |
| `build_system_prompt()` | 36 | `buildSystemPrompt()` — 模板字符串 |
| `build_user_prompt()` | 20 | `buildUserPrompt()` — 模板字符串 |
| `call_deepseek()` | 15 | `callDeepSeek()` — `fetch()` |
| `parse_ai_response()` | 5 | `parseAiResponse()` — `JSON.parse()` |
| `load_benchmark_data()` | 38 | `loadBenchmark()` — Supabase fetch + 缓存 |
| `load_knowledge()` | 34 | `loadKnowledge()` — Supabase fetch + 缓存 |
| **合计** | **223** | **~150 行 TypeScript** |

**迁移难度**: 🟢 低。纯 HTTP 调用 + 字符串处理，无 Python 专属依赖。

**关键注意**:
- `_benchmark_cache` / `_knowledge_cache` 在 Workers 中用全局变量，利用 warm request 复用
- benchmark_data.json / ai_knowledge_base.json fallback → Workers 可用 KV 存储

### 3.2 相似度校验 (similarity_checker) → Workers

| Python 函数 | 行数 | TS 等效 |
|-------------|------|---------|
| `_bigrams()` | 7 | `bigrams()` — `Set.add()` |
| `_jaccard()` | 5 | `jaccard()` — 直接翻译 |
| `_name_similarity()` | 3 | `nameSimilarity()` |
| `_spec_similarity()` | 3 | `specSimilarity()` |
| `_engineering_similarity()` | 15 | `engineeringSimilarity()` |
| `compute_similarity()` | 12 | `computeSimilarity()` |
| `_find_similar_groups()` | 22 | `findSimilarGroups()` — Union-Find |
| `check_consistency()` | 100 | `checkConsistency()` |
| **合计** | **167** | **~120 行 TypeScript** |

**迁移难度**: 🟢 低。纯算法，Jaccard + Union-Find 在 JS 中语法几乎一致。

### 3.3 知识库 (knowledge) → Workers

| Python 函数 | 行数 | TS 等效 |
|-------------|------|---------|
| `GET /knowledge` | 10 | `GET /knowledge` — fetch Supabase |
| `POST /knowledge` | 30 | `POST /knowledge` — fetch Supabase INSERT |
| `load_knowledge()` | 34 | 已在 pricing 中实现 |
| **合计** | **74** | **~40 行 TypeScript** |

**迁移难度**: 🟢 低。简单 CRUD。

### 3.4 调试日志 (pricing_debug_logger) → Workers

**迁移难度**: 🟢 低。Supabase INSERT + SELECT，`PricingDebugLog` 类直接翻译。

### 3.5 Excel 导出 (excel_export + template_export) → 保留 FastAPI

**不可迁移原因**:
- `openpyxl` 是 Python 专属库，Workers 无替代
- 企业 Excel 需求复杂：合并单元格、大纲折叠、中文字体、公式、行高估算
- SheetJS (xlsx) 在 Workers 环境可用，但不支持：`ws.merge_cells()`、`ws.sheet_properties.outlinePr`、`PatternFill`、动态行插入+样式复制
- 884 行 Python 逻辑如果强行用 JS 重写 → 2000+ 行且功能残缺

**保留方案**:
- FastAPI 精简为仅保留 Excel 导出端点
- 部署到 Render / Fly.io (免费额度足够)
- Workers 将 Excel 请求透明代理转发到 FastAPI

### 3.6 空壳端点 → 删除

8 个 CRUD 端点（enterprise_price, material_price, quota, bill_of_quantities, ai_recommend, auto_match, auto_pricing, project）全部是空壳，返回 `ApiResponse(data={})`。不迁移。

---

## 四、迁移风险清单

| 风险 | 等级 | 影响 | 缓解措施 |
|------|------|------|----------|
| Workers 10ms CPU 限制 | 🟢 低 | AI 套价是 IO-heavy (等 DeepSeek)，非 CPU 密集型。候选匹配 + Jaccard <5ms | 已验证 benchmark |
| Workers 30s 超时 | 🟢 低 | DeepSeek 调用 <10s，单条套价 <15s | 无需特殊处理 |
| 冷启动 | 🟢 低 | Workers V8 isolates <50ms | 可忽略 |
| Supabase anon key 暴露 | 🟡 中 | Worker 代码硬编码 key，与当前 tool.html 相同安全级别 | Workers 环境变量隔离 |
| DeepSeek API Key 安全 | 🟡 中 | 用户在前端输入，经 Workers 转发 | 不存储 key，每次传入 |
| Excel 代理转发延迟 | 🟡 中 | Workers→FastAPI 增加一跳 | Render 选同区域减少延迟 |
| FastAPI 部署成本 | 🟢 低 | Render 免费层 750h/月 | 够用 |
| 知识库 JSON fallback | 🟡 中 | Workers 无本地文件系统 | KV Store 存储 JSON 兜底 |
| 多人并发 DeepSeek | 🟡 中 | 企业多人同时套价 | Workers 速率限制 + 队列 |
| 数据一致性 | 🟢 低 | Supabase 是唯一数据源 | 不变 |

---

## 五、分阶段改造计划

### Phase 1: Workers 项目搭建 (2-3h)

```
目标: Workers 跑通基本路由，代理转发 Excel 请求

文件:
  workers/
  ├── wrangler.toml           # 配置: 路由、环境变量、KV binding
  ├── package.json             # 依赖: hono (轻量路由)
  ├── tsconfig.json
  └── src/
      ├── index.ts             # Hono 路由入口
      └── types.ts             # 共享类型

tool.html 改动:
  1 行: BACKEND_URL → https://api.xxx.workers.dev

验证:
  curl https://api.xxx.workers.dev/health → {"status":"ok"}
  curl https://api.xxx.workers.dev/api/v1/export/excel → 转发 FastAPI 成功
```

### Phase 2: 迁移 AI 套价 + 知识库 (4-6h)

```
文件:
  workers/src/
  ├── pricing.ts              # 从 ai_pricing_service.py 翻译
  ├── knowledge.ts            # 从 knowledge.py 翻译
  ├── benchmark.ts            # benchmark 数据加载+缓存
  ├── prompt.ts               # System/User Prompt 模板
  └── deepseek.ts             # DeepSeek API 封装

移除:
  backend/app/api/v1/endpoints/ai_pricing.py (端点层)
  backend/app/api/v1/endpoints/knowledge.py (端点层)
  backend/app/services/ai_pricing_service.py (服务层, ~250行)
  → FastAPI 不再处理 AI 套价

验证:
  1. tool.html AI 套价 → Workers 返回正确匹配
  2. 知识库查看器 → Workers 返回完整知识库
  3. 套价后 recordAiRule → Workers 写入 Supabase
  4. 相似度校验 → 自动补全正常工作
```

### Phase 3: 迁移调试日志 + 校验 (1-2h)

```
文件:
  workers/src/
  ├── similarity.ts           # 从 similarity_checker.py 翻译
  └── debug.ts                # 从 pricing_debug_logger.py 翻译

移除:
  backend/app/services/similarity_checker.py
  backend/app/services/pricing_debug_logger.py

验证:
  1. 套价后 check-consistency 正常
  2. debug-logs?format=html 正常显示
```

### Phase 4: 精简 FastAPI (1h)

```python
# 精简后的 FastAPI — 仅保留 Excel 导出
# backend/app/main.py → ~30 行

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.export import router as export_router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(export_router, prefix="/api/v1/export")

@app.get("/health")
def health():
    return {"status": "ok", "service": "excel-export"}
```

### Phase 5: 部署 FastAPI 到 Render (1h)

```
Render 配置:
  Build Command: pip install fastapi uvicorn openpyxl httpx pydantic
  Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  环境变量:
    SUPABASE_URL=https://lnvtykghcpsjpwczbqsm.supabase.co
    SUPABASE_ANON_KEY=sb_publishable_...

Workers 配置:
  EXCEL_SERVICE_URL = https://decoration-pricing.onrender.com
  → Excel 请求转发到此 URL
```

### Phase 6: 生产上线 (1h)

```
1. Workers 绑定自定义域名: api.decoration-pricing.workers.dev
2. tool.html 上线 (BACKEND_URL 指向 Workers)
3. 关闭本地 localhost:8000
4. 监控: Cloudflare Analytics + Supabase 查询日志
```

---

## 六、需要修改的文件清单

### 新建

| 文件 | 说明 |
|------|------|
| `workers/wrangler.toml` | Workers 配置 |
| `workers/package.json` | 依赖: hono |
| `workers/tsconfig.json` | TypeScript 配置 |
| `workers/src/index.ts` | 路由 + 安全中间件 |
| `workers/src/pricing.ts` | AI 套价 (from ai_pricing_service.py) |
| `workers/src/knowledge.ts` | 知识库 (from knowledge.py) |
| `workers/src/similarity.ts` | 相似度校验 (from similarity_checker.py) |
| `workers/src/benchmark.ts` | 基准价加载 |
| `workers/src/prompt.ts` | Prompt 模板 |
| `workers/src/deepseek.ts` | DeepSeek 封装 |
| `workers/src/debug.ts` | 调试日志 |
| `workers/src/types.ts` | 共享类型 |

### 修改

| 文件 | 改动 |
|------|------|
| `docs/tool.html` | `BACKEND_URL` 改为 Workers 地址 |
| `frontend/public/tool.html` | 同步 |
| `backend/app/main.py` | 精简为仅 Excel 导出 (~30 行) |

### 删除/归档

| 文件 | 说明 |
|------|------|
| `backend/app/api/v1/endpoints/ai_pricing.py` | 已迁移到 Workers |
| `backend/app/api/v1/endpoints/knowledge.py` | 已迁移到 Workers |
| `backend/app/services/ai_pricing_service.py` | 已迁移到 Workers |
| `backend/app/services/similarity_checker.py` | 已迁移到 Workers |
| `backend/app/services/pricing_debug_logger.py` | 已迁移到 Workers |
| `backend/app/ai/` 整个目录 | 空壳，从未使用 |
| `backend/app/api/v1/endpoints/` 中 8 个 stub 端点 | 空壳 CRUD |
| `backend/app/db/` | SQLAlchemy，未被使用 |
| `backend/app/core/config.py` | 精简为 Excel 所需配置 |

### 不变

| 文件 | 原因 |
|------|------|
| `docs/admin.html` | 直连 Supabase，不依赖 FastAPI |
| `frontend/src/` (React) | 直连 Supabase |
| `docs/ai_knowledge_base.json` | Worker 从 Supabase 加载，JSON 作为 KV fallback |
| `docs/benchmark_data.json` | 同上 |
| `data/seeds/` | 数据库恢复脚本 |
| `backend/app/services/excel_export.py` | 保留，仅 Excel 用途 |
| `backend/app/services/template_export.py` | 保留，仅 Excel 用途 |

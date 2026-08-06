# 装修成本AI套价系统 — 架构分析与Cloudflare Workers迁移方案

## 一、当前架构分析报告

### 1.1 当前部署架构

```
┌──────────────────────────────────────────────────┐
│ Cloudflare Pages                                  │
│  tool.html + admin.html + React 前端              │
│  GitHub: supabest/decoration-pricing-system       │
└──────────┬───────────────────────────────────────┘
           │ fetch() 直连
           ▼
┌──────────────────────────────────────────────────┐
│ Supabase (云端)                                   │
│  benchmark_items, material_prices, ai_knowledge   │
│  ai_pricing_logs, profiles, projects              │
└──────────────────────────────────────────────────┘
           ▲
           │ httpx (Python)
┌──────────┴──────────────┐       ┌───────────────┐
│ FastAPI (localhost:8000)│──────▶│ DeepSeek API   │
│  仅本地可访问           │       │ api.deepseek.. │
└─────────────────────────┘       └───────────────┘
```

**当前问题**：FastAPI 运行在 `localhost:8000`，仅开发者本机可用。其他用户打开 Cloudflare Pages 的 tool.html，AI 套价功能不可用（`BACKEND_URL` 指向 localhost）。

### 1.2 tool.html ↔ FastAPI 调用关系

| 前端调用 | 频率 | 端点 | 说明 |
|----------|------|------|------|
| `checkBackend()` | 页面加载 | `GET /health` | 检测后端状态 |
| `getKnowledge()` | 页面加载 | `GET /api/v1/knowledge` | 加载知识库 |
| `recordAiRule()` | 套价后 | `POST /api/v1/knowledge` | 记录新规则 |
| `priceOne()` | 每条清单×1 | `POST /api/v1/pricing/single` | AI 单行套价 |
| `startAiPricing()` 校验 | 一次 | `POST /api/v1/pricing/check-consistency` | 相似清单一致性 |
| `doExport()` | 导出时 | `POST /api/v1/export/excel` | Excel 方式一导出 |
| `doTemplateExport()` | 导出时 | `POST /api/v1/export/template` | Excel 方式二导出 |
| 调试查看 | 手动 | `GET /api/v1/pricing/debug-logs` | 调试日志 |

### 1.3 FastAPI 功能清单与迁移评估

| 模块 | 行数 | 功能 | 核心依赖 | 迁移难度 |
|------|------|------|----------|----------|
| `ai_pricing_service.py` | 349 | 候选匹配/DeepSeek调用/知识库加载 | httpx, json, re | 🟢 低 — 纯 HTTP+字符串 |
| `similarity_checker.py` | 283 | 相似度计算/一致性校验 | ai_pricing_service | 🟢 低 — 纯算法 |
| `pricing_debug_logger.py` | 131 | 调试日志收集/存储 | httpx→Supabase | 🟢 低 — 改成 KV/D1 |
| `excel_export.py` | 490 | openpyxl 生成 Excel | **openpyxl** | 🔴 高 — Python 专属库 |
| `template_export.py` | 394 | openpyxl 模板导出 | **openpyxl** | 🔴 高 — Python 专属库 |
| `knowledge.py` (端点) | 78 | 知识库 CRUD API | httpx | 🟢 低 |
| `ai_pricing.py` (端点) | 147 | 套价+校验+调试端点 | 各 service | 🟢 低 |

### 1.4 Python 专有依赖

| 依赖 | 用途 | Workers 替代方案 |
|------|------|------------------|
| `openpyxl` | Excel 读写/格式化/公式/折叠 | **SheetJS (xlsx)** — 浏览器端已有 |
| `uvicorn` | HTTP 服务器 | Cloudflare Workers 内置 |
| `pydantic` | 请求校验 | Zod / 手写校验 |
| `pydantic-settings` | 环境变量 | `env` binding / wrangler.toml |

### 1.5 结论：可迁移性

- **可完整迁移**：AI 套价、知识库、候选匹配、相似度校验、调试日志（~900 行 Python → ~600 行 TS）
- **不应迁移**：Excel 导出（openpyxl 在 Workers 无替代，但 `tool.html` 已有 SheetJS 客户端导出能力）
- **已有客户端方案**：前端 `collectExportData()` 早已实现 SheetJS 导出，后端 Excel 服务是为兼容旧版保留

---

## 二、Cloudflare Workers 迁移方案

### 2.1 目标架构

```
┌─────────────────────────────────────────────────┐
│ Cloudflare Pages                                 │
│  tool.html + admin.html + React 前端             │
└──────────┬──────────────────────────────────────┘
           │ fetch()
           ▼
┌──────────────────────────────────────────────────┐
│ Cloudflare Workers (api.decoration-pricing.xxx)   │
│  POST /api/v1/pricing/single                     │
│  POST /api/v1/pricing/check-consistency           │
│  GET  /api/v1/knowledge                          │
│  POST /api/v1/knowledge                          │
│  GET  /api/v1/pricing/debug-logs                 │
│  GET  /health                                    │
└──────────┬───────────────────────────────────────┘
           │ fetch()
           ▼
┌──────────────────────────────────────────────────┐
│ Supabase (不变)                    DeepSeek API   │
└──────────────────────────────────────────────────┘
```

### 2.2 Workers 项目结构

```
workers/
├── wrangler.toml              # CF Workers 配置
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts               # 路由入口
│   ├── pricing.ts             # AI 套价主逻辑 (from ai_pricing_service.py)
│   ├── knowledge.ts           # 知识库加载 (from load_knowledge)
│   ├── similarity.ts          # 相似度校验 (from similarity_checker.py)
│   ├── benchmark.ts           # 基准价加载 (from load_benchmark_data)
│   ├── prompt.ts              # Prompt 构建 (from build_system/user_prompt)
│   ├── deepseek.ts            # DeepSeek API 调用
│   ├── debug.ts               # 调试日志 (from pricing_debug_logger)
│   └── types.ts               # TypeScript 类型定义
```

### 2.3 迁移映射

| Python 函数 | Workers TS 函数 | 说明 |
|-------------|----------------|------|
| `route_teams()` | `routeTeams()` | 纯字符串匹配，直接翻译 |
| `build_candidates()` | `buildCandidates()` | 2-gram 分词+评分，JS 版更简洁 |
| `engineering_parse()` | `engineeringParse()` | 同 route_teams 逻辑 |
| `build_system_prompt()` | `buildSystemPrompt()` | 字符串拼接 |
| `build_user_prompt()` | `buildUserPrompt()` | 字符串拼接 |
| `call_deepseek()` | `callDeepSeek()` | fetch() 直发 |
| `parse_ai_response()` | `parseAiResponse()` | JSON.parse() |
| `price_single()` | `priceSingle()` | 串联上述函数 |
| `check_consistency()` | `checkConsistency()` | 翻译相似度算法 |
| `load_knowledge()` | `loadKnowledge()` | Supabase fetch |
| `load_benchmark_data()` | `loadBenchmark()` | Supabase fetch |
| `save_debug_log()` | `saveDebugLog()` | Supabase INSERT |
| `ExcelExporter` | ❌ 删除 | 前端 SheetJS 已覆盖 |

### 2.4 代码量估算

| 指标 | Python (当前) | TypeScript (目标) |
|------|--------------|-------------------|
| AI 套价核心 | ~350 行 | ~200 行 |
| 相似度校验 | ~280 行 | ~180 行 |
| 调试日志 | ~130 行 | ~100 行 |
| 知识库 API | ~80 行 | ~50 行 |
| Excel 导出 | ~900 行 | 删除（前端已有） |
| 路由/配置 | 分散 | ~50 行 (index.ts) |
| **总计** | **~1740 行** | **~580 行** |

### 2.5 tool.html 改动

只需改 1 行：

```javascript
// 改前
const BACKEND_URL = 'http://localhost:8000';

// 改后
const BACKEND_URL = 'https://api.decoration-pricing.workers.dev';
```

### 2.6 风险与应对

| 风险 | 等级 | 应对 |
|------|------|------|
| Workers 10ms CPU 限制 | 中 | AI 套价是 IO-heavy（等 DeepSeek），非 CPU-heavy。候选匹配 <5ms |
| Workers 30s 超时 | 低 | DeepSeek API 调用 <10s，批量套价逐条处理 |
| 冷启动延迟 | 低 | Workers 通常 <50ms，V8 isolates 极快 |
| openpyxl 功能丢失 | 低 | SheetJS 在前端已实现，测试确认即可 |
| 环境变量泄漏 | 中 | DeepSeek Key 由用户传入，不存 Workers 环境变量 |
| Supabase anon key 暴露 | 低 | Worker 代码中 hardcode anon key（与当前 tool.html 相同安全级别） |

---

## 三、需要修改的文件列表

### 新建文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `workers/wrangler.toml` | ~20 | Workers 配置 |
| `workers/package.json` | ~15 | 依赖声明 |
| `workers/tsconfig.json` | ~10 | TS 配置 |
| `workers/src/index.ts` | ~80 | 路由分发 |
| `workers/src/pricing.ts` | ~200 | AI 套价核心 |
| `workers/src/knowledge.ts` | ~50 | 知识库加载 |
| `workers/src/similarity.ts` | ~180 | 相似度校验 |
| `workers/src/benchmark.ts` | ~30 | 基准价加载 |
| `workers/src/prompt.ts` | ~60 | Prompt 构建 |
| `workers/src/deepseek.ts` | ~30 | DeepSeek 调用 |
| `workers/src/debug.ts` | ~80 | 调试日志 |
| `workers/src/types.ts` | ~30 | 类型定义 |

### 修改文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `docs/tool.html` | 改 1 行 | `BACKEND_URL` 指向 Workers |
| `frontend/public/tool.html` | 同步 | 同上 |

### 可删除/归档

| 文件 | 说明 |
|------|------|
| `backend/` 整个目录 | Workers 替代后不再需要本地 FastAPI |
| 或保留 `backend/` 用于本地调试 | 加注释标记为 deprecated |

### 不需要修改

| 文件 | 原因 |
|------|------|
| `docs/admin.html` | 直连 Supabase，不依赖 FastAPI |
| `frontend/src/` (React) | 直连 Supabase |
| `docs/ai_knowledge_base.json` | Worker 从 Supabase 加载，JSON 仍是 fallback |
| `docs/benchmark_data.json` | Worker 优先 Supabase，JSON 兜底 |
| `data/seeds/` | 不变 |

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 分支策略（永久规则）

> **默认在 `dev` 分支进行所有开发工作，禁止直接在 `main` 分支修改代码。**

- **`main`** — 稳定版 v1.3.0，生产环境，Render + Cloudflare Pages 自动部署。**只接受 merge，禁止直接提交。**
- **`dev`** — 日常开发分支。**所有代码修改、新功能、bug 修复都在此分支进行。** 稳定后 merge 到 main 上线。
- 每次开始工作前执行 `git branch` 确认当前在 `dev` 分支，如果在 `main` 则执行 `git checkout dev`。

## 项目概述

装修成本分析系统 — 装修工程人工费+材料费智能套价工具。

- **后端**: Python 3.12, FastAPI, LangChain → DeepSeek API, Supabase PostgreSQL + Auth + REST API（Render 部署）
- **前端**: React + TypeScript + Vite（Cloudflare Pages 部署）
- **核心工具**: `docs/tool.html`（~2600行纯 HTML/CSS/JS 单页应用）
- **生产**: https://decoration-pricing-system.pages.dev（Pages）+ https://decoration-pricing-system.onrender.com（Render）
- **版本**: V1.3.0
- **仓库**: 私有（GitHub）

## 本地开发

```bash
# 套价工具 + 管理面板（纯 HTML，无需构建）
cd docs && python3 -m http.server 8080
# → http://localhost:8080/tool.html
# → http://localhost:8080/admin.html

# FastAPI 后端（AI 套价 + Excel 导出）
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000/docs

# React 前端
cd frontend && npm run dev
# → http://localhost:5173
```

localhost 环境自动免登录（tool.html 和 admin.html 均已适配）。

## 核心架构

### 数据流

```
用户上传 BOQ（Excel/手动输入）
    ↓
tool.html 渲染清单 → Supabase REST API 读取 497 条基准价
    ↓
用户点击「AI 套价」→ 未匹配行 → FastAPI 后端 → DeepSeek API
    ↓
DeepSeek 返回子目匹配 + 辅材配方 → tool.html 计算综合单价
    ↓
导出 Excel（方式一：后端 openpyxl 生成 / 方式二：模板填入）
```

### 关键文件

| 文件 | 说明 |
|------|------|
| `docs/tool.html` | **核心套价工具** — BOQ 导入、基准价侧栏、AI 套价、Excel 导出 |
| `docs/admin.html` | 管理面板 — 用户管理 / 信息价录入 / 知识库 / 基准价浏览 |
| `docs/v5.html` | V5 实验版 — AI 套价独立测试页面 |
| `docs/ai_knowledge_base.json` | **AI 知识库** — tips/synonyms/rules 三类规则驱动 AI 匹配决策 |
| `docs/benchmark_data.json` | 497 条基准价完整备份（含辅材配方），localhost 离线备用 |
| `backend/app/ai/engine.py` | LangChain → DeepSeek LLM 初始化（`deepseek-v4-pro`） |
| `backend/app/services/ai_pricing_service.py` | AI 套价核心服务：工程解析 → 候选匹配 → AI 推理 |
| `backend/app/services/pricing_debug_logger.py` | 调试日志收集器，`DEBUG_PRICING=true` 时写入 `ai_pricing_logs` 表 |
| `backend/app/services/similarity_checker.py` | 相似清单一致性校验 — 2-gram Jaccard + 子目差异检测 |
| `backend/app/services/excel_export.py` | 方式一导出引擎 — openpyxl 生成 Excel（公式、折叠、自动行高） |
| `backend/app/services/template_export.py` | 方式二导出引擎 — 读入用户模板，填入数据+插入子目行 |
| `frontend/src/` | React 页面（登录、工作台、基准价查询、辅材规则等） |

### AI 模型配置（DeepSeek + 智谱）

- 默认模型: `deepseek-v4-pro`（配置在 `backend/app/core/config.py` 的 `LLM_MODEL`）
- 支持模型（前端 AI 面板下拉选择，`model` 字段经 `/pricing/single` 透传到 `call_deepseek`）：
  - `deepseek-v4-pro`（强，默认）/ `deepseek-v4-flash`（省·快）
  - `glm-5.3-flash`（智谱·快）— `call_deepseek` 的 `_resolve_base_url` 按 model 前缀路由：`glm*` → `LLM_BASE_URL_ZHIPU`（默认 `https://open.bigmodel.cn/api/paas/v4`，国际版可覆盖），其余 → `LLM_BASE_URL`
- API Key 由用户在前端 AI 面板输入（仅本次使用，不保存），经 `/pricing/single` 透传，**需与所选模型厂商匹配**
- 模型名出现在 `backend/app/core/config.py` 和 `docs/tool.html` 两处（`docs/v5.html` 已删除），修改时需两处同步
- API 走 OpenAI 兼容 `/chat/completions`，temperature=0
- **`deepseek-v4-pro` 是推理模型**，`backend/app/services/ai_pricing_service.py` 的 `call_deepseek` 必须：
  - `max_tokens=settings.LLM_MAX_TOKENS`（8000，曾因 2000 太小被推理吃光，导致 `content` 空/截断，大量清单「套不上价」）
  - `timeout=settings.LLM_TIMEOUT_SECONDS`（180，曾因 60 太短，推理长时 ReadTimeout）
  - 先读 `message.content`，为空回退读 `message.reasoning_content`
  - `parse_ai_response` 已做健壮解析（兼容代码块/前后杂质/截断 JSON 修复）
- 相关参数已固化在 `config.py`：`LLM_MAX_TOKENS` / `LLM_TIMEOUT_SECONDS` / `CONFIDENCE_LOW_THRESHOLD`（70，低于此值导出备注列标 ⚠️低置信度）
- 回归测试：`backend/tests/test_services/test_parse_ai_response.py`（可 `python` 直跑，也兼容 pytest）
- ⚠️ 这几处是 2026-08-16 修复过的「易丢失」点，改回 `max_tokens=2000` 或删掉 `reasoning_content` 回退会导致套价成功率骤降，勿回退

### AI 知识库 (`docs/ai_knowledge_base.json`)

三类规则:
- **tips**: 通用提示（多工序拆解、天棚路由、排查指南）
- **synonyms**: 同义词映射（扇灰→刮腻子、硬包→软包/饰面板 等 15 组）
- **rules**: 套价规则（大板砖墙面、门槛石、灯槽、窗帘盒、假梁天花侧板、单位换算 等 24 条）

同步到 Supabase: 通过 `admin.html` 管理面板的 📤 上传按钮，或 SQL Editor 执行 SQL。

## Supabase

- URL: `https://lnvtykghcpsjpwczbqsm.supabase.co`
- Anon key: `sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q`
- 前端通过 Fetch API 直连（`_get`/`_post`/`_patch`/`_del` 封装在 tool.html）

### RLS 策略

| 表 | SELECT | INSERT/UPDATE/DELETE |
|----|--------|---------------------|
| `benchmark_items` | `authenticated` 均可读 | 需 `is_admin=true` |
| `material_prices` | 公开（无 RLS） | 需 `is_admin=true` |
| `profiles` | — | 仅管理员 |

### 数据库当前状态（2026-08-07）

| 表 | 行数 | 备注 |
|----|------|------|
| `benchmark_items` | 497 | FIXED 432 / RATE 63 / GROUP 2，含 aux 辅材配方 |
| `material_prices` | 21 | 21 种辅材信息价（2024-01 基准价） |
| `main_material_catalog` | 226 | 主材目录+价格 |
| `ai_pricing_logs` | — | 调试日志（`DEBUG_PRICING=true` 时写入） |

### 数据库恢复

```sql
-- RLS 修复
DROP POLICY IF EXISTS benchmark_read_approved ON benchmark_items;
CREATE POLICY benchmark_read_auth ON benchmark_items FOR SELECT TO authenticated USING (true);

-- 数据恢复: Table Editor → Import CSV 或 SQL Editor 执行 data/seeds/ 下文件
```

## 计价公式

```
综合单价 = 人工单价 + 主材费×(1+损耗率/100) + 辅材费 + 管理费 + 利润
管理费   = 人工单价 × 管理费率%
利润     = 人工单价 × 利润率%
合价     = 综合单价 × 工程量
```

## Excel 导出（FastAPI 后端 + openpyxl）

### 方式一：配置导出 `POST /api/v1/export/excel`

`collectExportData()` 收集 BOQ 数据 → `ExcelExporter` 生成新 sheet。

关键行为:
- 折叠层级: 分部(1)→清单(2)→子目(3)，子目初始 `hidden: true`
- 公式: 管理费/利润=lab×rate，综合单价=Σ各项，合价=usp×qty
- 合计行仅合价列 SUM，通过 `main_row_indices`（仅父行）避免子目双倍计数
- 编号列仅子目行显示基准价编号，清单行留空

### 方式二：模板导出 `POST /api/v1/export/template`

前端解析模板识别表头 + 自动映射列 → 后端读入原模板，`insert_rows()` 动态插入子目行，`_copy_row_style()` 复制样式。

### 关键 schema

### 关键 schema 注意事项

- **`ExportSubItem.bid`** 类型是 `str`（不是 `int`）——基准价编号如 `"NS-015"`、`"JD-145"` 是字符串编码
- **`TemplateExportRequest.column_mapping`** 的键是模板列索引（0-based 字符串），值是数据字段 key
- 模板导出 `mat`（主材费）= `mat_price × (1 + waste_rate/100)`（计算值），`mat_price` 是原始单价

## 版本发布 + 邮件通知

**组件**：
| 文件 | 说明 |
|------|------|
| `backend/app/api/v1/endpoints/releases.py` | 版本管理 + 邮件编排（10 个端点） |
| `backend/app/schemas/release.py` | Pydantic 模型 |
| `backend/app/services/mail_client.py` | QQ SMTP 邮件发送（smtplib + EmailMessage） |
| `backend/app/services/user_lookup.py` | Auth Admin API 分页获取用户邮箱 |
| `data/migrations/supabase_releases_migration.sql` | system_releases + email_logs + email_test_logs 建表 + RLS |

**架构**：Render（版本管理+邮件编排） → QQ SMTP（smtp.qq.com:465 SSL）
**密钥**：SMTP 授权码仅存 Render 环境变量；service_role key 仅存 Render 环境变量
**API**：
- 公开：`GET /api/v1/releases?limit=20`、`GET /api/v1/releases/{id}`
- 管理员：`/api/v1/admin/releases/*`（全部使用 `Depends(require_admin)`）
- 发布后不可修改/删除；数据库幂等基于 `email_logs(release_id,user_id)` UNIQUE

## 数据库恢复

如果 Supabase 数据丢失，按顺序执行：

```sql
-- 1. RLS 修复
DROP POLICY IF EXISTS benchmark_read_approved ON benchmark_items;
CREATE POLICY benchmark_read_auth ON benchmark_items FOR SELECT TO authenticated USING (true);

-- 2. 数据恢复（任选其一）
-- 方式 A: Table Editor → Import CSV → benchmark_items.csv
-- 方式 B: SQL Editor 执行 data/seeds/ 下所有 SQL 文件
```

`docs/benchmark_data.json` 作为前端离线备用，`data/seeds/` 包含完整 SQL 恢复脚本。

## 注意事项

- `docs/tool.html` ↔ `frontend/public/tool.html` 必须保持同步（修改时两处都要改）
- 同理 `docs/admin.html` ↔ `frontend/public/admin.html`
- `docs/benchmark_data.json` / `docs/waste_rates.json` ↔ `frontend/public/` 必须同步（Pages 只部署 `frontend/public/`，缺了会导致线上离线兜底退化为 4 条内置数据）
- DeepSeek 模型名三处同步: `backend/app/core/config.py`, `docs/tool.html`, `docs/v5.html`
- 新增 BOQ 行字段需同步改: `makeRow()`, `rowTotal()`, `renderBoq()`, `collectExportData()`
- `rowUnitPrice(r)` 依赖 `r.subs`，`r.subs` 可能为 undefined，调用方需判空
- 导出格式修改需同时验证方式一和方式二
- 敏感数据（材料价格）只存 Supabase，不入 git
- `data/seeds/` 已被 `.gitignore` 排除（含实际定价数据，不上传 GitHub）

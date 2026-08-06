# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 分支策略（永久规则）

> **默认在 `dev` 分支进行所有开发工作，禁止直接在 `main` 分支修改代码。**

- **`main`** — 稳定版 v1.2.0，生产环境，Render + Cloudflare Pages 自动部署。**只接受 merge，禁止直接提交。**
- **`dev`** — 日常开发分支。**所有代码修改、新功能、bug 修复都在此分支进行。** 稳定后 merge 到 main 上线。
- 每次开始工作前执行 `git branch` 确认当前在 `dev` 分支，如果在 `main` 则执行 `git checkout dev`。

## 项目概述

装修成本分析系统 — 装修工程人工费+材料费智能套价工具。

- **后端**: Supabase PostgreSQL + Auth + REST API + FastAPI (Render 部署)
- **前端**: React + TypeScript + Vite（Cloudflare Pages 部署）
- **生产**: https://decoration-pricing-system.pages.dev（Pages）+ https://decoration-pricing-system.onrender.com（Render）
- **版本**: V1.2.0
- **套价工具**: `docs/tool.html`（~2600行纯 HTML/CSS/JS 单页）
- **仓库**: 私有（GitHub）

## 本地开发

```bash
# 套价工具 + 管理面板（纯 HTML，无需构建）
cd docs && python3 -m http.server 8080
# → http://localhost:8080/tool.html
# → http://localhost:8080/admin.html

# FastAPI 后端（Excel 导出服务）
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000/docs

# React 前端
cd frontend && npm run dev
# → http://localhost:5173
```

localhost 环境自动免登录（tool.html 和 admin.html 均已适配）。

**后端依赖**：`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `openpyxl`, `sqlalchemy`, `psycopg2-binary`, `python-multipart`, `python-jose`, `passlib`, `bcrypt`, `httpx`

## 核心文件

| 文件 | 说明 |
|------|------|
| `docs/tool.html` | **核心套价工具** — BOQ 导入、基准价侧栏、AI 套价、Excel 导出 |
| `docs/admin.html` | 管理面板 — 用户管理 / 信息价录入 / 知识库 / 基准价浏览 |
| `docs/benchmark_data.json` | 497 条基准价完整备份（含辅材配方），localhost 离线备用 |
| `frontend/src/` | React 页面（登录、工作台、基准价查询、辅材规则等） |
| `frontend/public/tool.html` | `docs/tool.html` 的同步副本 |
| `backend/app/services/excel_export.py` | **方式一导出引擎** — openpyxl 生成 Excel（公式、折叠、自动行高） |
| `backend/app/services/template_export.py` | **方式二导出引擎** — 读入用户模板，填入数据+插入子目行 |
| `backend/app/schemas/export.py` | 导出请求模型（ExportRequest, TemplateExportRequest） |
| `backend/app/api/v1/endpoints/export.py` | 导出 API 端点（`/excel`, `/template`） |
| `data/seeds/` | 种子 SQL/JSON — 数据库恢复用 |
| `scripts/` | 数据生成脚本（Excel 解析、辅材匹配、SQL 生成） |

## 计价公式

```
综合单价 = 人工单价 + 主材费×(1+损耗率/100) + 辅材费 + 管理费 + 利润
管理费   = 人工单价 × 管理费率%
利润     = 人工单价 × 利润率%
合价     = 综合单价 × 工程量
```

## Supabase

- URL: `https://lnvtykghcpsjpwczbqsm.supabase.co`
- Anon key: `sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q`
- 前端通过 Fetch API 直连（`_get`/`_post`/`_patch`/`_del` 封装在 tool.html:536-540）

### RLS 策略

| 表 | SELECT | INSERT/UPDATE/DELETE |
|----|--------|---------------------|
| `benchmark_items` | `authenticated` 均可读 | 需 `is_admin=true` |
| `material_prices` | 公开（无 RLS） | 需 `is_admin=true` |
| `profiles` | — | 仅管理员 |

`is_admin()` 函数检查 `profiles` 表。

## 数据库当前状态（2026-07-31）

| 表 | 行数 | 备注 |
|----|------|------|
| `benchmark_items` | 497 | FIXED 432 / RATE 63 / GROUP 2，含 aux 辅材配方 |
| `material_prices` | 21 | 21 种辅材信息价（2024-01 基准价） |
| `main_material_categories` | 23 | 主材品类 |
| `main_material_catalog` | 226 | 主材目录 |
| `main_material_prices` | 226 | 主材价格 |
| `profiles` | 1 | Lee 管理员（leening222@126.com） |
| `auxiliary_rules` | 0 | 旧版 keyword 规则（V2 系统不依赖） |
| `ai_knowledge` | 0 | 已丢失 |

## Excel 导出（FastAPI 后端 + openpyxl）

两种导出方式均通过 FastAPI 后端（`localhost:8000`）生成 xlsx 文件，前端 `tool.html` 以 fetch 调用。

### 方式一：配置导出 `POST /api/v1/export/excel`

`collectExportData()` 收集 BOQ 数据 → `ExcelExporter` 生成新 sheet。

关键格式设置：
- **全部单元格**: `vertical: 'center'` + `wrapText: true`
- **行高**: 根据内容字数自动估算（`_set_row_heights`）
- **折叠**: `summaryBelow: false`，层级：分部(1)→清单(2)→子目(3)
- **公式**: 管理费=lab×rate, 利润=lab×rate, 综合单价=Σ各项, 合价=usp×qty
- **合计行**: 仅合价列 SUM，通过 `main_row_indices`（仅父行）避免子目双倍计数
- **编号列**: 仅子目行显示基准价编号（`code` 列），清单行留空
- **子目 USP**: 保留值（不含管理费/利润加成），父行 USP 为公式
- **子目初始折叠**: `hidden: true`

### 方式二：模板导出 `POST /api/v1/export/template`

前端 `handleTmplFile()` 解析模板识别表头 + `autoMatchTmplCols()` 自动映射列 → `doTemplateExport()` 以 FormData（template 文件 + JSON 数据）发送至后端 → `TemplateExcelExporter` 读入原模板，在表头下方填入数据。

- `ws.insert_rows()` 在父行下方动态插入子目行
- `_copy_row_style()` 将父行样式复制到插入行
- `_apply_styles()` / `_set_row_heights()` 补齐格式（与方式一对齐）
- `_set_outline()` 设置分组折叠（与方式一行为一致）
- 支持 `📌 包含套价子目` 勾选框（`tmplShowSubs`）

### 关键 schema 注意事项

- **`ExportSubItem.bid`** 类型是 `str`（不是 `int`）——基准价编号如 `"NS-015"`、`"JD-145"` 是字符串编码
- **`TemplateExportRequest.column_mapping`** 的键是模板列索引（0-based 字符串），值是数据字段 key
- 模板导出 `mat`（主材费）= `mat_price × (1 + waste_rate/100)`（计算值），`mat_price` 是原始单价

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

- `docs/tool.html` 和 `frontend/public/tool.html` 必须保持同步（修改时两处都要改）
- 同理 `docs/admin.html` ↔ `frontend/public/admin.html`
- 新增 BOQ 行字段需同步改 `makeRow()`、`rowTotal()`、`renderBoq()`、`collectExportData()`
- `collectExportData()` 负责收集导出数据（方式一和方式二共用）
- `rowUnitPrice(r)` 依赖 `r.subs`，`r.subs` 可能为 undefined，调用方需判空
- 敏感数据（材料价格）只存 Supabase，不入 git
- 导出格式修改需同时验证 **方式一**（配置导出）和 **方式二**（模板导出）

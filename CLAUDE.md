# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

装修成本分析系统 — 装修工程人工费+材料费智能套价工具。

- **后端**: Supabase PostgreSQL + Auth + REST API
- **前端**: React + TypeScript + Vite（Cloudflare Pages 部署）
- **套价工具**: `docs/tool.html`（~2600行纯 HTML/CSS/JS 单页）
- **仓库**: 私有（GitHub）

## 本地开发

```bash
# 套价工具 + 管理面板（纯 HTML，无需构建）
cd docs && python3 -m http.server 8080
# → http://localhost:8080/tool.html
# → http://localhost:8080/admin.html

# React 前端
cd frontend && npm run dev
# → http://localhost:5173
```

localhost 环境自动免登录（tool.html 和 admin.html 均已适配）。

## 核心文件

| 文件 | 说明 |
|------|------|
| `docs/tool.html` | **核心套价工具** — BOQ 导入、基准价侧栏、AI 套价、Excel 导出 |
| `docs/admin.html` | 管理面板 — 用户管理 / 信息价录入 / 知识库 / 基准价浏览（含辅材完整性检查） |
| `docs/index.html` | React 入口（生产构建） |
| `docs/benchmark_data.json` | 497 条基准价完整备份（含辅材配方），localhost 离线备用 |
| `frontend/src/` | React 页面（登录、工作台、基准价查询、辅材规则等） |
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

## Excel 导出配置

`doConfigExport()` (tool.html:1791)：用户勾选列 + 预设模板。

关键格式设置：
- **全部单元格**: `vertical: 'center'` + `wrapText: true`
- **标题/表头**: 水平居中
- **序号/单位列**: 水平居中
- **数字列**: 右对齐
- **行高**: 根据内容字数自动估算
- **折叠**: `summaryBelow: false`，层级：分部(1)→清单(2)→子目(3)
- **公式**: 管理费=lab×rate, 利润=lab×rate, 综合单价=Σ各项, 合价=usp×qty
- **合计行**: 末行 SUM 公式汇总
- **编号列**: 仅子目行显示基准价编号，清单行留空
- **子目初始折叠**: `hidden: true`

`doTemplateExport()` (tool.html:2046)：上传 Excel 模板，匹配列名填入数据，保留原格式。

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

- `docs/tool.html` 和 `frontend/public/tool.html` 必须保持同步（`cp`）
- 同理 `docs/admin.html` ↔ `frontend/public/admin.html`
- JS 语法检查: `node -e "new Function(js)"`（注意 localStorage 在 Node.js 不可用）
- `renderBoq()` 不递归调用自身；系数输入框 `onchange` 用 `updCoef()`/`updField()`
- 新增 BOQ 行字段需同步改 `makeRow()`、`rowTotal()`、`renderBoq()`、`exportResult()`
- DeepSeek 模型: `deepseek-v4-pro`
- 敏感数据（材料价格）只存 Supabase，不入 git

# 装修成本分析系统（V1.4.0）

装修工程人工费 + 材料费智能套价工具：BOQ 导入 → AI 套价（基准价子目匹配）→ 双计价口径（对内成本 / 对甲报价·集团基准价）→ 带公式 Excel 导出。

## 架构（实际运行）

| 层 | 技术 | 部署 |
|----|------|------|
| 静态应用（产品主体） | 纯 HTML/CSS/JS：`docs/tool.html`（电脑端 · 5200 行）、`docs/m.html`（手机版）、`docs/admin.html`（管理面板） | Cloudflare Pages（只发布 `frontend/public/`，与 `docs/` 双副本必须同步） |
| React 壳 | React + TS + Vite — 登录/工作台/审批/基准价浏览；`/pricing` 以 iframe 挂 tool.html | 同上 |
| 计算后端 | FastAPI + httpx（直调 OpenAI 兼容 LLM 端点）+ openpyxl（三种 Excel 导出） | Render |
| 数据 / 认证 | Supabase：PostgreSQL + Auth + RLS + REST + RPC；草稿/历史方案/版本公告 | Supabase 云 |

- AI 套价 API Key 由前端输入、仅本次请求透传，不落库
- 生产后端依赖仅 8 项，见 `backend/requirements.txt`
- 计价双引擎（对内成本 497 条 / 对甲报价 ZS02 集团 296 条）严格隔离，详见 [CLAUDE.md](./CLAUDE.md)

## 本地开发

```bash
# 静态应用（无需构建）
cd docs && python3 -m http.server 8080
# → http://localhost:8080/tool.html（localhost 自动免登录）

# FastAPI 后端（AI 套价 + Excel 导出）
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000/docs

# React 前端
cd frontend && npm run dev
# → http://localhost:5173
```

## 质量闸门

```bash
scripts/run_tests.sh        # 一键：双副本 6 文件 + 5 套 JS 沙箱（539 断言）+ 后端 pytest
scripts/check_dual_copy.sh  # 只查 docs/ ↔ frontend/public/ 六文件同步
```

改完任何 `docs/` 下文件都要同步到 `frontend/public/`（双副本守卫会把关）。

## 遗留栈说明（不在生产路径，待清理裁定）

以下为早期「企业版多租户」技术路线的脚手架，生产未使用、依赖也未安装，保留待单独裁定删除：

- `docker-compose.yml` — 本地 Postgres+pgvector / Redis / Celery worker 编排
- `backend/requirements/{base,dev,prod}.txt` — 含 SQLAlchemy / Celery / LangChain（生产已改用 `backend/requirements.txt`）
- `backend/app/models/`、`backend/app/db/` — SQLAlchemy 模型与会话（生产走 Supabase REST）
- `backend/app/tasks/` — Celery 任务；`backend/app/ai/engine.py` — LangChain 初始化
- `backend/app/api/v1/endpoints/` 中 8 个 deprecated 空壳端点（`router.py` 已注释挂载）
- `services/`（llm / embedding / vector-db 容器配置）、`workers/`（空目录）

## 文档

- [CLAUDE.md](./CLAUDE.md) — 开发规约与架构权威：分支策略、双计价引擎、Excel 导出、版本发布、数据库恢复
- `docs/superpowers/specs`、`docs/superpowers/plans` — 设计规格与实施计划（用户裁定记录）
- `docs/architecture-*.md` — 架构升级分析（历史留档）

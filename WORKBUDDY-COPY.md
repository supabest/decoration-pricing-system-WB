# WORKBUDDY-COPY.md

本目录是 `~/Documents/Github/decoration-pricing-system` 的**完整副本**，用于在 WorkBuddy 中开发与运行。
原项目是只读参考，**任何改动都不回写原项目**。

## 副本状态

| 项 | 值 |
|---|---|
| 来源 | `/Users/leeningchen/Documents/Github/decoration-pricing-system` |
| 复制时源状态 | 分支 `dev`，HEAD `fa95fca`，工作区干净，259 文件（不含 .git） |
| 副本 git | 完整 355 条历史，分支 `dev`，HEAD `fa95fca`，**无任何远端**（原 origin 已移除，物理上推不回原仓库） |
| 与源的一致性 | 复制后 `diff -rq --exclude=.git` 退出码 0；`scripts/check_dual_copy.sh` 4/4 通过 |
| 副本内唯一新增 | 本文件 + `.workbuddy/memory/`（WorkBuddy 项目记忆目录） |

原项目在复制前后各校验一次：`git status` 为空、HEAD `fa95fca`、内容指纹 `b827a9a9…` 一致，未发生任何写入。

## ⚠️ 数据尚未隔离

副本当前**仍连接原项目的 Supabase 云库** `lnvtykghcpsjpwczbqsm`。
在副本里执行导入脚本、RLS 迁移或改基准价，**会直接影响原项目线上数据**。

真正隔离需要（尚未执行，属独立任务）：

1. 新建独立 Supabase 项目
2. 依次执行 `data/migrations/` 下 9 个迁移（顺序见 CLAUDE.md「上线顺序」）
3. 迁入数据：`benchmark_items` 497 条、`group_benchmark_items` 296 条、`group_pricing_rules` 费率种子、`auxiliary_rules`、`material_prices`、`main_material_*`、`profiles`
4. 用新密钥重打 `backend/app/data/benchmark_snapshot.enc`
5. 替换 26 处项目引用（功能性落点：`backend/app/core/config.py`、`frontend/src/lib/supabaseClient.ts`、`frontend/functions/sb/_route.js`、`docs/{tool,m,admin,login}.html` + `frontend/public/` 对应副本）
6. 同步改写 `docs/superpowers/tests/sb_proxy_test.js` 等测试里的固定值

隔离完成前，**不要在本副本执行任何写数据的脚本**（`*--write`、迁移 SQL、`report_pricing_failure` 之外的写操作）。

## 运行

```bash
# 静态应用（无需构建）
cd docs && python3 -m http.server 8080     # localhost 自动免登录

# 后端（需自建 venv 并装 backend/requirements.txt）
cd backend && python3 -m venv venv311 && venv311/bin/pip install -r requirements.txt
venv311/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# React 前端
cd frontend && npm install && npm run dev
```

本机无 `backend/.env`（原项目也没有）。需要 AI 套价 / 快照兜底时须自备：
`LLM_API_KEY`、`SUPABASE_SERVICE_ROLE_KEY`、`BENCHMARK_SNAPSHOT_KEY`、SMTP 授权码。

## 开发必守规则（与原项目一致）

- 在 `dev` 分支开发，`main` 只接受 merge
- `docs/` ↔ `frontend/public/` 四文件必须逐字节一致（`scripts/check_dual_copy.sh`）
- 改完跑 `scripts/run_tests.sh`（双副本 + 8 套 JS 沙箱 + pytest）
- 双计价引擎严格隔离：内部 497 条（损耗率口径）/ 对甲集团 296 条（消耗量口径）
- `price === null` 才是「待询价」，`0` 是有效价

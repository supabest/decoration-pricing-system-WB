# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 分支策略（永久规则）

> **默认在 `dev` 分支进行所有开发工作，禁止直接在 `main` 分支修改代码。**

- **`main`** — 稳定版 v1.4.0，生产环境，Render + Cloudflare Pages 自动部署。**只接受 merge，禁止直接提交。**
- **`dev`** — 日常开发分支。**所有代码修改、新功能、bug 修复都在此分支进行。** 稳定后 merge 到 main 上线。
- 每次开始工作前执行 `git branch` 确认当前在 `dev` 分支，如果在 `main` 则执行 `git checkout dev`。

## 项目概述

装修成本分析系统 — 装修工程人工费+材料费智能套价工具。

- **后端**: Python 3.12, FastAPI, httpx 直调 OpenAI 兼容端点（DeepSeek / 智谱 GLM）, Supabase PostgreSQL + Auth + REST API（Render 部署；生产依赖仅 8 项，见 `backend/requirements.txt`）
- **前端**: React + TypeScript + Vite（Cloudflare Pages 部署）
- **核心工具**: `docs/tool.html`（~2600行纯 HTML/CSS/JS 单页应用）
- **生产**: https://decoration-pricing-system.pages.dev（Pages）+ https://decoration-pricing-system.onrender.com（Render）
- **版本**: V1.4.0
- **仓库**: 私有（GitHub）

## 本地开发

```bash
# 套价工具 + 管理面板（纯 HTML，无需构建）
cd docs && python3 -m http.server 8080
# → http://localhost:8080/tool.html
# → http://localhost:8080/admin.html
# → http://localhost:8080/m.html   手机版（手机真机访问把 localhost 换成本机局域网 IP，同网段即可）

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
| `docs/m.html` | **手机版套价工具**（V1.4 新增）— 五步流卡片式；与 tool.html 代码独立，只共享 groups_json 契约 + 同一套 Supabase/FastAPI；电脑端功能界面不受影响 |
| `docs/ai_knowledge_base.json` | **AI 知识库** — tips/synonyms/rules 三类规则驱动 AI 匹配决策 |
| `docs/benchmark_data.json` | 497 条基准价明文备份 — **已 .gitignore，只在本机**（加密进快照 + 不再发布到 Pages） |
| `backend/app/data/benchmark_snapshot.enc` | **基准价加密快照**（497 条 + 475 条损耗率，AES-256-GCM）— 密文进仓库，密钥 `BENCHMARK_SNAPSHOT_KEY` 只在 Render 环境变量与 `backend/.env` |
| `backend/app/services/benchmark_snapshot.py` | 快照加解密与进程内缓存；解不开/缺文件回空结构并打 `[SNAPSHOT]` |
| `scripts/encrypt_benchmark_snapshot.py` | 生成密钥 / 重打快照 / `--verify` 校验线上密钥能否解开仓库那份（用 backend venv 跑） |
| `docs/superpowers/tests/bench_fallback_test.js` | 离线兜底三级退的双端对偶沙箱（无 token 绝不请求后端快照） |
| `data/migrations/benchmark_rls_confidential_migration.sql` | **价表保密迁移**（待 Dashboard 执行）— 五张价表 SELECT 收到 `authenticated` |
| `scripts/check_dual_copy.sh` | **双副本同步守卫** — docs ↔ frontend/public 四文件 diff，不一致 exit 1 |
| `scripts/run_tests.sh` | **一键全量回归** — 双副本 + 8 套 JS 沙箱 + pytest（收尾必跑） |
| `data/migrations/ai_pricing_logs_rls_migration.sql` | **调试日志表 RLS 锁读**（2026-10-18；匿名只剩 INSERT，后端读走 service_role）|
| `backend/app/ai/engine.py` | ⚠️ **遗留死代码** — LangChain 初始化（生产依赖未装、未被任何生产端点导入）；实际 LLM 调用在 `ai_pricing_service.call_deepseek`（httpx 直调） |
| `backend/app/services/ai_pricing_service.py` | AI 套价核心服务：工程解析 → 候选匹配 → AI 推理 |
| `backend/app/services/pricing_debug_logger.py` | 调试日志收集器，`DEBUG_PRICING=true` 时写入 `ai_pricing_logs` 表 |
| `backend/app/services/similarity_checker.py` | 相似清单一致性校验 — 2-gram Jaccard + 子目差异检测 |
| `backend/app/services/excel_export.py` | 方式一导出引擎 — openpyxl 生成 Excel（公式、折叠、自动行高） |
| `backend/app/services/template_export.py` | 方式二导出引擎 — 读入用户模板，填入数据+插入子目行 |
| `scripts/import_group_benchmark.py` | **集团基准价导入** — 解析附录2 xlsx 296 条 ZS02 子目 → Supabase；内置 H 值重算审计闸门（全部偏差必须命中 `KNOWN_ANOMALIES` 8 码登记，否则 exit 1）；`--dry-run`/`--write` |
| `backend/app/services/group_summary_export.py` | **集团汇总表导出** — ZS02 明细 sheet + T02 四部分汇总 sheet，后端重算 h（与前端公式同源） |
| `docs/superpowers/tests/group_pricing_test.js` | 集团计价引擎沙箱回归（node 直跑，A-H 段 300+ 断言，含跨端黄金值钉） |
| `frontend/src/` | React 页面（登录、工作台、基准价查询、辅材规则等） |

### AI 模型配置（DeepSeek + 智谱）

- 默认模型: `deepseek-v4-pro`（配置在 `backend/app/core/config.py` 的 `LLM_MODEL`）
- 支持模型（前端 AI 面板下拉选择，`model` 字段经 `/pricing/single` 透传到 `call_deepseek`）：
  - `deepseek-v4-pro`（强，默认）/ `deepseek-v4-flash`（省·快）
  - `glm-5.3-flash`（智谱·快）— `call_deepseek` 按 model 前缀路由：`glm*` → 智谱**双端点**（主 `LLM_BASE_URL_ZHIPU` = 普通 API key 按量计费端点，备 `LLM_BASE_URL_ZHIPU_FALLBACK` = Coding Plan 套餐端点），其余 → `LLM_BASE_URL`
  - **双端点自动回退**：普通 key 只在 paas 端点有钱（主）、套餐 key 只在 coding 端点有额度（备）；遇鉴权/计费类错误（401/402/403 或 body 含 1113）立即换备端点，429 限流（1302）则同端点指数退避（2/4/8/15s）重试。⚠️ 智谱 1113 余额不足也返回 HTTP 429，判端点不匹配必须看 body 不能只看状态码
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

> 保密边界（2026-10-31 裁定）：**价表对已注册用户不需要保密，对外部绝对保密**。
> anon/publishable key 本来就写在 `config.py:36` 和前端 bundle 里公开，所以 **RLS 是唯一的门**；
> 后端读价表走 service_role（`_sb_headers()`，未配时回退 anon）。
> 下表「应为」列是 `data/migrations/benchmark_rls_confidential_migration.sql` 执行后的目标状态——**该迁移待 Dashboard 执行**。

| 表 | SELECT（现状 → 应为） | INSERT/UPDATE/DELETE |
|----|--------|---------------------|
| `benchmark_items` | `authenticated`（已是，迁移里再幂等声明一次） | 需 `is_admin=true` |
| `material_prices` | 公开（无 RLS）→ **`authenticated`** | 需 `is_admin=true` |
| `main_material_catalog` | 公开 → **`authenticated`** | 需 `is_admin=true` |
| `profiles` | — | 仅管理员 |
| `ai_pricing_logs` | 匿名/登录一律拒绝（2026-10-18 RLS 锁读） | 匿名 INSERT 放行（本机调试写入不炸）；读取走 service_role |
| `group_benchmark_items` / `group_pricing_rules` | `public`（localhost 免登录 anon 冒烟时留的口子）→ **`authenticated`** | 需 `is_admin=true` |
| `projects` | 按用户（RLS 实测正常拦截） | 按用户 |
| `pricing_failures` | 匿名可读（admin 面板直查；行内是用户清单原文，不是价，本次不动） | 匿名可写（统计入口不设身份门槛，既有裁定） |

### 数据库当前状态（2026-08-07）

| 表 | 行数 | 备注 |
|----|------|------|
| `benchmark_items` | 497 | FIXED 432 / RATE 63 / GROUP 2，含 aux 辅材配方 |
| `material_prices` | 21 | 21 种辅材信息价（2024-01 基准价） |
| `main_material_catalog` | 226 | 主材目录+价格 |
| `ai_pricing_logs` | — | 调试日志（`DEBUG_PRICING=true` 时写入）；已 RLS 锁读（`data/migrations/ai_pricing_logs_rls_migration.sql`，**待 Dashboard 执行**） |

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

### 双计价引擎（集团基准价 · 对甲报价，2026-10 新增）

`tool.html` 顶部有「对内成本 / 对甲报价（集团）」模式开关（`pricingMode`），两套公式**严格并存、互不改动**：

```
集团综合单价 h = 人工A + Σ(主材单价×消耗量Ci) + 辅材D + 机械E + 管理费F + 利润G
管理费 F = (A+E) × 17%      ← 费率写死于集团规定，取费基数 = 人工+机械（非人工单价）
利润   G = (A+E) × 12%
```

- **主材消耗量口径**：损耗已含于 Ci（如瓷砖 1.4469 m²/m²），与内部公式的 `×(1+损耗率)` 不同，勿混用
- **数据源**：Supabase `group_benchmark_items`（296 条 = A精装146+B水电106+C拆除33+D措施11，`scripts/import_group_benchmark.py --write` 导入）+ `group_pricing_rules`（费率种子：mgmt .17 / profit .12 / green .13 / baogan .03 / tax .09 / coordFee 默认 NULL）。前端懒加载进 `GROUP_RATES`，**费率禁止硬编码进 JS/Python 逻辑**
- **待询价拦截**：集团子目任一主材 `price===null` → 该行不入汇总、导出被 400 拦截（`detail.pending=[codes]`）；`price===0` 与「甲供按 0 计」合法，NULL 才拦截——**null≠0 是集团端全局判据**（coordFee 同理：NULL=未配置不静默当 0，前端标注「参数未配置」，后端导出 400）
- **T02 四部分汇总**：一 分部分项（**D 类不进**）→ 二 措施（=ΣD类合价 + 绿安费，绿安/包干基数只含分部分项行的 人工+机械）→ 三 其他（包干费 + 赶工/变更/涨幅手工费 + 精装修配合费=费率×面积；**暂列金额=0，集团规定不予计取**）→ 四 税金=(一+二+三)×9% → 五 总造价+单方造价(÷装修面积)
- **导出**：`POST /api/v1/export/group-summary`（payload 下发 raw 值、后端重算，前端 h 不被信任）；黄金值锚点：ZS02-D-003 h=4.0779、A-009 补价100 h=230.6085
- **模式隔离**：集团子目 `gtype:'group'` 挂在既有 subs 契约上（向后兼容 m.html）；group 模式下内部导出链（方式一/二、splitByTrade 对账）入口被 `groupModeBlock()` 拦截
- **AI 一键套价双口径**：`POST /api/v1/pricing/single` 的 `mode` 字段（默认 `internal`）决定候选池——`internal` 走 497 条 `benchmark_items`+班组路由+内部 prompt；`group` 走 `group_benchmark_items`（`load_group_benchmark_data` **只读 Supabase、不做本地 JSON 兜底**，降级会把内部口径的价送进对甲报价）+ `route_disciplines`（discipline 只加分不硬过滤）+ ZS02 版 prompt + 按编号校验。**AI 只选子目、绝不代填价**：返回的 `pending_mats` 只含名称，主材价仍由用户走 `updGroupMat`；集团口径下跳过相似清单一致性校验（auto_fix 的 `{...s}` 浅拷会让两行共用同一 mats 数组）与失败上报（`pricing_failures` 统计的是内部补库缺口，OTH 手工金额行也不得上报）
- 迁移：`data/migrations/group_benchmark_migration.sql` + `data/migrations/projects_fitout_fees_migration.sql`（后者补 `projects.fitout_area/overtime_fee/contract_change_fee/inflation_fee` 四列——**缺列会使草稿自动保存静默失败**，须在 Dashboard 执行）
- 源表已知异常：A-069/070 的 Excel H 公式漏算续行主材、B-100~106 手填费率隐含 15/10——引擎一律以 T01 公式（17/12）重算为准，`raw_composite` 仅留档供集团对账

**上线顺序（P1 发布硬依赖，严格按序）**：

1. `data/migrations/group_benchmark_migration.sql`（集团两表）
2. `data/migrations/projects_fitout_fees_migration.sql`（projects 四列）
3. `python scripts/import_group_benchmark.py --dry-run`（审计 0 未登记异常才可继续）
4. `python scripts/import_group_benchmark.py --write`（导入 296 条基准价 + 费率种子）
5. 前端发布（docs/tool.html / frontend 同步）

注：**前端先于迁移 1/2 发布**会使内部模式草稿静默失效（PostgREST 未知列 400：`fitout_area` 等四列与集团两表不存在），不是集团模式用户也不会报错——只有控制台里的失败请求。

### 对内成本测算（与对外报价严格分离，不进入任何导出）

```
目标成本线   = 项目合同金额 × (1 - 预估目标利润率/100)
测算直接成本 = Σ[(人工 + 主材×(1+损耗) + 辅材) × 工程量]   ← 不含管理费/利润加成
测算利润率   = (合同金额 - 测算直接成本) / 合同金额 × 100
```

- 管理费/利润率属**对外报价**范畴；**对甲合同金额（不含暂列金额，选填）与预估目标利润率属对内核算输入**——仍在报价阶段、金额未定的项目可留空合同金额；目标利润率是用户按项目全部直接成本（含未录入工具的费用项）对比合同金额的预设值。两套口径不可混淆
- 工具内"清单直接成本"仅覆盖已录入套价的费用项 ≠ 项目全部直接成本，面板文案已注明
- 存储：`projects.contract_amount`、`projects.target_profit_rate`（迁移见 `data/migrations/projects_internal_cost_migration.sql`）

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

### 集团汇总导出 `POST /api/v1/export/group-summary`（对甲报价模式专用）

`collectGroupSummaryPayload()` → `GroupSummaryExporter`：sheet1 清单明细（ZS02 A~H 分解）、sheet2 T02 汇总表（合计行用 Excel 公式）。校验：面积≤0 / 待询价 / coordFee 未配置 → 400 带结构化 detail。group 模式下方式一/二入口被前端拦截，不可误用内部口径。

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

价表明文 `docs/benchmark_data.json` / `docs/waste_rates.json` 已随保密改造 `.gitignore` 掉（只留本机），线上离线兜底改用 `backend/app/data/benchmark_snapshot.enc`（密文进仓库）；`data/seeds/` 包含完整 SQL 恢复脚本。

**刷新加密快照**（基准价有增删改之后必做，否则兜底数据停在旧版）：

```bash
backend/venv311/bin/python scripts/encrypt_benchmark_snapshot.py            # 重打 .enc（需 backend/.env 里的密钥）
backend/venv311/bin/python scripts/encrypt_benchmark_snapshot.py --verify   # 校验能否解密、只报条数不报价格
```
密钥 `BENCHMARK_SNAPSHOT_KEY` 三处必须一致：Render 环境变量、本机 `backend/.env`、生成快照时用的那把。改密钥后必须重打快照。

## 注意事项

- **收尾闸门：改完必跑 `scripts/run_tests.sh`**（双副本 4 文件 + 8 套 JS 沙箱 + pytest 一键，任一红即 exit 1）；只查双副本用 `scripts/check_dual_copy.sh`
- `docs/tool.html` ↔ `frontend/public/tool.html` 必须保持同步（修改时两处都要改）
- 同理 `docs/admin.html` ↔ `frontend/public/admin.html`，`docs/m.html` ↔ `frontend/public/m.html`；`docs/ai_knowledge_base.json` ↔ `frontend/public/`（缺了则 admin.html 未登录时知识库面板读到旧版规则集）
- **价表明文不再发布到 Pages**：`benchmark_data.json` / `waste_rates.json` 已从未部署。离线兜底走 `GET /api/v1/benchmark/snapshot`（需登录态，后端解密 `.enc` 返回），无 token 的外部拿不到——改动兜底链时保持「无 token 绝不请求后端快照」这条，`bench_fallback_test.js` 会钉住
- DeepSeek 模型名两处同步: `backend/app/core/config.py`, `docs/tool.html`（`docs/v5.html` 已删除，勿再引用）
- 新增 BOQ 行字段需同步改: `makeRow()`, `rowTotal()`, `renderBoq()`, `collectExportData()`
- `rowUnitPrice(r)` 依赖 `r.subs`，`r.subs` 可能为 undefined，调用方需判空
- 导出格式修改需同时验证方式一和方式二
- 敏感数据（材料价格/基准价）只存 Supabase；仓库里只允许 `benchmark_snapshot.enc` 这种**密文**形态存在，任何明文价表文件都不得进 git 或 `frontend/public/`
- **手机版 `docs/m.html`**：`groups_json` 行/子目字段契约权威在 tool.html 的 `makeRow()`/`addSub()`；改这两处时必须同步 m.html 的 `makeRow()`/`addSub()`/`collectExportData()`/`buildDraftPayload()`，否则跨端草稿接力丢字段
- m.html 回归：`node docs/superpowers/tests/m_logic_test.js`（手机端逻辑）+ `node docs/superpowers/tests/m_parity_test.js`（只读 tool.html 抽同名函数，双沙箱同夹具比对算价/落点/询价匹配一致性；**不修改电脑端**）
- **调试日志本机可见性**：`ai_pricing_logs` 锁读后，本机 `/pricing/debug-logs` 需在 `backend/.env` 配 `SUPABASE_SERVICE_ROLE_KEY`（可选）；未配时写入不受影响、读取为空——这是预期行为不是故障
- `data/seeds/` 已被 `.gitignore` 排除（含实际定价数据，不上传 GitHub）

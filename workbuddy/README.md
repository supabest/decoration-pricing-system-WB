# WorkBuddy 平台自动套价 · 最终架构实现

本目录是「在 WorkBuddy 会话内完成自动套价 / 报价 / 成本分析」的实现，按 2026-11-15 定死的六层架构建设：**基准价只在用户 Supabase 云端唯一一份；项目公共授权一次、全体成员共用；技能为项目 Skill；产物存项目资产**。

**这不是网页工具**：不需要网页前端，不需要 Render / FastAPI 运算后端，不改动 Pages 部署。仓库原有的 FastAPI + React 网页应用与本目录无依赖关系。

> 架构唯一基线：[`docs/系统设计-最终架构.md`](docs/系统设计-最终架构.md)；管理员配置：[`docs/Supabase平台接入说明.md`](docs/Supabase平台接入说明.md)。

## 设计要点

- **确定性脚本负责算价**：候选召回、三费计价、导出、成本分析全部由 `scripts/*.py` 完成，模型只判断「该套哪个子目」。
- **模型不接触价格**：`prepare` 产出的候选 JSON 只含编号 / 名称 / 规格 / 单位，没有任何价格字段。
- **价表云端在线拉取**：`datasource.py` 经项目公共授权读 Supabase REST，价表只在进程内存、不落盘；云端失败明确报错，不静默用旧价。
- **主链三段式**：`prepare`（候选）→ 模型写 `decisions.json` → `apply`（出报价表）；另有 `aux` / `kb` / `check` / `analyze` 等旁路能力。
- **数据不随包走**：代码、测试、文档、DDL 入库；价表、密钥、报价产物一律不入库，产物只写项目资产。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 项目 Skill 定义、运行位置、调用方式、口径与保密红线 |
| `scripts/` | 13 个脚本：云端取数 / 快照兜底、召回、计价、清单解析、单表与拆表导出、辅材规则与辅材清单、备注分级、知识库脱敏、一致性校验、CLI |
| `tests/` | 21 个测试模块 + `conftest.py`，覆盖取数层 / 快照 / 解析 / 召回 / 计价 / 多子目 / 覆盖参数 / 辅材规则 / 导出列 / 拆表 / 备注 / 辅材清单 / 知识库 / 一致性 / CLI 冒烟 / 端到端 |
| `docs/` | **系统设计-最终架构**（唯一基线）、Supabase 平台接入说明、规格与实施计划、与远端功能对齐规格、同事使用说明、P0 验收报告 |
| `sql/` | `wb_supabase_setup.sql`（补 3 张表 + RLS）、`wb_readonly_access.sql`（专用只读账号白名单 + B 档策略重建） |
| `.env.example` | 变量名模板（**不含任何真实值**；主路径由平台公共授权注入） |

当前 `workbuddy/` 共 **45 个文件**（3 根 + docs 6 + scripts 13 + sql 2 + tests 21），全部为代码 / 文档 / 测试 / DDL，**不含任何价表数据**。

## 🔴 保密边界（务必遵守）

企业基准价与集团基准价属机密。以下内容**刻意不入库**，`.gitignore` 已作对应排除：

| 不入库项 | 原因 |
|---|---|
| Supabase 价表数据 | 只在用户 Supabase 云端；快照、主材价、辅材规则一律不导出、不复制、不入库 |
| 公共授权凭据 / JWT / 口令 | 由平台云端代持，不给 AI、不写文件、不进仓库、不贴对话 |
| `.env`（`BENCHMARK_SNAPSHOT_KEY`） | 离线兜底解密密钥，泄露即等于交出全量价表 |
| `data/benchmark_snapshot.enc` | 加密后的全量价表（仅可选离线兜底）。仓库 `backend/app/data/benchmark_snapshot.enc` 是旧网页应用的线上兜底，本目录不再复制一份 |
| `*.xlsx` 报价表 / 清单 | 含真实综合单价与合价明细，属机密产物；只写**项目资产**，`gitignore` 已全局忽略 |
| `work/candidates.json`、`work/decisions.json` | 运行产物，随具体项目变化 |
| `.venv/`、`.pytest_cache/` | 本地环境 |

> 技能走**项目 Skill + 项目资产**分发，同事不必成为 GitHub collaborator，`main` 历史明文价表不会因加人而外泄；该历史遗留仍在，若日后确需邀请 collaborator，先清 `main`。

## 在新环境准备（首次）

### 主路径：项目公共授权（成员零配置）

| 步 | 谁做 | 动作 |
|---|---|---|
| 1 | 管理员（Supabase） | Dashboard 建**专用只读账号**（普通 authenticated，非 service_role）；SQL Editor 执行 `sql/wb_supabase_setup.sql` 补 3 张表；需要时按 `sql/wb_readonly_access.sql` 收紧策略 |
| 2 | 管理员（Supabase） | 一次性 `cli.py sync-seeds` 把损耗率 / 辅材数据补进云端，用完立即清除管理员令牌 |
| 3 | 管理员（WorkBuddy） | 项目详情 → 项目配置 → 连接器 → 把 `supabase` 配成**公共授权**，用专用账号授权一次 |
| 4 | 平台注入 | `WB_PRICING_SOURCE=supabase` 等变量由运行环境注入，成员不接触任何值；清单见 `.env.example`（只列变量名） |
| 5 | 验证 | `python scripts/cli.py probe` → 全表 `ok` 且行数非零 |
| 6 | 分发 | 项目配置 → 技能，把本目录配成**项目 Skill**；右上角「邀请」拉成员，无需 GitHub collaborator |

架构细节与 A / B 档 RLS 触发条件见 `docs/系统设计-最终架构.md`；逐步操作见 `docs/Supabase平台接入说明.md`。

### 可选：离线兜底（仅本机调试 / 断网演练）

代码可自由 clone；离线兜底所需密文与密钥须由有权限者自备，且**不随项目 Skill 分发**：

```bash
cd workbuddy
python3 -m venv .venv
.venv/bin/pip install openpyxl cryptography pytest

# 自备 BENCHMARK_SNAPSHOT_KEY 与 data/benchmark_snapshot.enc，
# 或用 BENCHMARK_SNAPSHOT_PATH 指向仓库外的密文；均被 .gitignore 忽略
# 重建密文：.venv/bin/python scripts/build_snapshot.py
#          可用 DECORATION_PRICING_REPO 指定含 data/seeds 的仓库根目录
```

`WB_PRICING_SOURCE` 不设时默认 `snapshot`；**正式使用必须设为 `supabase`**。

## 工作流

```bash
cd workbuddy

# 1) 出候选（脚本，零 token，结果不含价格）
.venv/bin/python scripts/cli.py prepare <清单.xlsx> -o work/candidates.json

# 1b) 可选：顺带写出脱敏知识库提示块，candidates.json 结构不变
.venv/bin/python scripts/cli.py prepare <清单.xlsx> -o work/candidates.json \
  --knowledge-out work/kb_prompt.txt

# 2) 由模型读候选，为每行判定子目，写 work/decisions.json
#    格式见 SKILL.md：{"1": {"code": "NS-017", "team": "泥水班组", "confidence": 92}}

# 3) 出报价表（--preset: client / internal / labor）
.venv/bin/python scripts/cli.py apply work/candidates.json \
  -o 结果.xlsx --decisions work/decisions.json \
  --overrides work/overrides.json --preset client

# 3b) 按分部分 sheet（S1：每个分部独立表头/合计，末尾追加「汇总」）
.venv/bin/python scripts/cli.py apply work/candidates.json \
  -o 分部分项.xlsx --decisions work/decisions.json --split

# 4) 辅材费用清单（P1，与 apply 共用 candidates / decisions）
.venv/bin/python scripts/cli.py aux work/candidates.json \
  -o 辅材清单.xlsx --decisions work/decisions.json \
  --project-name 项目名 --contract-amount 0 --target-profit-rate 0

# 5) 知识库脱敏提示块（S2，默认 stdout 零落盘）
.venv/bin/python scripts/cli.py kb
.venv/bin/python scripts/cli.py kb -o work/kb_prompt.txt

# 6) 相似清单一致性校验（S2，只产出 JSON 报告，不改写输入）
.venv/bin/python scripts/cli.py check work/candidates.json \
  --decisions work/decisions.json -o work/consistency.json \
  --group-by section --threshold 0.90

# 云端只读体检（只报表状态 / 行数 / 字段名，不输出价格）
.venv/bin/python scripts/cli.py probe

# 统计与回归
.venv/bin/python scripts/cli.py stats
.venv/bin/python -m pytest tests/ -q --basetemp=<工作区内临时目录>
```

正式运行前由平台注入 `WB_PRICING_SOURCE=supabase`、`WB_SUPABASE_URL`、`WB_SUPABASE_ANON_KEY`、`WB_SUPABASE_TOKEN`；变量名清单见 `.env.example`，**值不写入任何文件**。

`team` 必填：`internal_code` 在不同班组间存在重复（如 `YQ-01`）。

计价口径：`综合单价 = 人工 + 主材×(1+损耗率/100) + 辅材`，`合价 = 综合单价 × 工程量`。对内**不计**管理费与利润；集团 296 条对甲报价（17% / 12%）属二期，不在本目录范围。

## P0 验收状态

- 回归 `103 / 103` 通过。
- 真实清单 10 / 10 行的单价构成与合价，与远端口径逐行对账误差为 0。
- 导出按远端 `EXP_COLS` 16 列对齐，另加 1 列「套用子目」；`client / internal / labor` 三套预设分别为完整 17 列、对甲 12 列、劳务 10 列，含合计行。
- 详见 `docs/P0验收报告.md`。

> 上述数字均为各阶段**当时口径**；当前全量回归为 **198 / 198 通过**（含云端取数层 14 项契约测试）。

### S1 阶段成果（2026-11-07，分阶段交付第 1 期）

- `apply --split`：按源工作表（分部）分 sheet，sheet 内按章节插标题行，每个分部独立表头与合计行，末尾「汇总」列各分部行数与合价；`--no-summary` 可关闭汇总。口径对齐 `backend/app/services/excel_export.py` 的 `_generate_split()`。
- 备注分级：`未套价：无候选子目` / `未套价：待判定子目` / `子目缺失` / `部分子目缺失(n/m)` / `低置信度`，决策里显式写的备注优先。口径对齐远端 `buildSplitExport()` 的 reason。
- 回归 `126 passed + 15 skipped`；拆表形态与单表形态的合计逐次对账一致。

### S2 阶段成果（2026-11-07，分阶段交付第 2 期 · 纯本地改动，未提交未 push）

本阶段只做「不依赖用户提供材料」的两项，避免空等样例：

- **知识库脱敏注入**（`scripts/knowledge.py` + `cli.py kb`）：读取仓库 `docs/ai_knowledge_base.json` 43 条（tips 4 / synonyms 15 / rules 24），按后端 `build_system_prompt()` 三桶口径渲染；源库 7 条内嵌真实金额的规则人工改写为纯工序文本，`assert_no_pricing()` 做 fail-closed 守卫。`prepare --knowledge-out` 可顺带产出同一份提示块，且不改变 `candidates.json` 结构。
- **相似清单一致性校验**（`scripts/similarity.py` + `cli.py check`）：2-gram Jaccard、四字段加权 0.20 / 0.50 / 0.20 / 0.10、Union-Find 相似组、severity 三级 + `auto_fix` 建议，逐字对齐 `backend/app/services/similarity_checker.py`；支持 `--group-by sheet|section` 收窄比较域。只出 JSON 报告，不自动补全、不改写 `decisions`、不上报、不写任何价格。
- **口径复核**：`scripts/retrieve.py` 与后端 `CRAFT_KEYWORDS` 各 23 条，逐值与顺序完全一致，无差异；S2 未改动 `retrieve.py`，避免破坏与后端的逐字对齐。
- **回归** `169 passed + 15 skipped`（新增 43 项测试：`test_knowledge.py` / `test_similarity.py` / `test_cli_check.py`）。真实源库端到端验证：提示块 43 条 / 脱敏 7 条 / 零定价痕迹；`check` 分级正确、跨域不连边、报告无金额。
- 源码 `docs/ai_knowledge_base.json`、`backend/app/services/ai_pricing_service.py`、`similarity_checker.py`、`retrieve.py` 均**未改动**。

### 阶段路线（架构已定稿，见 `docs/系统设计-最终架构.md` §12）

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 取数层与纠偏 | `datasource.py`、`probe` / `sync-seeds`、补表 SQL、系统设计、技能与文档定位纠偏 | ✅ 已落地 |
| 1 平台配置 | 专用只读账号 → 补库 → **项目公共授权** → 云端 `probe` 验证直连 | ⏳ 管理员侧动作，脚本与 SQL 已备 |
| 2 三费补全 | 主材三表接入、「子目 ↔ 主材」映射、缺价显式标注 | ⏳ 规格已定，待实现 |
| 3 成本分析与资产化 | `analysis.py` + `cli.py analyze` + `sink` 抽象 + 产物写项目资产 | ⏳ 规格已定，待实现 |
| 4 项目 Skill 与多人验收 | 配项目 Skill、邀请成员、第二位成员跑同一清单结果一致 | ⏳ 待平台侧动作 |

**已决策结论（不需要再确认）**

- 两层架构：WorkBuddy 项目 + Supabase；**不用 Render 后端、不做网页前端**。
- `/sb` 反代只是临时数据通道：云端任务 `probe` 直连成功即去掉该依赖。
- RLS 默认 A 档（不改线上策略）；旧网页确认停用后执行 `wb_readonly_access.sql` B 档。
- `main` 不重写历史；项目 Skill 分发使 GitHub collaborator 非必需。
- 集团 296 条 / 管理费 17% / 利润 12% 属二期，对内不加。
- 主材价未接入前必须标注「主材价待补」，**禁止静默按 0 出表**。

**仍需用户提供材料的旁路**：供应商报价导入（报价表样例）、模板导出（公司模板样例）。

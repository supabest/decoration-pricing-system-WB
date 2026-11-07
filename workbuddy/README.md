# WorkBuddy 会话式套价应用 · P0 → S2 阶段成果

本目录是「在 WorkBuddy 会话内完成自动套价 / 报价 / 输出报表」的实现，与仓库原有的 FastAPI + React 网页应用**并行、互不依赖**：不启动后端、不连接 Supabase、不改动 Pages 部署。

## 设计要点

- **确定性脚本负责算价**：候选召回、计价、Excel 导出全部由 `scripts/*.py` 完成，模型只判断「该套哪个子目」。
- **模型不接触价格**：`prepare` 产出的候选 JSON 只含编号 / 名称 / 规格 / 单位，没有任何价格字段。
- **主链三段式文件进文件出**：`prepare`（候选）→ 模型写 `decisions.json` → `apply`（出报价表）；另有 `aux` 辅材清单、`kb` 知识库提示块、`check` 一致性校验三个可选旁路命令，不改变主链产物。
- **数据不随包走**：代码与测试入库，价表数据、密钥、报价结果一律不入库。详见下节。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | WorkBuddy 技能定义、调用方式、决策格式与口径说明 |
| `scripts/` | 12 个脚本：快照 / 重建、召回、计价、清单解析、单表与拆表导出、辅材规则与辅材清单、备注分级、知识库脱敏、一致性校验、CLI |
| `tests/` | 19 个测试模块 + `conftest.py`，覆盖快照 / 解析 / 召回 / 计价 / 多子目 / 覆盖参数 / 辅材规则 / 导出列 / 拆表 / 备注 / 辅材清单 / 知识库 / 一致性 / CLI 冒烟 / 端到端 |
| `docs/` | 规格与实施计划、与远端功能对齐规格、同事使用说明、P0 验收报告 |
| `.env.example` | 密钥模板（**不含真实密钥**） |

## 🔴 保密边界（务必遵守）

企业基准价与集团基准价属机密。以下内容**刻意不入库**，`.gitignore` 已作对应排除：

| 不入库项 | 原因 |
|---|---|
| `.env`（`BENCHMARK_SNAPSHOT_KEY`） | 解密密钥，泄露即等于交出全量价表 |
| `data/benchmark_snapshot.enc` | 加密后的全量价表。仓库 `backend/app/data/benchmark_snapshot.enc` 是网页应用的线上兜底，本目录不再复制一份 |
| `*.xlsx` 报价表 / 清单 | 含真实综合单价与合价明细，且 `.gitignore` 已全局忽略 |
| `work/candidates.json`、`work/decisions.json` | 运行产物，随具体项目变化 |
| `.venv/`、`.pytest_cache/` | 本地环境 |

> 邀请 GitHub collaborator 等同于交出仓库全部内容。邀请前请先确认 `main` 分支及 git 历史中的明文价表已清理。

## 在新环境准备数据（首次）

代码可自由 clone，数据须由有权限者单独提供：

```bash
cd workbuddy
python3 -m venv .venv
.venv/bin/pip install openpyxl cryptography pytest

cp .env.example .env
# 编辑 .env，填入 BENCHMARK_SNAPSHOT_KEY（32 字节 base64）；chmod 600 .env
# 将有权限的加密快照放到 data/benchmark_snapshot.enc
# 该路径与 .env 均已被 .gitignore 忽略，不会被提交
```

需要重建含辅材信息价与辅材清单项的快照时，另需仓库 `data/seeds/` 下两份种子数据（同样不在 git 中），然后：

```bash
cd workbuddy
.venv/bin/python scripts/build_snapshot.py
# 可用 DECORATION_PRICING_REPO 指定含 data/seeds 的仓库根目录
```

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

# 统计与回归
.venv/bin/python scripts/cli.py stats
.venv/bin/python -m pytest tests/ -q
```

`team` 必填：`internal_code` 在不同班组间存在重复（如 `YQ-01`）。

计价口径：`综合单价 = 人工 + 主材×(1+损耗率/100) + 辅材`，`合价 = 综合单价 × 工程量`。对内**不计**管理费与利润；集团 296 条对甲报价（17% / 12%）属二期，不在本目录范围。

## P0 验收状态

- 回归 `103 / 103` 通过。
- 真实清单 10 / 10 行的单价构成与合价，与远端口径逐行对账误差为 0。
- 导出按远端 `EXP_COLS` 16 列对齐，另加 1 列「套用子目」；`client / internal / labor` 三套预设分别为完整 17 列、对甲 12 列、劳务 10 列，含合计行。
- 详见 `docs/P0验收报告.md`。

> 上述数字均为各阶段**当时口径**；当前全量回归见下方 S2 段落：`169 passed + 15 skipped`。

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

### 未闭合 / 后续

- 主材价当前为 0：能力已打通，缺真实价目或供应商报价导入。
- 尚无线上导出的清单报价表，未做字节级 / 逐行线上对比。
- 已交付：拆表与备注分级（`apply --split`）、辅材清单导出（`cli.py aux`）、知识库脱敏注入（`cli.py kb`）、相似清单一致性校验（`cli.py check`）。
- 待办（**需用户提供材料**才开工）：供应商报价导入（需报价表样例）、模板导出（需公司模板样例）。
- 后续阶段：对内成本面板、Excel 公式与折叠层级（P2）；集团 296 条对甲报价（二期）。
- 上线前门禁：正式生产快照与密钥、Supabase 数据隔离、git 历史明文价表清理。

# WorkBuddy 会话式套价应用 · P0 阶段成果

本目录是「在 WorkBuddy 会话内完成自动套价 / 报价 / 输出报表」的 P0 实现，与仓库原有的 FastAPI + React 网页应用**并行、互不依赖**：不启动后端、不连接 Supabase、不改动 Pages 部署。

## 设计要点

- **确定性脚本负责算价**：候选召回、计价、Excel 导出全部由 `scripts/*.py` 完成，模型只判断「该套哪个子目」。
- **模型不接触价格**：`prepare` 产出的候选 JSON 只含编号 / 名称 / 规格 / 单位，没有任何价格字段。
- **三段式文件进文件出**：`prepare`（候选）→ 模型写 `decisions.json` → `apply`（出报价表）。
- **数据不随包走**：代码与测试入库，价表数据、密钥、报价结果一律不入库。详见下节。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | WorkBuddy 技能定义、调用方式、决策格式与口径说明 |
| `scripts/` | 8 个脚本：快照、召回、计价、清单解析、导出、辅助规则、CLI、快照重建 |
| `tests/` | 12 个测试模块 + `conftest.py`，覆盖快照 / 解析 / 召回 / 计价 / 多子目 / 覆盖参数 / 辅材规则 / 导出列 / 端到端 |
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

# 2) 由模型读候选，为每行判定子目，写 work/decisions.json
#    格式见 SKILL.md：{"1": {"code": "NS-017", "team": "泥水班组", "confidence": 92}}

# 3) 出报价表（--preset: client / internal / labor）
.venv/bin/python scripts/cli.py apply work/candidates.json \
  -o 结果.xlsx --decisions work/decisions.json \
  --overrides work/overrides.json --preset client

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

### 未闭合 / 后续

- 主材价当前为 0：能力已打通，缺真实价目或供应商报价导入。
- 尚无线上导出的清单报价表，未做字节级 / 逐行线上对比。
- P1 待办：供应商报价导入、拆表与备注、模板导出、辅材清单导出、知识库、一致性校验。

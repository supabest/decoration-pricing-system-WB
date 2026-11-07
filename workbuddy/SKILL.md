---
name: decoration-pricing
display_name: "装修套价"
display_name_en: "Decoration Pricing"
version: 1.0.0
description: 装修工程量清单套价与报价。当用户提供 BOQ 清单（Excel/CSV）、要求「套价 / 套定额 / 匹配基准价 / 出报价表 / 算综合单价 / 工程量清单报价」时使用。本地离线运行，基准价来自加密快照，不依赖任何外部 API Key。
description_zh: 装修工程量清单套价与报价。读取 Excel/CSV 清单，按 497 条企业基准价匹配子目，计算人工+主材+辅材综合单价，导出带合价的报价表。本地离线运行，无需外部 API Key。适用于「套价 / 套子目 / 匹配基准价 / 工程量清单报价 / 算综合单价」。
description_en: Decoration BOQ pricing. Read an Excel/CSV bill of quantities, match each line to the 497-item internal benchmark price list, compute comprehensive unit price (labour + main material + auxiliary material) and export a priced quotation workbook. Runs fully offline from an encrypted local snapshot with no external API key.
agent_created: true
---

# 装修套价（内部 497 条口径）

## 什么时候用

- 用户丢来一份工程量清单，要「套价 / 套子目 / 匹配基准价」
- 要把清单转成带综合单价与合价的报价表
- 要核对某条清单应该套哪个子目

不适用：集团 296 条对甲报价（管理费 17%、利润 12%，口径不同，属二期）。

## 怎么被调用

用户可以说「帮我把这份清单套价」并给出文件路径，也可显式输入 `/decoration-pricing`。
以下是本文件里的命令约定：**均在技能根目录执行**

```bash
cd ~/.workbuddy/skills/decoration-pricing
```

（`scripts/*.py` 自身按 `__file__` 定位数据，换目录也能跑，但相对路径的 `.venv/bin/python` 与 `work/` 需要固定 cwd。）

## 工作流（三段式，文件进文件出）

### 第 1 段 · 出候选（脚本，零 token）

```bash
.venv/bin/python scripts/cli.py prepare <清单.xlsx> -o work/candidates.json
```

产出每行 top-40 候选。**候选里只有编号/名称/规格/单位，没有任何价格** —— 这是保密设计，判断时不需要看到定价。

### 第 2 段 · 判定子目（模型）

读 `work/candidates.json`，为每行挑一个子目，写入 `work/decisions.json`：

```json
{
  "1": {"code": "NS-017", "team": "泥水班组", "confidence": 92, "remark": ""},
  "2": {"subs": [
    {"code": "YQ-025", "team": "木工班组", "coef": 1.0, "conv": 1.0},
    {"code": "YQ-011", "team": "木工班组", "coef": 0.5, "conv": 1.0}
  ], "confidence": 88}
}
```

一行可挂多个子目（`subs`），每个子目可自带 `coef / conv / mat_price / waste_rate`。
**子目级参数优先于行级 `--overrides`**（远端口径：行级价只是暂存区）。

判定要点：
- `code` 必须**原样照抄**候选里的值（编号跨班组重复，必须同时给 `team`）
- 名称不同但工艺/部位/材料相同 → 可套；只是"看起来像"→ 不要套
- 拿不准的行**不写**，交给 `apply` 标「未匹配」，由人复核
- `confidence` < 60 的行，视为未匹配

### 第 3 段 · 计价导出（脚本）

```bash
.venv/bin/python scripts/cli.py apply work/candidates.json -o 结果.xlsx \
  --decisions work/decisions.json \
  --overrides work/overrides.json \
  --preset client
```

可选参数：

| 参数 | 作用 |
|---|---|
| `--overrides` | 按行号给计价参数，格式 `{"1": {"mat_price": 100, "waste_rate": 5, "coef": 1.0, "conv": 1.0}}`；不传 `waste_rate` 时按编号从损耗率表自动带出 |
| `--preset` | 导出列预设：`client` 对甲 / `internal` 对内 / `labor` 劳务 |
| `--columns` | 精确指定列 key，逗号分隔，优先级高于 `--preset` |
| `--auto` | 无决策时取候选第一名（仅作基线，不要用于正式报价） |
| `--split` | 按源工作表（分部）分 sheet，内部按章节插标题行，末尾追加「汇总」sheet（S1） |
| `--no-summary` | `--split` 时不生成末尾「汇总」sheet |

产出报价表：**远端 16 列 + 1 列「套用子目」扩展**，末行为合计。16 列为序号/编号/项目名称/项目特征/单位/工程量/人工单价/主材单价/主材费/主材损耗率/辅材费/管理费/利润/综合单价/合价/备注。内部口径管理费与利润恒为 0。

**备注自动生成（S1）**：未套价分「无候选子目」与「待判定子目」；决策给了编号但快照查不到标「子目缺失」；多子目只部分命中给 `n/m`；`confidence < 60` 标「低置信度，建议复核」。决策里显式写的 `remark` 优先，不被覆盖。判定子目时拿不准的行**不写**，让 `apply` 自动标注原因供人复核。

### 第 4 段 · 辅材费用清单（P1，可选）

```bash
.venv/bin/python scripts/cli.py aux work/candidates.json -o 辅材清单.xlsx \
  --decisions work/decisions.json --project-name 项目名 \
  --contract-amount 0 --target-profit-rate 0
```

与 `apply` 共用 `candidates / decisions / --auto`，但只走辅材配方引擎，不计算人工、主材与综合单价。按工种分 sheet：品种行按合价降序、固定辅材费包干行置尾；未套子目单列供人工补费；末尾「辅材汇总」含材料费 / 固定费 / 合计，`--contract-amount > 0` 时追加「占总成本比例」。远端口径见 `docs/tool.html` 的 `buildAuxExport()` 与 `backend/app/services/aux_export.py`。

## 计价口径（不得改动）

```
人工     = Σ(子目单价 × coef × conv)
主材     = Σ(子目主材价 × (1 + 损耗率/100) × coef × conv)
综合单价 = 人工 + 主材 + 辅材
合价     = 综合单价 × 工程量
```

**内部口径不含管理费与利润。** 管理费 17% / 利润 12% 是集团 296 条对甲报价的算法，不要套到这里。

## 数据与密钥

| 项 | 位置 |
|---|---|
| 基准价密文 | `data/benchmark_snapshot.enc`：497 基准价 + 475 损耗率 + 21 辅材信息价 + 497 辅材清单项 |
| 密钥 | `.env` 的 `BENCHMARK_SNAPSHOT_KEY`，或同名环境变量 |
| 重建快照 | `.venv/bin/python scripts/build_snapshot.py`（从仓库 `data/seeds/` 只读取数） |
| 校验 | `.venv/bin/python scripts/cli.py stats` |

密文可随 skill 分发；密钥不随包走。无密钥时 `stats` 会返回 0 条。
**集团 296 条不在快照内**（二期），重建脚本也不会纳入。

## 保密红线

- 不把基准价明细写进任何可分发文档、对话回复或导出文件之外的地方
- 只有 `apply` / `aux` 阶段才从快照读价格；`prepare` 的候选 JSON 里绝不能出现 `unit_price` / `price` 字段
- 汇报结果时只给汇总金额与匹配率，不逐条罗列定价

## 已知限制

- 清单格式：当前适配「多级表头 + 纵向合并」与「单行表头」两类；其他格式需先看结构再接
- **表头可能折行**（如 `计量\n单位`），列名匹配已做空白归一化
- 一条清单行可挂多个子目，但**每个子目只套一个基准价编号**（不自动拆面层/基层）
- 主材价默认 0，需用 `--overrides` 或子目自带 `mat_price` 提供；辅材已实现 FIXED / RATE / GROUP 三型
- 编号格式差异（`NS-01` vs `NS-1`）不做模糊匹配，必须精确
- 模板导出、供应商报价导入属 P1，尚未实现（需用户提供模板/报价表样例）；拆表与备注分级（`apply --split`）、辅材清单导出（`cli.py aux`）已实现
- 召回只做文本相似度，**尺寸/厚度类判断留给模型**（如「100*100 线槽」需按宽+高=200mm 选档）
- 源清单本身的错误（如名称写「墙布硬包」而特征写成灯槽）无法自动识别，需人工复核

## 测试

```bash
.venv/bin/python -m pytest tests/ -q     # 126 passed + 15 skipped
```

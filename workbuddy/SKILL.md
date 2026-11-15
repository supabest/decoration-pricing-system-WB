---
name: decoration-pricing
display_name: "装修套价"
display_name_en: "Decoration Pricing"
version: 1.0.0
description: 装修工程量清单套价、报价与成本分析。当用户提供 BOQ 清单（Excel/CSV）、要求「套价 / 套定额 / 匹配基准价 / 出报价表 / 算综合单价 / 成本分析」时使用。本项目为 WorkBuddy 多人协作项目：基准价只存于 Supabase 云端，经项目公共授权在线拉取，成员无需数据库账号，产物存项目资产。
description_zh: 装修工程量清单套价与报价。读取 Excel/CSV 清单，按企业基准价匹配子目，计算人工+主材+辅材综合单价，导出报价表并做成本分析。数据源是用户 Supabase 账号下的云端价表（项目公共授权一次，全项目共用），价表只在进程内存、不落盘；离线加密快照仅为可选兜底。适用于「套价 / 套子目 / 匹配基准价 / 工程量清单报价 / 算综合单价 / 成本分析」。
description_en: Decoration BOQ pricing for a multi-member WorkBuddy project. Reads an Excel/CSV bill of quantities, matches items to the internal benchmark price list, computes comprehensive unit price (labour + main material + auxiliary material), exports a quotation and performs cost analysis. Prices live in the user's Supabase project and are fetched at runtime via one project-level shared authorization; members need no database account and price data never touches disk. An encrypted local snapshot is only an optional fallback.
agent_created: true
---

# 装修套价（内部 497 条口径）

## 什么时候用

- 用户丢来一份工程量清单，要「套价 / 套子目 / 匹配基准价」
- 要把清单转成带综合单价与合价的报价表
- 要核对某条清单应该套哪个子目

不适用：集团 296 条对甲报价（管理费 17%、利润 12%，口径不同，属二期）。

## 运行位置与数据源

本技能是 **WorkBuddy 项目 Skill**（项目配置 → 技能，云端统一管理，双端可用），不是个人本地技能。项目成员共用同一份代码与同一份云端价表。

| 项 | 落点 |
|---|---|
| 价表 / 主材 / 辅材规则 | 用户 Supabase 账号，云端唯一一份 |
| 身份 | Supabase 专用只读账号（authenticated，仅价表表 SELECT，非 service_role） |
| 授权 | 项目配置里**一次公共授权**，凭据由平台云端代持；不落本地、不进对话 / 仓库 |
| 同事 | 只需是项目成员，不需要 Supabase 账号，看不到任何凭据 |
| 清单 / 报价 / 成本分析产物 | **项目资产**（云端 5GB，成员共享） |

架构唯一基线见 `docs/系统设计-最终架构.md`；管理员配置步骤见 `docs/Supabase平台接入说明.md` 与 `sql/wb_readonly_access.sql`。

## 怎么被调用

用户可以说「帮我把这份清单套价」并给出文件路径，也可显式输入 `/decoration-pricing`。
以下命令在技能根目录执行（项目 Skill 展开后的目录，或 clone 后的 `workbuddy/`）：

```bash
cd <技能根目录>
```

`scripts/*.py` 自身按 `__file__` 定位代码；价表由 `datasource.py` 在线拉取，不依赖任何本地数据文件。相对路径的 `.venv/bin/python` 与 `work/` 需要固定 cwd。

**主路径必须设置 `WB_PRICING_SOURCE=supabase`**；不设时沿用 `snapshot`（离线兜底），仅用于调试。云端取数失败会明确报错，不会静默用旧价。

## 工作流（主链三段 + 可选能力，文件进文件出）

主链是 `prepare → 模型判定 → apply` 三段；`aux` / `kb` / `check` 是按需叠加的旁路能力，不改变主链产物。

### 第 1 段 · 出候选（脚本，零 token）

```bash
.venv/bin/python scripts/cli.py prepare <清单.xlsx> -o work/candidates.json
```

产出每行 top-40 候选。**候选里只有编号/名称/规格/单位，没有任何价格** —— 这是保密设计，判断时不需要看到定价。

可选 `--knowledge-out work/kb_prompt.txt`：顺带写出一份**脱敏知识库提示块**（43 条，含价规则已改写为纯工序文本），供第 2 段判定时参考。不传时 `candidates.json` 结构完全不变；第 5 段也可用 `kb` 命令独立产出同一份提示块。

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

### 第 5 段 · 知识库脱敏提示块（S2，可选）

```bash
.venv/bin/python scripts/cli.py kb                          # 默认只打印到 stdout，不落盘
.venv/bin/python scripts/cli.py kb -o work/kb_prompt.txt   # 写出到文件
.venv/bin/python scripts/cli.py kb --kb /path/to/kb.json -o work/kb_prompt.txt
```

读取仓库 `docs/ai_knowledge_base.json`（43 条：`tips` 4 / `synonyms` 15 / `rules` 24），按后端 `build_system_prompt()` 的三桶口径渲染成提示块。**源库 7 条内嵌真实金额的规则已人工改写为纯工序文本**；输出前有 fail-closed 守卫，一旦出现金额 / 单价痕迹直接报错，绝不静默放行。提示块不含任何价格，可安全进入模型上下文。

### 第 6 段 · 相似清单一致性校验（S2，可选）

```bash
.venv/bin/python scripts/cli.py check work/candidates.json \
  --decisions work/decisions.json -o work/consistency.json \
  --group-by section --threshold 0.90 --default-confidence 100
```

对齐后端 `similarity_checker.py`：2-gram Jaccard、四字段加权（名称 0.20 / 规格 0.50 / 工程语义 0.20 / 单位 0.10）、Union-Find 相似组、severity 三级与 `auto_fix` 建议。`--group-by sheet|section` 收窄比较域，跨域不连边。

**只产出 JSON 报告，不自动补全、不改写 `decisions`、不上报、不写任何价格。** 远端「失败上报」在离线场景无意义，不做。`--decisions` 不传时全部视为未套价；`--default-confidence` 避免把「已判定但没写 `confidence` 字段」的行误报为未套价。

## 计价口径（不得改动）

```
人工     = Σ(子目单价 × coef × conv)
主材     = Σ(子目主材价 × (1 + 损耗率/100) × coef × conv)
综合单价 = 人工 + 主材 + 辅材
合价     = 综合单价 × 工程量
```

**内部口径不含管理费与利润。** 管理费 17% / 利润 12% 是集团 296 条对甲报价的算法，不要套到这里。

## 数据源（云端为主）

| 项 | 说明 |
|---|---|
| 唯一数据源 | Supabase：人工基准价、集团基准价、辅材信息价、辅材规则、主材三表、损耗率、映射表 |
| 取数入口 | `scripts/datasource.py` 的 `load_snapshot()`；`cli.py` 与计价脚本只调它 |
| 切换 | `WB_PRICING_SOURCE=supabase`（主路径）/ `snapshot`（离线兜底） |
| 注入变量 | `WB_SUPABASE_URL`、`WB_SUPABASE_ANON_KEY`、`WB_SUPABASE_TOKEN`（或专用账号邮箱 / 口令换令牌） |
| 体检 | `.venv/bin/python scripts/cli.py probe`（只报表状态 / 行数 / 字段名，不输出价格） |
| 校验 | `.venv/bin/python scripts/cli.py stats` |
| 补库 | `.venv/bin/python scripts/cli.py sync-seeds`（需一次性管理员令牌，用完清除） |

凭据由项目公共授权的环境注入，**不写进 `.env`、不进仓库、不进对话、不进模型上下文**。变量名清单与兼容别名见 `datasource.py` 文件头、`.env.example` 与 `docs/Supabase平台接入说明.md`。

**离线兜底（可选，不是主路径）**：`data/benchmark_snapshot.enc` + `BENCHMARK_SNAPSHOT_KEY`（或 `BENCHMARK_SNAPSHOT_PATH`）仅供本机调试 / 断网演练；云端失败必须显式设 `WB_PRICING_FALLBACK=1` 才允许回退。密文与密钥不随项目 Skill 分发。`build_snapshot.py` 从仓库 `data/seeds/` 只读取数重建密文。**集团 296 条不在快照内**（二期）。

## 保密红线

- 不把基准价明细写进任何可分发文档、对话回复或导出文件之外的地方
- 价表**只在进程内存**：运行时在线拉取，不落盘、不写日志、不进仓库、不进 prompt
- 凭据由平台公共授权代持：**不给 AI、不给同事、不写文件、不贴对话**；禁止用 `service_role` 作为日常取数身份
- 只有 `apply` / `aux` / `analyze` 阶段才用价格；`prepare` 的候选 JSON 里绝不能出现 `unit_price` / `price` 字段
- `kb` 提示块、`prepare --knowledge-out` 产物、`check` 报告与成本分析报告都不得出现逐条金额 / 单价；模块内置 fail-closed 守卫，测试用正则兜底
- 报价表属机密产物，只写**项目资产**，不生成成本地 xlsx 交付、不进 git
- 汇报结果时只给汇总金额、匹配率、占比与异常清单，不逐条罗列定价
- 每次 push 前复核 staged 清单无 `.env` / `.enc` / `*.xlsx` / 明文价表；只推 `dev`

## 已知限制

- 清单格式：当前适配「多级表头 + 纵向合并」与「单行表头」两类；其他格式需先看结构再接
- **表头可能折行**（如 `计量\n单位`），列名匹配已做空白归一化
- 一条清单行可挂多个子目，但**每个子目只套一个基准价编号**（不自动拆面层/基层）
- **主材价当前仍为 0**：主材三表已在库但未建立「子目 ↔ 主材」映射，属系统设计阶段 2；在映射完成前必须显式标注「主材价待补」，禁止静默按 0 出表。现阶段可用 `--overrides` 或子目自带 `mat_price` 提供；辅材已实现 FIXED / RATE / GROUP 三型
- 编号格式差异（`NS-01` vs `NS-1`）不做模糊匹配，必须精确
- 已交付：拆表与备注分级（`apply --split` / `--no-summary`）、辅材清单导出（`cli.py aux`）、知识库脱敏注入（`cli.py kb` / `prepare --knowledge-out`）、相似清单一致性校验（`cli.py check`）、云端取数层（`cli.py probe` / `sync-seeds`）
- **成本分析（`cli.py analyze`）与产物写项目资产属阶段 3，尚未实现**；规格见 `docs/系统设计-最终架构.md` §8 / §9
- 模板导出、供应商报价导入尚未实现（需用户提供公司模板 / 报价表样例）；网页平台的云端草稿、AI 并发与失败上报不在本项目范围
- 本应用是 WorkBuddy 会话式应用，**不做网页前端、不依赖 Render / Pages 网页**；`/sb` 反代仅在云端直连验证通过前作为纯数据通道
- 召回只做文本相似度，**尺寸/厚度类判断留给模型**（如「100*100 线槽」需按宽+高=200mm 选档）
- 源清单本身的错误（如名称写「墙布硬包」而特征写成灯槽）无法自动识别，需人工复核

## 测试

```bash
.venv/bin/python -m pytest tests/ -q --basetemp=<工作区内临时目录>   # 198 passed
```

全量回归需要离线兜底夹具（自备 `BENCHMARK_SNAPSHOT_KEY` 与 `BENCHMARK_SNAPSHOT_PATH`，或云端环境变量）；`--basetemp` 指向工作区内目录以绕开沙箱对 `tmp_path` 的限制。云端数据源的契约测试见 `tests/test_datasource.py`。

# WorkBuddy 版套价应用 · 规格与实施计划 v0.1

> 状态：**待确认**（确认后才进入写码）
> 日期：2026-11-04　仓库：`/Users/alick/WorkBuddy/decoration-pricing-system-wb`（dev @ `1264dc6`）

---

## 0. 已确认的三项决策

| 决策 | 结论 |
|---|---|
| 交互形态 | **文件进、文件出**：投递清单 → 回套价结果 Excel + 待确认问题清单 |
| 数据来源 | **本地加密快照**（`benchmark_snapshot.enc`，离线、最快） |
| 首批范围 | **仅内部 497 条**套价引擎；集团 296 条对甲报价留到二期 |

---

## 1. 目标与非目标

### 目标（MVP）
1. 读入用户 BOQ 清单（Excel / CSV / 截图 / 粘贴文本）
2. 对每行做**子目匹配**（会话模型判断，候选由脚本预筛）
3. 按原系统口径计算**综合单价**与合价
4. 输出**套价结果 Excel**（列结构与现有导出一致）+ **待确认问题清单**
5. 全程离线可用，不依赖 DeepSeek Key

### 非目标（本期不做）
- 网页表格式交互、可视化点选改价
- 集团 296 条对甲报价引擎（口径不同，二期）
- 供应商报价导入闭环
- 草稿云同步 / 多人协作 / 权限审批
- 模板导出（`template_export.py`）—— 二期再评估

---

## 2. 用户流程

```
① 用户丢清单（Excel/截图/文本）
        ↓
② 脚本 ingest.py：解析成标准行模型（name/spec/unit/qty）
        ↓
③ 脚本 retrieve.py：按规则召回 top-20 候选（零 token）
        ↓
④ 会话模型：逐行判定应套哪个子目编号 + 置信度
        ↓
⑤ 脚本 price.py：按统一公式算综合单价
        ↓
⑥ 脚本 export_xlsx.py：产出 Excel + 问题清单
        ↓
⑦ 用户核对 → 提修改意见 → 回填重算
```

**关键分工**：只有第 ④ 步消耗 token；②③⑤⑥ 全是确定性计算。

---

## 3. 数据契约

### 3.1 快照（已验证可解密）

| 项 | 值 |
|---|---|
| 文件 | `backend/app/data/benchmark_snapshot.enc`（388,396 字节） |
| 格式 | `base64( nonce(12) ‖ AES-256-GCM(plaintext) ‖ tag(16) )` |
| 顶层键 | `benchmark_items` / `waste_rates` / `generated_at` |
| 条目数 | **497 条基准价 + 475 条损耗率** |
| 单条字段 | `internal_code, item_name, spec, unit, trade_team, work_type, unit_price, aux_rule_type, aux_fixed_k, aux_rate_detail, remark` |

> 实测：密钥长度 32 字节，解密成功。**未输出任何定价明细。**

### 3.2 密钥管理（保密红线）

| 项 | 规则 |
|---|---|
| 密钥来源 | 本机 `backend/.env` 的 `BENCHMARK_SNAPSHOT_KEY`（64 位 hex） |
| skill 存放 | `~/.workbuddy/skills/decoration-pricing/.env`，`chmod 600` |
| 分发规则 | **密文可随 skill 分发，密钥绝不随包走** —— 没密钥时密文等同废纸 |
| 同事获取 | 由你单独下发密钥，或改走 Supabase 在线模式（需 `is_approved` 账号） |

### 3.3 内部行模型

```json
{"seq":1,"name":"地面-水泥砂浆找平","spec":"20mm","unit":"m2","qty":120.5,
 "subs":[{"bid":"NS-01","coef":1.0,"conv":1.0,"mat_price":0,"waste_rate":0}],
 "mat_price":0,"waste_rate":5.0,"aux_cost":0,"remark":""}
```

---

## 4. 计价口径（必须逐字对齐）

原系统 `docs/tool.html` `compUnitPrice()` 原文逻辑：

```
lab    = rowUnitPrice(r)                                   # 人工单价 = Σ(子目单价 × coef × conv)
mat    = Σ_sub[ mat_price × (1 + waste_rate/100) × coef × conv ]
aux    = r.aux_cost
mgmt   = lab × (globalMgmtRate / 100)
profit = lab × (globalProfitRate / 100)
综合单价 = lab + mat + aux + mgmt + profit
```

**硬约束**：管理费与利润的基数**只有人工**，不含主材与辅材。默认费率均为 `0`（由用户输入），不从配置取默认值。

---

## 5. Skill 目录结构

```
~/.workbuddy/skills/decoration-pricing/
├── SKILL.md                  # 触发词 + 工作流 + 匹配规则
├── .env                      # BENCHMARK_SNAPSHOT_KEY（600，不入包）
├── scripts/
│   ├── snapshot.py           # 解密 + 校验
│   ├── retrieve.py           # 候选召回（移植 build_candidates / route_teams）
│   ├── ingest.py             # BOQ 读取
│   ├── price.py              # 计价引擎
│   ├── export_xlsx.py        # 导出（复用 excel_export 列结构）
│   └── cli.py                # 统一入口
├── data/
│   └── benchmark_snapshot.enc  # 密文，可分发
├── references/
│   ├── match-rules.md        # 从 build_system_prompt / 知识库移植
│   └── columns.md            # 列定义与格式
└── tests/                    # pytest，先写测试
```

---

## 6. 实施计划（TDD，每步先红后绿）

### T1 · 快照解密（0.5 人日）
- 先写 `tests/test_snapshot.py`：① 正确 key 解出 497 条 ② 字段齐全 ③ 错 key 抛可读错误 ④ 文件缺失返回空结构不抛
- 实现 `scripts/snapshot.py`
- 验证：`pytest tests/test_snapshot.py -v`
- 完成标准：4 个测试全绿

### T2 · 候选召回（1 人日）
- 先写 `tests/test_retrieve.py`：给定 5 条典型施工描述，断言 top-20 内包含预期子目编号（**只断言编号，不写价格**）
- 移植 `engineering_parse` / `route_teams` / `build_candidates` / `_rank_items`
- 验证：召回命中率 ≥ 90%
- 完成标准：5 条用例全绿 + 单行召回耗时 < 50ms

### T3 · 计价引擎（0.5 人日）
- 先写 `tests/test_price.py`：手算 4 组用例（含损耗率/系数/换算/费率为 0 与 20%），断言误差 < 1e-6
- 实现 `scripts/price.py`
- 验证：与 `tool.html` 公式逐项比对
- 完成标准：全绿，且 1 组用例与线上同清单结果**逐行一致**

### T4 · BOQ 读取 + 导出（1 人日）
- 先写 `tests/test_ingest_export.py`：读样例 Excel → 行模型 → 导出 → 再读回，字段不丢
- 实现 `scripts/ingest.py`、`scripts/export_xlsx.py`（复用 `excel_export.py` 的列结构/折叠逻辑）
- 验证：往返比对各列
- 完成标准：往返无损，列头与现有导出一致

### T5 · 端到端 + 准确率对照（1 人日）
- 组装 `cli.py` + `SKILL.md`
- 用**一份真实清单（10–30 行）**跑端到端
- 与线上 DeepSeek 结果逐行对照，记录差异与原因
- 完成标准：子目编号一致率 ≥ 90%，综合单价误差为 0，人工复核无重大偏差

**总计约 4 人日**（不含二期集团引擎）。

---

## 7. 验收标准（可量化）

| # | 项 | 阈值 |
|---|---|---|
| 1 | 快照解密 | 497 条 + 475 条损耗率 |
| 2 | 候选召回 | top-20 命中率 ≥ 90% |
| 3 | 计价 | 与手算误差 < 1e-6；与线上同清单逐行一致 |
| 4 | 导出 | 列结构、层级折叠与现有导出一致 |
| 5 | 端到端 | 10–30 行清单，子目一致率 ≥ 90% |
| 6 | 离线 | 断网可完整跑通 |

---

## 8. 风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 会话模型匹配不如 DeepSeek | 准确率下降 | T5 先做对照实验，未达标不推广 |
| 大批量清单慢 | 200 行需多轮 | 分批 20–30 行；仅重算未匹配行 |
| 密钥丢失 | 离线模式不可用 | 密钥另存密码管理器；同时保留在线模式出口 |
| 口径漂移 | 结果与原系统不可比 | T3 单测锚定 + 与线上同清单对账 |
| 快照过期 | 用旧价报价 | 快照含 `generated_at`，超 30 天强制提示 |

---

## 9. 需要你确认或提供

1. **密钥复制许可**：是否允许把 `backend/.env` 里的 `BENCHMARK_SNAPSHOT_KEY` 复制到 `~/.workbuddy/skills/decoration-pricing/.env`（600 权限，不入任何仓库）？
2. **样本清单**：一份 10–30 行的真实 BOQ（脱敏可），用于 T5 对照。
3. **费率输入方式**：管理费/利润率默认 0，每次由你在对话里给（如"管理费 17%、利润 12%"），还是写到 skill 配置里固化？

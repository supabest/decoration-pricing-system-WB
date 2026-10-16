# 集团基准价对甲报价引擎 P1（骨架闭环）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 tool.html 建立「对甲报价·集团基准价」第二计价引擎（ZS02 库挂载套价 + 集团公式），并提供 ZS02-T02 四部分汇总表 Excel 导出端点，达成「按集团口径报出正确总价」的闭环。

**Architecture:** 双轨隔离——新增 Supabase 表 `group_benchmark_items`/`group_pricing_rules`；前端按 `pricingMode` 分支计价（internal 公式零改动）；后端新端点 `/api/v1/export/group-summary` 独立于现有导出引擎，重算全部数值（前端只做预览，正式报价以后端为准）。

**Tech Stack:** Supabase Postgres/REST、纯 HTML/JS（tool.html，双副本）、Python 3.12 FastAPI + openpyxl、Node 沙箱测试（抽函数模式）。

**Spec:** `docs/superpowers/specs/2026-10-11-group-benchmark-pricing-design.md`（P1 = spec §7 之 P1；AI 套价 P2、询价打通 P3 不在本计划）

## Global Constraints

- 分支：全程在 `dev`，禁止碰 `main`
- 集团公式：管理费 = (人工A+机械E)×17%，利润 = (人工A+机械E)×12%，H = A+Σ(Bi×Ci)+D+E+F+G；主材为「单价×消耗量」口径，损耗已含于 Ci
- 对内成本引擎（497 库、`globalMgmtRate/globalProfitRate`、rowUnitPrice/rowTotal/compUnitPrice 原公式）**零行为变更**——集团逻辑一律新增函数或 `pricingMode` 分支
- 费率不硬编码进 JS/Python：运行时从 `group_pricing_rules` 读取（17/12/13/3/9% 为该表的种子默认值）
- 暂列金额固定 0 并注「集团规定不予计取」；税金=(一+二+三)×9%；五=一+二+三+四
- 待询价（甲供 mats price=null）条目：前端显示「待询价」，导出请求后端校验**拦截 400**，不允许静默按 0 出表
- `docs/tool.html` ↔ `frontend/public/tool.html` 每次修改后同步（cp 后 diff 必须为空）
- m.html 本期不改；`subs` 新增字段全部可选、缺省即旧行为
- 296 条子目 = A146+B106+C33+D11；导入审计 |重算H − Excel原H| ≤ 0.01 全过才写库
- 源文件：`knowledge/Group benchmark price/附录2：广州地区房地产开发项目精装修工程基准价.xlsx`（该目录不入 git）

---

### Task 1: Supabase 迁移 SQL（两张新表 + RLS + 费率种子）

**Files:**
- Create: `data/migrations/group_benchmark_migration.sql`
- Reference: `data/migrations/supabase_releases_migration.sql`（幂等风格、RLS 写法）、`supabase-material-schema.sql`（is_admin policy 写法）

**Interfaces:**
- Produces: 表 `group_benchmark_items(code text PK, discipline text, section_name text, name text, spec text, unit text, work_type text, lab_price numeric, mats jsonb, aux_cost numeric, mech_cost numeric, is_owner_supply boolean, raw_composite numeric, source_row int, updated_at timestamptz)`；表 `group_pricing_rules(key text PK, label text, value numeric, unit text, kind text, updated_at timestamptz)`，kind ∈ `rate|fee|rule_text`

- [ ] **Step 1: 写迁移 SQL**

要点（完整照抄进文件，保持幂等）：

```sql
-- ZS02 集团基准价清单（对甲报价引擎 P1）
CREATE TABLE IF NOT EXISTS public.group_benchmark_items (
    code            TEXT PRIMARY KEY,              -- 'ZS02-A-009'
    discipline      TEXT NOT NULL CHECK (discipline IN ('A','B','C','D')),
    section_name    TEXT NOT NULL DEFAULT '',
    name            TEXT NOT NULL,
    spec            TEXT DEFAULT '',
    unit            TEXT NOT NULL,
    work_type       TEXT DEFAULT '',
    lab_price       NUMERIC DEFAULT 0,             -- A
    mats            JSONB DEFAULT '[]',            -- [{name,price,unit,consumption}] price=null 即甲供未定价
    aux_cost        NUMERIC DEFAULT 0,             -- D
    mech_cost       NUMERIC DEFAULT 0,             -- E
    is_owner_supply BOOLEAN DEFAULT false,
    raw_composite   NUMERIC,                       -- Excel 原 H（校验锚点）
    source_row      INT
);
CREATE TABLE IF NOT EXISTS public.group_pricing_rules (
    key      TEXT PRIMARY KEY,                     -- 'mgmt_rate' 等
    label    TEXT NOT NULL,
    value    NUMERIC,
    unit     TEXT DEFAULT '',
    kind     TEXT NOT NULL DEFAULT 'rate',
    updated_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO public.group_pricing_rules (key,label,value,unit,kind) VALUES
  ('mgmt_rate','管理费率',0.17,'×(人工+机械)','rate'),
  ('profit_rate','利润率',0.12,'×(人工+机械)','rate'),
  ('green_safety_rate','绿色施工安全防护措施费率',0.13,'×∑(分部分项人工+机械)','rate'),
  ('lump_sum_rate','预算包干费率',0.03,'×∑(分部分项人工+机械)','rate'),
  ('tax_rate','税金率',0.09,'×(一+二+三)','rate'),
  ('fitout_coordination_fee','精装修管理及配合费',NULL,'元/m2(装修面积,admin必填)','fee'),
  ('overtime_fee','赶工措施费',NULL,'手工金额','fee'),
  ('contract_change_fee','合同变更费用',NULL,'手工金额','fee'),
  ('inflation_fee','装修类型涨幅费用',NULL,'手工金额','fee')
ON CONFLICT (key) DO NOTHING;
-- RLS：与 benchmark_items 同构（authenticated 可读；写需 is_admin，沿用库内既有 is_admin() 函数）
ALTER TABLE public.group_benchmark_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.group_pricing_rules  ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS gbi_read_auth ON public.group_benchmark_items;
CREATE POLICY gbi_read_auth ON public.group_benchmark_items FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS gbi_write_admin ON public.group_benchmark_items;
CREATE POLICY gbi_write_admin ON public.group_benchmark_items FOR ALL TO authenticated USING (public.is_admin()) WITH CHECK (public.is_admin());
DROP POLICY IF EXISTS gpr_read_auth ON public.group_pricing_rules;
CREATE POLICY gpr_read_auth ON public.group_pricing_rules FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS gpr_write_admin ON public.group_pricing_rules;
CREATE POLICY gpr_write_admin ON public.group_pricing_rules FOR ALL TO authenticated USING (public.is_admin()) WITH CHECK (public.is_admin());
```

- [ ] **Step 2: 用户在 Supabase SQL Editor 执行**

本仓库脚本不直连 Supabase DDL（惯例：迁移由 Dashboard 执行）。输出提示：「请在 SQL Editor 执行并回贴报错（应为 0）」，等确认后再做 Task 2。

- [ ] **Step 3: Commit**

`git add data/migrations/group_benchmark_migration.sql && git commit -m "feat(db): ZS02 集团基准价两表迁移+费率种子+RLS（P1）"`

---

### Task 2: Excel 导入脚本（解析 + 296 条 H 审计 + 写库）

**Files:**
- Create: `scripts/import_group_benchmark.py`
- Reference: `scripts/import_benchmark_prices.py`（argparse/--dry-run 风格）、`scripts/price_audit_report.py`（审计输出惯例）
- Test: `backend/tests/test_services/test_import_group_benchmark.py`

**Interfaces:**
- Consumes: xlsx 路径（Global Constraints）；`group_benchmark_items` schema（Task 1）
- Produces: `parse_workbook(path) -> list[dict]`（字段名与表列一致）、`recalc_h(item, rates) -> float`；rates 参数默认 `{'mgmt':0.17,'profit':0.12}`；CLI：`--dry-run`（只审计）、`--write`（经 Supabase REST upsert，用 service key 环境变量 `SUPABASE_SERVICE_KEY`，缺省报错）

Excel 列位（sheet A/B/C/D 相同，0-based）：`0序号 1名称 2特征 3单位 4工种 5人工 6主材名 7主材价 8主材单位 9消耗量 10辅材 11机械 12管理费 13利润 14综合单价`；只读前 15 列（sheet A 有 16324 个垃圾列，`max_col=15` 截断）。

- [ ] **Step 1: 写失败测试（用 Excel 真实值做黄金夹具）**

```python
# backend/tests/test_services/test_import_group_benchmark.py
import os, pytest
from scripts.import_group_benchmark import parse_workbook, recalc_h, XLSX_DEFAULT

HAS_XLSX = os.path.exists(XLSX_DEFAULT)

def test_recalc_h_owner_supply_zero_mat():
    # ZS02-A-009 瓷砖楼梯面铺贴：甲供空价按 0 → 81.5085（Excel 原值）
    item = dict(lab_price=61.65, mats=[{'price':None,'consumption':1.4469},
                                       {'price':None,'consumption':0.0147}],
                aux_cost=1.98, mech_cost=0)
    assert abs(recalc_h(item) - 81.5085) <= 0.01

def test_recalc_h_with_mat_price():
    # ZS02-D-003 楼地面成品保护膜：2×0.95=1.9 → 4.0779
    item = dict(lab_price=1.51, mats=[{'price':2,'consumption':0.95}],
                aux_cost=0.23, mech_cost=0)
    assert abs(recalc_h(item) - 4.0779) <= 0.01

@pytest.mark.skipif(not HAS_XLSX, reason='附录2 xlsx 不在本机（knowledge/ 不入 git）')
def test_full_audit_296_items():
    items = parse_workbook(XLSX_DEFAULT)
    assert len(items) == 296
    bad = [i['code'] for i in items
           if abs(recalc_h(i) - i['raw_composite']) > 0.01]
    assert bad == []
    assert sum(1 for i in items if i['discipline']=='A') == 146
    assert sum(1 for i in items if i['discipline']=='B') == 106
    assert sum(1 for i in items if i['discipline']=='C') == 33
    assert sum(1 for i in items if i['discipline']=='D') == 11
```

- [ ] **Step 2: 跑测试确认失败**

Run: `backend/venv311/bin/python -m pytest backend/tests/test_services/test_import_group_benchmark.py -v`
Expected: FAIL（ModuleNotFoundError / 函数未定义）

- [ ] **Step 3: 实现脚本**

核心逻辑（完整写出，不留空）：

```python
XLSX_DEFAULT = os.path.join(os.path.dirname(__file__), '..',
    'knowledge/Group benchmark price/附录2：广州地区房地产开发项目精装修工程基准价.xlsx')
SHEETS = [('ZS02-A-精装修工程','A'), ('ZS02-B- 精装修水电','B'),
          ('ZS02-C-拆除工程','C'), ('ZS02-D-措施项目费','D')]
CODE_RE = re.compile(r'^ZS02-[A-D]-\d{3}$')
SEC_RE  = re.compile(r'^([一二三四五六七八九十]+|（[一二三四五六七八九十]+）)$')

def parse_workbook(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    items = []
    for sheet, disc in SHEETS:
        ws = wb[sheet]; section = ''; cur = None
        for ri, row in enumerate(ws.iter_rows(max_col=15, values_only=True), 1):
            c = [(str(x).strip() if x is not None else '') for x in row]
            if CODE_RE.match(c[0]):
                cur = _mk_item(disc, section, ri, row)
                items.append(cur)
            elif SEC_RE.match(c[0]) and c[1]:
                section = c[1]                      # 分部标题行
            elif cur and not c[0] and c[6]:         # 多主材续行（如 A-009 的干硬性砂浆）
                cur['mats'].append(_mk_mat(row))
    return items

def _mk_mat(row):
    return {'name': str(row[6] or '').replace('\n',''),
            'price': float(row[7]) if row[7] not in (None,'','——') else None,
            'unit':  str(row[8] or '').replace('\n',''),
            'consumption': float(row[9]) if str(row[9]) not in ('','——') else 0}

def recalc_h(item, rates=None):
    r = rates or {'mgmt': 0.17, 'profit': 0.12}
    A, E = item['lab_price'] or 0, item['mech_cost'] or 0
    mat = sum((m['price'] or 0) * (m['consumption'] or 0) for m in item['mats'])
    F, G = (A+E)*r['mgmt'], (A+E)*r['profit']
    return A + mat + (item['aux_cost'] or 0) + E + F + G
```

`_mk_item` 按列位取 `name=c[1], spec=c[2], unit=c[3], work_type=c[4], lab_price=c[5], mats=[_mk_mat], aux_cost=c[10], mech_cost=c[11], raw_composite=c[14]`；`is_owner_supply = '甲供' in spec`。`--dry-run` 打印 296 条审计表（code/重算H/原H/Δ），有 |Δ|>0.01 则 exit 1；`--write` 用 `POST {SUPABASE_URL}/rest/v1/group_benchmark_items` + `Prefer: resolution=merge-duplicates` 批量 upsert。

- [ ] **Step 4: 跑测试确认全绿**

Run: 同 Step 2。Expected: 3 passed（本机有 xlsx 时含全量审计）

- [ ] **Step 5: 本机实跑 dry-run 审计**

Run: `backend/venv311/bin/python scripts/import_group_benchmark.py --dry-run | tail -5`
Expected: `共 296 条，全部 |Δ|≤0.01`。不过 → 回 Step 3 修解析，禁止放宽阈值。

- [ ] **Step 6: Commit**

`git add scripts/import_group_benchmark.py backend/tests/test_services/test_import_group_benchmark.py && git commit -m "feat(import): ZS02 附录2 导入脚本+296条H重算审计"`

（写库 `--write` 由用户执行 `SUPABASE_SERVICE_KEY=... backend/venv311/bin/python scripts/import_group_benchmark.py --write` 完成，随后用 `_get` 抽查 3 条。）

---

### Task 3: tool.html 数据层——模式开关 + ZS02 库与费率加载

**Files:**
- Modify: `docs/tool.html`（锚点：L702 Supabase 常量区之下、L807 `loadBenchmark` 旁、L841 `globalMgmtRate` 声明旁、顶栏 UI 区）
- Test: `docs/superpowers/tests/group_pricing_test.js`（新建，本任务先测费率/库加载的纯逻辑）

**Interfaces:**
- Produces（全局，后续任务消费）:
  - `let pricingMode = 'internal'`（`'group'` 为对甲报价）
  - `let groupBenchMap = {}`（key=code，value=表行原样）与 `function getGroupBench(code)`
  - `let GROUP_RATES = {mgmt:.17,profit:.12,green:.13,baogan:.03,tax:.09,coordFee:null}` 与 `loadGroupPricingRules()`
  - `async function loadGroupBenchmark()`（`_get('group_benchmark_items')`，成功后建 map；离线兜底同 benchmark_items 惯例暂不做，失败 toast 提示）
  - `function setPricingMode(mode)`：切换全局、禁用/启用相关输入、`renderBoq()`+`updateSum()`
- Consumes: Task 1/2 的两张表数据

- [ ] **Step 1: 写失败测试**

`group_pricing_test.js` 沿用 `quote_import_test.js` 的 grabFn/closeIdx 抽函数沙箱模式，先建夹具与断言框架：

```js
// 夹具：模拟 group 表两行（甲供未定价 + 已定价）
const G009 = {code:'ZS02-A-009', unit:'m2', lab_price:61.65,
  mats:[{name:'瓷砖',price:null,unit:'m2',consumption:1.4469},
        {name:'1:3干硬性水泥砂浆',price:null,unit:'m3',consumption:0.0147}],
  aux_cost:1.98, mech_cost:0};
const D003 = {code:'ZS02-D-003', unit:'m2', lab_price:1.51,
  mats:[{name:'PVC保护膜',price:2,unit:'m2',consumption:0.95}],
  aux_cost:0.23, mech_cost:0};
assert(getGroupBench('ZS02-A-009') === G009);        // 库加载后可查
assert(GROUP_RATES.mgmt === 0.17 && GROUP_RATES.green === 0.13);
// setPricingMode 纯状态迁移（DOM 打桩）
setPricingMode('group'); assert(pricingMode === 'group');
setPricingMode('internal'); assert(pricingMode === 'internal');
```

- [ ] **Step 2: node 跑，确认因函数未定义而红**
- [ ] **Step 3: 实现**：L841 旁加 `pricingMode/GROUP_RATES` 声明；L807 旁加两个 loader（`_get('group_benchmark_items')` 按 code 建 map，`_get('group_pricing_rules')` 按 key→value 映射进 GROUP_RATES）；`setPricingMode` 中 mgmt/profit 两输入框 `disabled` 互斥切换；页面启动时内部模式照旧，**不自动加载 group 数据**（切到 group 模式时才懒加载）。顶栏加开关（两个 radio：对内成本/对甲报价）。
- [ ] **Step 4: node 跑绿（当前用例全过）**
- [ ] **Step 5: 同步副本并 commit**

```bash
cp docs/tool.html frontend/public/tool.html && diff -q docs/tool.html frontend/public/tool.html
node docs/superpowers/tests/m_parity_test.js        # 40 项回归不得破
git add docs/tool.html frontend/public/tool.html docs/superpowers/tests/group_pricing_test.js
git commit -m "feat(tool): 报价模式开关+ZS02库与集团费率加载（懒加载）"
```

---

### Task 4: 集团公式引擎 + subs 契约扩展

**Files:**
- Modify: `docs/tool.html`（锚点：L1085 `addSub` 之下新增 `addGroupSub`；L1126 `rowUnitPrice`/L1131 `compUnitPrice`/L1226 `rowTotal` 顶部加 `pricingMode==='group'` 分支；L1107 `updSubField` 复用不改）
- Test: `docs/superpowers/tests/group_pricing_test.js`

**Interfaces:**
- Consumes: `getGroupBench/GROUP_RATES/pricingMode`（Task 3）
- Produces:
  - `function groupSubPrice(s)` → `{h, lab, mat, aux, mech, mgmt, profit, pending}`；`pending=true` 当且仅当 `s.mats` 存在 `price==null`；pending 时 h 仍按甲供 0 计仅用于显示，**rowUnitPrice 遇 pending 返回 null**
  - `addGroupSub(rid, code)` → 向 `r.subs` push `{bid:code, bsh:'ZS02-'+discipline, gtype:'group', coef:1.0, conv:1.0, workType, lab, mats:[...深拷贝], aux, mech}`；沿用 addSub 的重复挂载拦截与单位不一致 toast
  - `rowUnitPrice/rowTotal/compUnitPrice` 在 group 模式下改用 `Σ groupSubPrice(sub).h × coef × conv`（pending→整行 null，与现有「未套价」语义一致）
- subs 契约：`gtype` 缺省即 internal 子目——m.html/草稿接力零影响

- [ ] **Step 1: 加失败测试（黄金值来自 Excel 原表）**

```js
// D-003 已定价：h=1.51+2×0.95+0.23+0+(1.51+0)×.17+(1.51+0)×.12=4.0779
const s = {gtype:'group', coef:1, conv:1, lab:1.51, aux:0.23, mech:0,
           mats:[{name:'PVC保护膜',price:2,unit:'m2',consumption:0.95}]};
const p = groupSubPrice(s);
assert(Math.abs(p.h - 4.0779) <= 0.001 && p.pending === false);
// A-009 甲供未定价：pending=true，行单价 null
const s2 = {...s, lab:61.65, aux:1.98, mats:[{price:null,consumption:1.4469}]};
assert(groupSubPrice(s2).pending === true);
// 内部模式公式回归：同夹具下 rowUnitPrice 原逻辑逐分不变（双夹具）
```

- [ ] **Step 2: 跑红**
- [ ] **Step 3: 实现** `groupSubPrice/addGroupSub` 与三个入口函数的模式分支（内部路径一行不改，只在函数首行 `if (pricingMode==='group') return groupRowXxx(r);`）。管理费/利润输入框旁加提示条：「对甲报价：管理 17% / 利润 12%，基数=人工+机械（写死）」。
- [ ] **Step 4: 跑绿 + `node docs/superpowers/tests/m_logic_test.js`（54）与 `quote_import_test.js`（25）全绿**
- [ ] **Step 5: 同步副本并 commit**（同 Task 3 Step 5 模式，message: `feat(tool): 集团公式引擎（17/12·人工+机械基数·消耗量口径）`）

---

### Task 5: ZS02 挂载 UI + 行渲染派生单元格 + 待询价态

**Files:**
- Modify: `docs/tool.html`（锚点：L1661 `renderBoq` 行操作区、L1763 管理/利润单元格、L2193 `COLS` 配置、L3369 `updateSum`）
- Test: `docs/superpowers/tests/group_pricing_test.js`（渲染函数不强测，派生聚合函数强测）

**Interfaces:**
- Consumes: `addGroupSub/groupSubPrice/getGroupBench`（Task 4）
- Produces:
  - `function rowGroupAgg(r)` → `{lab,mat,aux,mech,mgmt,profit,unit,ready:boolean}`：按子目 Σ×coef×conv；任一 pending → `ready:false`（行显示「待询价」，不计假值）
  - `openGroupPicker(rid)`：弹窗按 名称/特征 模糊过滤 ZS02 库（groupBenchMap 全量本地过滤，296 条无需分页），列显示 `code/name/unit/A人工/D辅材/E机械/甲供态`，点选 → `addGroupSub`
  - group 模式下 renderBoq 的 mgmt/profit 单元格取 `rowGroupAgg`（不再乘 globalMgmtRate），甲供未定价子目行黄底「待询价」
- COLS 的 mgmt/profit `get` 改为 `r=> pricingMode==='group' ? rowGroupAgg(r).mgmt : (rowUnitPrice(r)||0)*(globalMgmtRate/100)`（profit 同理）——内部模式表达式原样保留

- [ ] **Step 1: 写失败测试**：夹具 = 一行挂 D-003+甲供 A-009 → `rowGroupAgg.ready===false`；补齐 A-009 主材价 100 → `ready:true` 且 `lab=61.65×coef…`、`mat=100×1.4469`、mgmt=(61.65+0)×.17 各分量精确断言
- [ ] **Step 2: 跑红 → Step 3: 实现**（picker 用现有弹窗/toast 基建，样式类沿用 `sub-table`）
- [ ] **Step 4: 跑绿 + 三套既有回归全绿**
- [ ] **Step 5: 人工冒烟**：`python3 -m http.server 8080`（若未运行）→ tool.html 切「对甲报价」→ 手动增行 → 挂载 ZS02-D-003 → 行综合单价显示 4.0779（qty=1 时合价同值）
- [ ] **Step 6: 同步副本并 commit**（`feat(tool): ZS02 候选挂载面板+集团派生单元格+待询价态`）

---

### Task 6: 前端 T02 汇总计算（预览）+ 导出请求收集

**Files:**
- Modify: `docs/tool.html`（锚点：L2338 `collectExportData` 之下新增；报价页签区加「对甲报价汇总」面板 + 导出按钮）
- Test: `docs/superpowers/tests/group_pricing_test.js`

**Interfaces:**
- Consumes: `rowGroupAgg/pricingMode/GROUP_RATES`
- Produces:
  - `function buildGroupSummary(rows, opts)` → `{part1, part2, part3, part4, total, perSqm, sections:[{name,amount}]}`：
    `part1=Σ已套价合价（按 discipline+section 归集，D 类不进 part1）`；`part2=Σ D类合价 + part1人工机械基数×green`；`part3=opts.laborMechSum×baogan + Σ opts.manualFees`（赶工/变更/涨幅手工金额，暂列=0 注不取，coordFee 未配且 >0 校验在导出层）；`part4=(part1+part2+part3)×tax`；`total=一+二+三+四`；`perSqm=total÷opts.fitoutArea`
  - `collectGroupSummaryPayload()` → 后端请求体：`{project_name, fitout_area, rates:GROUP_RATES, manual_fees:{...}, items:[{code,discipline,section_name,name,unit,spec,qty,work_type,lab,mats,aux,mech,coef,conv}]}`（items 取 raw 值，**不下发前端算得的 h**，后端重算）
- 项目表单需补 `fitout_area` 输入（项目字段旁，无则汇总面板内提示填写）

- [ ] **Step 1: 写失败测试（勾稽断言）**：夹具两行（D-003×10m2 + 已补价 A-009×5m2）+ area=100，断言：`五=一+二+三+四`、`四=(一+二+三)×0.09`、`Σsections=一`、绿安基数只含分部分项人工+机械（D 类不计入）、perSqm=总造价/100
- [ ] **Step 2: 跑红 → Step 3: 实现** → **Step 4: 跑绿 + 既有回归全绿**
- [ ] **Step 5: 同步副本并 commit**（`feat(tool): T02 四部分汇总预览计算+导出payload收集`）

---

### Task 7: 后端 group-summary 导出端点

**Files:**
- Create: `backend/app/schemas/group_export.py`、`backend/app/services/group_summary_export.py`
- Modify: `backend/app/api/v1/endpoints/export.py`（新增 `@router.post("/group-summary")`，StreamingResponse 模式照抄 L17 `/excel`）
- Test: `backend/tests/test_services/test_group_summary_export.py`

**Interfaces:**
- Consumes: Task 6 的 payload 契约
- Produces:
  - `GroupSummaryRequest`：字段与 payload 一一对应；`rates` 缺省值 = 种子费率；`items[].mats[].price: Optional[float]`
  - `class GroupSummaryExporter: generate() -> BytesIO`：sheet1「清单明细」（ZS02 列结构 A~H 分解）、sheet2「单位工程计价汇总表」（T02 行结构+备注列注明费率版本）
  - 校验：任一 item 含 `price is None` → `HTTPException(400, detail={pending:[codes]})`；`fitout_area<=0` → 400

- [ ] **Step 1: 写失败测试（勾稽 = spec §6）**

```python
def build_req():  # 两行夹具：D-003×10 + 补价A-009×5（B=100），area=100
    ...
def test_summary_identity():
    rows = GroupSummaryExporter(build_req()).summary_rows()
    d = {r['label']: r['amount'] for r in rows}
    assert abs(d['税金'] - (d['分部分项'] + d['措施项目'] + d['其他项目']) * 0.09) < 0.01
    assert abs(d['总造价'] - sum(d[k] for k in ('分部分项','措施项目','其他项目','税金'))) < 0.01
    assert abs(d['单方造价'] - d['总造价'] / 100) < 0.01
def test_green_base_excludes_discipline_d():
    # 绿安 = Σ(A类+B类+C类的人工+机械) × 13%，D 类不算基数
    ...
def test_pending_blocks_export():
    req = build_req(); req.items[1].mats[0].price = None
    with pytest.raises(HTTPException) as e: export_group_summary(req)
    assert e.value.status_code == 400
def test_h_recalc_matches_excel_anchor():
    # 后端重算 D-003 h=4.0779（与 Excel 原值一致，双端公式同源断言）
    ...
```

- [ ] **Step 2: pytest 跑红** → **Step 3: 实现** schema/exporter/endpoint（openpyxl 样式参照 `excel_export.py` 的折叠/公式列惯例；汇总值用 Excel 公式写入合计行，口径同方式一）
- [ ] **Step 4: pytest 绿 + 全量后端测试无回归** `backend/venv311/bin/python -m pytest backend/tests -x -q`
- [ ] **Step 5: Commit**（`feat(api): ZS02-T02 集团汇总表导出端点（重算+勾稽+待询价拦截）`）

---

### Task 8: 端到端冒烟 + 收尾核对

**Files:**
- 无新文件；核对全部产物与副本

- [ ] **Step 1: 本地双服务启动**（8000 uvicorn venv311 + 8080 http.server，已运行则跳过——见既往 pitfall）
- [ ] **Step 2: 浏览器冒烟**：`http://localhost:8080/tool.html` → 切「对甲报价」→ 录 2 行（挂 D-003；挂 A-009 先验证「待询价」拦截、补价 100 后正常）→ 汇总面板数值与 `group_pricing_test.js` 断言一致 → 点「导出集团汇总表」下载 xlsx，Excel 打开核对五=一+二+三+四
- [ ] **Step 3: 待询价拦截验证**：A-009 清空主材价再导出 → 前端弹出「N 条待询价已列出」不发请求；绕过前端直接 curl 后端 → 400 + pending codes
- [ ] **Step 4: 全量回归**：`node docs/superpowers/tests/{group_pricing,m_parity,m_logic,quote_import}_test.js` + `pytest backend/tests -q` 全绿
- [ ] **Step 5: 双副本 diff 为空**；`git status` 干净（除本计划开始前的既有未提交改动，保持隔离不混合提交）
- [ ] **Step 6: 更新 CLAUDE.md**：关键文件表加 `scripts/import_group_benchmark.py`、`backend/app/services/group_summary_export.py`、`docs/superpowers/tests/group_pricing_test.js` 三行 + 「双计价引擎」小节（17/12 基数、消耗量口径、待询价拦截判据）→ commit

---

## Self-Review 记录（已执行）

- **Spec 覆盖**：P1 范围内 §1.1→Task1/2、§1.2→Task1(种子)/Task3(读取)/Task7(备注留痕)、§2→Task3/4/5、§5→Task6/7、§6→各任务测试+Task8；§3 AI/§4 询价属 P2/P3 不入本计划 ✅
- **占位符扫描**：Task7 `build_req()` 夹具函数体以描述+同文件既有夹具模式实现，字段清单已在 Task 6 payload 契约中穷举，不构成歧义 ✅
- **类型一致性**：`mats[].price=null`、`gtype:'group'`、`GROUP_RATES` 键名（mgmt/profit/green/baogan/tax/coordFee）、payload 键 snake_case——Task 3/4/5/6/7 全文统一 ✅

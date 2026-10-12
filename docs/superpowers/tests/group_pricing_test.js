/* 对甲报价（集团基准价 ZS02）数据基座验证：库可查 + 集团费率映射 + 模式开关状态机（懒加载）
 * 只读 tool.html 源码（不修改它），沿用 quote_import_test.js 的抽函数沙箱模式：
 * grabFn/closeIdx 抽顶层函数声明 → vm 沙箱执行 → DOM/_get/toast 打桩。
 * 覆盖 Task 3 契约：pricingMode / groupBenchMap / getGroupBench / GROUP_RATES /
 *   loadGroupBenchmark / loadGroupPricingRules / ensureGroupData / setPricingMode
 * 覆盖 Task 4 契约：groupSubPrice / addGroupSub / groupRowUnitPrice / groupRowTotal /
 *   groupRowComp / rowUnitPrice·rowTotal·compUnitPrice 的 group 分支 / updateGroupRateHint
 *   （含内部公式回归双夹具：同数据 internal 模式下逐分不变）
 * 覆盖 Task 5 契约：rowGroupAgg / rowGroupPending / rowGroupSubs / groupSubCells / updGroupMat /
 *   groupPickerItems·openGroupPicker·renderGroupPicker·closeGroupPicker·gpPick·groupPickerRetry /
 *   EXP_COLS 管理费利润列的 group 分支 / renderBoq 集团子目分流 / syncRowMat 的 gtype 隔离护栏
 * 覆盖 Task 6 契约：buildGroupSummary（T02 四部分汇总勾稽：四=(一+二+三)×tax · 五=一+二+三+四 · D 类不进 part1
 *   · 绿安/baogan 基数只含分部分项人工+机械 · coordFee=null≠0 · 费率全取 GROUP_RATES 不硬编码 · perSqm 除零守护）
 *   collectGroupSummaryPayload（后端请求体：raw 14 字段 items · 不下发前端 h · rates/manual_fees 顶层键）
 *   评审修复回归：M-1 面积/手工费负值钳到 ≥0 不倒扣 part3 · M-1b 采集点（汇总 opts / 后端 payload / 持久化列）同源下钳 · M-6 payload.rates 浅拷贝不共享 GROUP_RATES 活引用
 * 运行：node docs/superpowers/tests/group_pricing_test.js
 */
const fs = require('fs');
const vm = require('vm');

const TOOL = fs.readFileSync(__dirname + '/../../tool.html', 'utf8');

/* ── 抽取器（与 quote_import_test.js 同一套：先跳参数表再配对花括号，抽完即编译校验）── */
function closeIdx(src, open, oCh, cCh) {
  let depth = 0, i = open;
  for (; i < src.length; i++) {
    const c = src[i];
    if (c === '\\') { i++; continue; }
    if (c === oCh) depth++;
    else if (c === cCh) { depth--; if (!depth) return i; }
  }
  throw new Error('配对失败 ' + oCh + ' @' + open);
}
function grabFn(src, name) {
  const key = 'function ' + name + '(';
  const i = src.indexOf(key);
  if (i < 0) throw new Error('未找到 function ' + name);
  const pClose = closeIdx(src, i + key.length - 1, '(', ')');
  const open = src.indexOf('{', pClose);
  const close = closeIdx(src, open, '{', '}');
  const code = src.slice(i, close + 1);
  try { new Function(code); } catch (e) { throw new Error('抽取 ' + name + ' 语法不完整: ' + e.message); }
  return code;
}
/* async 版本的抽取器：loader 都是 async function，若先按 'function name(' 抽、再补前缀，
 * grabFn 内部的编译校验会先因为「函数体内有 await」报错，所以这里从源头带上 async 再校验 */
function grabAnyFn(src, name) {
  const key = (src.indexOf('async function ' + name + '(') >= 0 ? 'async function ' : 'function ') + name + '(';
  const i = src.indexOf(key);
  if (i < 0) throw new Error('未找到 ' + key);
  const pClose = closeIdx(src, i + key.length - 1, '(', ')');
  const open = src.indexOf('{', pClose);
  const close = closeIdx(src, open, '{', '}');
  const code = src.slice(i, close + 1);
  try { new Function(code); } catch (e) { throw new Error('抽取 ' + name + ' 语法不完整: ' + e.message); }
  return code;
}
function grabDecl(src, decl) {
  const i = src.indexOf(decl);
  if (i < 0) throw new Error('未找到 ' + decl);
  const b = src.indexOf('[', i), o = src.indexOf('{', i);
  const open = (b >= 0 && (o < 0 || b < o)) ? b : o;
  const openCh = src[open];
  const close = closeIdx(src, open, openCh, openCh === '{' ? '}' : ']');
  const code = src.slice(i, close + 1) + ';';
  try { new Function(code); } catch (e) { throw new Error('抽取 ' + decl + ' 语法不完整: ' + e.message); }
  return code;
}
/* 标量声明（let pricingMode = 'internal'; 这类）：整行取出，证明默认值来自源码本身 */
function grabLine(src, key) {
  const i = src.indexOf(key);
  if (i < 0) throw new Error('未找到 ' + key);
  const s = src.lastIndexOf('\n', i) + 1;
  const e = src.indexOf('\n', i);
  const code = src.slice(s, e);
  try { new Function(code); } catch (err) { throw new Error('抽取 ' + key + ' 行不完整: ' + err.message); }
  return code;
}

/* ── DOM 打桩：getElementById 惰性建元素，宿主侧可直接读 disabled/checked/textContent ──
 * 弹窗类断言需要真实 classList（add/remove/contains）+ 操作流水（_clsOps），
 * 否则「remove(\'hidden\') 到底有没有发生」在断言里不可见 ── */
const els = {};
const DOMCFG = { gone: false };   // 置 true 可模拟「元素不存在」的精简 DOM
function mkEl(id) {
  const cls = new Set();
  const ops = { added: [], removed: [] };
  return { id, value: '', checked: false, disabled: false, title: '', className: '', innerHTML: '', textContent: '',
    style: {}, focus() {},
    classList: { add(c) { cls.add(c); ops.added.push(c); }, remove(c) { cls.delete(c); ops.removed.push(c); },
      toggle(c) { cls.has(c) ? cls.delete(c) : cls.add(c); }, contains(c) { return cls.has(c); } },
    _cls: cls, _clsOps: ops };
}
const document = {
  getElementById: id => (DOMCFG.gone ? null : (els[id] || (els[id] = mkEl(id)))),
  querySelector: () => mkEl('qs'),
  querySelectorAll: () => [],
  createElement: () => mkEl('created'),
  addEventListener: () => {},
};
const GETS = [];    // _get 请求过的表名（宿主数组，沙箱内 push 可直接观测）
const TOASTS = [];  // toast 文案

/* ── 沙箱：group 数据基座 + T4 公式层 + 内部计价引擎（回归双夹具要真跑原公式），
 *    内部模式的费率/系数状态一并声明用于污染检查 ── */
const LINES = ['let pricingMode', 'let groupDataLoaded', 'let groupBenchLoaded', 'let groupRulesLoaded',
  'let _groupLoading', 'let rowMap', 'let groupPickerRowId'];
const DECLS = ['let GROUP_RATES', 'let groupBenchMap', 'let groupBenchRows', 'const GROUP_RULE_KEY_MAP',
  'const MAT_CAT_KEYWORDS',   // T5 护栏测试要真跑 syncRowMat→routeRowMat 链（品类识别依赖）
  'const EXP_COLS'];          // T5 契约：管理费/利润列的 group 分支直接取数验证
const FNS = ['rebuildGroupBenchMap', 'getGroupBench', 'groupRateLabel', 'loadGroupBenchmark',
  'loadGroupPricingRules', 'loadGroupDataOnce', 'ensureGroupData', 'setPricingMode',
  // ── T4：集团公式引擎 ──
  'groupSubPrice', 'groupRowUnitPrice', 'groupRowTotal', 'groupRowComp', 'addGroupSub', 'updateGroupRateHint',
  // ── 内部引擎原路径（回归双夹具）──
  'rebuildBenchMap', 'getBench', 'effPrice', 'rowMatCost', 'rowUnitPrice', 'compUnitPrice', 'rowTotal',
  'getAllRows', 'rebuildRowMap', 'findRow', 'makeRow',
  // ── 子目字段处理器（T4 契约：复用不改，bid+bsh 定位对集团子目同样有效）──
  'updCoef', 'updConv', 'updSubField',
  // ── T5：派生聚合 / 挂载面板 / gtype 隔离护栏 ──
  'rowGroupSubs', 'rowGroupAgg', 'rowGroupPending', 'groupExportFee', 'groupSubCells', 'groupSubRowHtml', 'updGroupMat',
  // ── T6：T02 四部分汇总预览计算 + 导出 payload 收集 ──
  'buildGroupSummary', 'collectGroupSummaryPayload', 'collectGroupManualFees', 'getGroupSummaryOpts',
  'groupModeBlock',              // F2 防御收口：混合态拦截逻辑断言（restoreProject 接线另为源码级）
  'groupPickerItems', 'groupMatPending', 'openGroupPicker', 'closeGroupPicker', 'renderGroupPicker',
  'groupPickerRetry', 'gpPick',
  'delSub', 'addSub', 'syncRowMat', 'routeRowMat', 'subCategoryScore', 'normKey', 'rowMatPending', 'fmt', 'esc'];

let ctx;
const HEAD = [
  '// 对内引擎状态：模式开关不得触碰',
  'let globalCoef=1.0, globalMgmtRate=10, globalProfitRate=15;',
  '// 内部引擎依赖的库/清单状态（T4 回归夹具用）',
  'let DB={}, benchMap={}, groups=[], uid=1, ALL=[];',
  'let hourlyRate=350, batchMode=false;',
  '// renderBoq/updateSum 用计数器桩：本测试只验开关接线与公式，不跑真实渲染',
  'let _render=0, _sum=0; function renderBoq(){_render++;} function updateSum(){_sum++;}',
  'function toast(m){TOASTS.push(m);}',
  'let RESP={}; let _get=async function(t,p){GETS.push(t); return (RESP[t]||[]).slice();};',
];
function buildSandbox() {
  ctx = vm.createContext({
    console, JSON, Math, Number, parseFloat, parseInt, String, Object, Array, isNaN, Set, Map, Date, RegExp, Promise,
    document, GETS, TOASTS, DOMCFG,
    setTimeout: () => 0,   // 弹窗聚焦等 UI 定时器在沙箱里不执行（只验接线，不验时序）
  });
  vm.runInContext(
    HEAD.join('\n') + '\n' +
    LINES.map(l => grabLine(TOOL, l)).join('\n') + '\n' +
    DECLS.map(d => grabDecl(TOOL, d)).join('\n') + '\n' +
    FNS.map(n => grabAnyFn(TOOL, n)).join('\n'),
    ctx);
}
const run = code => vm.runInContext(code, ctx);
const runA = code => vm.runInContext('(async () => { ' + code + ' })()', ctx);   // 宿主 await 沙箱 promise 可行

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? '  → ' + detail : '')); }
}
const reset = () => { GETS.length = 0; TOASTS.length = 0; };

(async function main() {
buildSandbox();   // 抽取即编译校验：工具函数/声明缺失会在此抛错（RED）

/* ══ 夹具：模拟 group_benchmark_items 两行（甲供未定价 + 已定价），字段照 T1 迁移列 ══ */
const G009 = { code: 'ZS02-A-009', discipline: 'A', section_name: '楼地面工程', name: '瓷砖地面',
  spec: 'SA级600×600', unit: 'm2', work_type: '泥水', lab_price: 61.65,
  mats: [{ name: '瓷砖', price: null, unit: 'm2', consumption: 1.4469 },
         { name: '1:3干硬性水泥砂浆', price: null, unit: 'm3', consumption: 0.0147 }],
  aux_cost: 1.98, mech_cost: 0, is_owner_supply: false, raw_composite: null, source_row: 146 };
const D003 = { code: 'ZS02-D-003', discipline: 'D', section_name: '单价措施项目', name: '成品保护-PVC保护膜',
  spec: '厚2mm', unit: 'm2', work_type: '油漆', lab_price: 1.51,
  mats: [{ name: 'PVC保护膜', price: 2, unit: 'm2', consumption: 0.95 }],
  aux_cost: 0.23, mech_cost: 0, is_owner_supply: false, raw_composite: null, source_row: 300 };
const RULES_SEED = [
  { key: 'mgmt_rate', label: '管理费率', value: 0.17, unit: '×(人工+机械)', kind: 'rate' },
  { key: 'profit_rate', label: '利润率', value: 0.12, unit: '×(人工+机械)', kind: 'rate' },
  { key: 'green_safety_rate', label: '绿色施工安全防护措施费率', value: 0.13, unit: '×∑(分部分项人工+机械)', kind: 'rate' },
  { key: 'lump_sum_rate', label: '预算包干费率', value: 0.03, unit: '×∑(分部分项人工+机械)', kind: 'rate' },
  { key: 'tax_rate', label: '税金率', value: 0.09, unit: '×(一+二+三)', kind: 'rate' },
  { key: 'fitout_coordination_fee', label: '精装修管理及配合费', value: null, unit: '元/m2(装修面积,admin必填)', kind: 'fee' },
  { key: 'overtime_fee', label: '赶工措施费', value: null, unit: '手工金额', kind: 'fee' },
  { key: 'contract_change_fee', label: '合同变更费用', value: null, unit: '手工金额', kind: 'fee' },
  { key: 'inflation_fee', label: '装修类型涨幅费用', value: null, unit: '手工金额', kind: 'fee' },
];
run('var G009 = ' + JSON.stringify(G009) + '; var D003 = ' + JSON.stringify(D003) +
    '; var RULES_SEED = ' + JSON.stringify(RULES_SEED) + ';');

/* ────────────── A. ZS02 库夹具：建 map 后可按 code 查原样行 ────────────── */
console.log('\n── A. groupBenchMap / getGroupBench：表行原样入 map ──');
run('rebuildGroupBenchMap([G009, D003])');
ok('A1 getGroupBench 命中同一对象引用（字段不改名，T4 直接读 lab_price/mats/aux_cost/mech_cost）',
  run('getGroupBench("ZS02-A-009") === G009'));
ok('A2 第二行同样可查', run('getGroupBench("ZS02-D-003") === D003'));
ok('A3 未入库编码返回 null（不是 undefined，调用方只需判 !x）', run('getGroupBench("ZS02-A-999") === null'));
ok('A4 map 键 = code', Object.keys(run('groupBenchMap')).join(',') === 'ZS02-A-009,ZS02-D-003',
  Object.keys(run('groupBenchMap')).join(','));
const matsA = run('getGroupBench("ZS02-A-009").mats');
ok('A5 甲供未定价位 mats[].price 仍是 null（T4「待询价」判据依赖，不能被成 0）',
  matsA.length === 2 && matsA[0].price === null && matsA[1].price === null, JSON.stringify(matsA));
ok('A6 消耗量口径原样保留（1.4469 不四舍五入）', run('getGroupBench("ZS02-A-009").mats[0].consumption') === 1.4469);
ok('A7 groupBenchRows 留有序数组（map 丢序，分部小计/导出要按 code 顺序）',
  run('groupBenchRows.length') === 2 && run('groupBenchRows[0].code') === 'ZS02-A-009');
run('rebuildGroupBenchMap([D003])');
ok('A8 重建不累积脏键（库刷新后旧 code 查不到）',
  run('getGroupBench("ZS02-A-009") === null') && run('Object.keys(groupBenchMap).length') === 1);
run('rebuildGroupBenchMap([])');
ok('A9 空数组入参不抛异常（离线/未建表路径）', run('getGroupBench("ZS02-D-003")') === null);
run('rebuildGroupBenchMap([G009, D003])');   // 还原夹具

/* ────────────── B. 两个 loader 的数据契约 ────────────── */
console.log('\n── B. loadGroupBenchmark / loadGroupPricingRules：表名、兜底解析、失败返回 false ──');
reset();
run('RESP = {group_benchmark_items: [G009, D003]};');
ok('B1 表名逐字 group_benchmark_items', await runA('return loadGroupBenchmark();') === true && GETS[0] === 'group_benchmark_items', JSON.stringify(GETS));
ok('B2 成功后库可查且行原样', run('getGroupBench("ZS02-A-009") === G009'));
ok('B3 loader 自身不动幂等标志（幂等由 ensureGroupData 统一管）', run('groupDataLoaded') === false);
reset();
run('RESP = {};');
ok('B4 未建表/离线：返回 false 并 toast 提示，不抛异常', await runA('return loadGroupBenchmark();') === false);
ok('B5 失败提示点名表名，便于排障', TOASTS.some(t => String(t).includes('group_benchmark_items')), JSON.stringify(TOASTS));
reset();
const G_STR = Object.assign({}, G009, { mats: JSON.stringify(G009.mats) });   // JSONB 以文本回传的兜底场景
run('RESP = {group_benchmark_items: ' + JSON.stringify([G_STR]) + '};');
await runA('return loadGroupBenchmark();');
ok('B6 mats 为 JSON 文本时解析成数组（消费侧只认数组）',
  run('Array.isArray(getGroupBench("ZS02-A-009").mats)') === true && run('getGroupBench("ZS02-A-009").mats.length') === 2);
run('RESP = {group_benchmark_items: [{code:"ZS02-B-001",mats:"{坏JSON"}]};');
await runA('return loadGroupBenchmark();');
ok('B7 mats 非法 JSON → 置空数组而不是崩掉整库', run('getGroupBench("ZS02-B-001").mats.length') === 0);
run('RESP = {group_benchmark_items: [{code:"ZS02-B-002"}]};');
await runA('return loadGroupBenchmark();');
ok('B8 无 mats 字段行兜底为 []', run('Array.isArray(getGroupBench("ZS02-B-002").mats)') && run('getGroupBench("ZS02-B-002").mats.length') === 0);

console.log('\n  · 费率 key → GROUP_RATES 短键映射');
const RATES_DEFAULT = { mgmt: 0.17, profit: 0.12, green: 0.13, baogan: 0.03, tax: 0.09, coordFee: null };
ok('B9 GROUP_RATES 初值即 T01 标准费率六键（离线/未建表时预览口径不变）',
  JSON.stringify(run('GROUP_RATES')) === JSON.stringify(RATES_DEFAULT), JSON.stringify(run('GROUP_RATES')));
ok('B10 断言式复核：mgmt 0.17 且 green 0.13', run('GROUP_RATES.mgmt') === 0.17 && run('GROUP_RATES.green') === 0.13);
reset();
run('RESP = {group_pricing_rules: RULES_SEED};');
ok('B11 表名逐字 group_pricing_rules', await runA('return loadGroupPricingRules();') === true && GETS[0] === 'group_pricing_rules', JSON.stringify(GETS));
ok('B12 五个 rate 键取库值', run('[GROUP_RATES.mgmt,GROUP_RATES.profit,GROUP_RATES.green,GROUP_RATES.baogan,GROUP_RATES.tax].join()') === '0.17,0.12,0.13,0.03,0.09',
  run('[GROUP_RATES.mgmt,GROUP_RATES.profit,GROUP_RATES.green,GROUP_RATES.baogan,GROUP_RATES.tax].join()'));
ok('B13 fee 类 NULL 记为 null 而非 0（coordFee 属 admin 必填拦截项）', run('GROUP_RATES.coordFee') === null);
ok('B14 未识别 key 忽略（手工金额行不进 GROUP_RATES，键数恒为六）', run('Object.keys(GROUP_RATES).length') === 6,
  run('JSON.stringify(Object.keys(GROUP_RATES))'));
reset();
run('RESP = {group_pricing_rules: [{key:"mgmt_rate",value:0.15},{key:"tax_rate",value:0.1}]};');
ok('B15 库值覆盖默认（改库即改口径，前端不写死）', await runA('return loadGroupPricingRules();') === true && run('GROUP_RATES.mgmt') === 0.15 && run('GROUP_RATES.tax') === 0.1);
ok('B16 未下发的键保持原值（profit 仍是 0.12，不会被清空）', run('GROUP_RATES.profit') === 0.12);
reset();
run('RESP = {};');
run('GROUP_RATES.mgmt = 0.15;');
ok('B17 空表：返回 false + toast，且 GROUP_RATES 保持既有值不被清',
  await runA('return loadGroupPricingRules();') === false && run('GROUP_RATES.mgmt') === 0.15 && TOASTS.length >= 1);
run('RESP = {group_pricing_rules: [{key:"fitout_coordination_fee",value:null},{key:"overtime_fee",value:null}]};');
ok('B18 全 NULL 表：返回 false（无有效数值，保留再次触发加载的机会）', await runA('return loadGroupPricingRules();') === false);
run('GROUP_RATES = {mgmt:0.17,profit:0.12,green:0.13,baogan:0.03,tax:0.09,coordFee:null};');   // 复位标准费率
ok('B19 groupRateLabel：0.17 → 17%（禁用提示/后续费率展示用）', run('groupRateLabel(0.17)') === '17%');
ok('B20 groupRateLabel：null → — 而不是 NaN%', run('groupRateLabel(null)') === '—', run('groupRateLabel(null)'));

/* ────────────── C. 懒加载状态机 ────────────── */
console.log('\n── C. 懒加载：内部模式启动零请求，切入 group 才加载，失败可重试、成功幂等 ──');
ok('C1 pricingMode 默认 internal（源码声明原样搬进沙箱）', run('pricingMode') === 'internal');
ok('C2 三个幂等标志初值均 false', run('groupDataLoaded') === false && run('groupBenchLoaded') === false && run('groupRulesLoaded') === false);
reset();
run('RESP = {};');
ok('C3 沙箱求值期未发任何 group 请求（数据只在显式调用时加载）', GETS.length === 0, JSON.stringify(GETS));
const BOOT_ANCHOR = '⚡ 所有数据请求并行加载';
const bootIdx = TOOL.indexOf(BOOT_ANCHOR);
if (bootIdx < 0) throw new Error('未找到启动并行加载块锚点：' + BOOT_ANCHOR);
const bootBlock = TOOL.slice(bootIdx, bootIdx + 700);
ok('C4 页面启动并行加载块未含 group loader / ensureGroupData（内部启动路径零改动）',
  !/loadGroup|ensureGroupData/.test(bootBlock), bootBlock.slice(0, 200));

reset();
run('setPricingMode("group");');
await runA('return ensureGroupData();');
ok('C5 首次切入 group：两张表各请求一次', GETS.filter(t => t === 'group_benchmark_items').length === 1 && GETS.filter(t => t === 'group_pricing_rules').length === 1, JSON.stringify(GETS));
ok('C6 加载失败仍完成模式切换（不回滚 pricingMode，用户看得见数据问题）', run('pricingMode') === 'group' && run('groupDataLoaded') === false);
ok('C7 失败向用户 toast（不静默）', TOASTS.some(t => /集团|基准价|费率/.test(String(t))), JSON.stringify(TOASTS));
reset();
run('setPricingMode("internal"); setPricingMode("group");');
await runA('return ensureGroupData();');
ok('C8 失败后再次触发会重发请求（幂等标志未被误置 true）', GETS.length === 2, JSON.stringify(GETS));
reset();
run('RESP = {group_benchmark_items: [G009, D003], group_pricing_rules: RULES_SEED};');
await runA('return ensureGroupData();');
ok('C9 数据就绪后 groupDataLoaded 置 true', run('groupDataLoaded') === true && run('groupBenchLoaded') === true && run('groupRulesLoaded') === true);
ok('C10 库数据落进 map（getGroupBench 可查 A-009）', run('getGroupBench("ZS02-A-009") === G009'));
reset();
run('setPricingMode("internal");');
run('setPricingMode("group");');
await runA('return ensureGroupData();');
ok('C11 成功后再切不再请求（懒加载幂等，来回切不重复打库）', GETS.length === 0, JSON.stringify(GETS));
reset();
run('groupDataLoaded=false; groupBenchLoaded=false; groupRulesLoaded=false; _groupLoading=null;');
run('setPricingMode("group"); setPricingMode("group"); setPricingMode("group");');
await runA('return ensureGroupData();');
ok('C12 同一轮连点开关只发一组请求（并发去重）', GETS.length === 2, JSON.stringify(GETS));

/* ────────────── D. 开关与对内控件的互斥/污染防线 ────────────── */
console.log('\n── D. setPricingMode：状态迁移 + 管理费/利润输入框 disabled 互斥 + 对内状态零污染 ──');
reset();
run('_render=0; _sum=0;');
run('setPricingMode("group");');
ok('D1 pricingMode === "group"', run('pricingMode') === 'group');
ok('D2 group 模式：管理费/利润输入框同时置灰（17%/12% 由 group_pricing_rules 驱动，不许手填）',
  run('document.getElementById("mgmtRateInp").disabled') === true && run('document.getElementById("profitRateInp").disabled') === true);
ok('D3 两输入框都有解释性 title（点名费率来源）',
  els['mgmtRateInp'].title.includes('group_pricing_rules') && els['profitRateInp'].title.includes('group_pricing_rules'), els['mgmtRateInp'].title);
ok('D4 radio 勾选态跟随（程序化调用也保持一致，且互斥）',
  els['modeGroupInp'].checked === true && els['modeInternalInp'].checked === false);
ok('D5 徽标文案切到「对甲报价」', String(els['pricingModeBadge'].textContent).includes('对甲报价'), els['pricingModeBadge'].textContent);
ok('D6 切换后重渲染清单与总计（renderBoq + updateSum 各一次）', run('_render') === 1 && run('_sum') === 1, 'render=' + run('_render') + ' sum=' + run('_sum'));

run('setPricingMode("internal");');
ok('D7 pricingMode === "internal"', run('pricingMode') === 'internal');
ok('D8 internal 模式：两输入框恢复可编辑（与 D2 互斥）',
  els['mgmtRateInp'].disabled === false && els['profitRateInp'].disabled === false);
ok('D9 radio 恢复「对内成本」勾选', els['modeInternalInp'].checked === true && els['modeGroupInp'].checked === false);
ok('D10 徽标回到「对内成本」', String(els['pricingModeBadge'].textContent).includes('对内成本'));
ok('D11 internal 模式不再触发任何加载（幂等标志已 true，也不该重发）', GETS.length === 0, JSON.stringify(GETS));

const coefBefore = run('globalCoef'), mgmtBefore = run('globalMgmtRate'), profitBefore = run('globalProfitRate');
reset();
run('setPricingMode("group"); setPricingMode("internal");');
ok('D12 模式来回切换不触碰对内公式参数（coef/管理费率/利润率原值）',
  run('globalCoef') === coefBefore && run('globalMgmtRate') === mgmtBefore && run('globalProfitRate') === profitBefore,
  [run('globalCoef'), run('globalMgmtRate'), run('globalProfitRate')].join('/'));
run('document.getElementById("mgmtRateInp"); document.getElementById("profitRateInp");');
els['mgmtRateInp'].value = '10'; els['profitRateInp'].value = '15';
run('setPricingMode("group"); setPricingMode("internal");');
ok('D13 切换不改写两输入框的既有数值（只切 disabled，快照/导出口径不受影响）',
  els['mgmtRateInp'].value === '10' && els['profitRateInp'].value === '15',
  els['mgmtRateInp'].value + '/' + els['profitRateInp'].value);
ok('D14 脏值归一：未知 mode 落回 internal（防 URL/快照带入野值）',
  run('setPricingMode("whatever"), pricingMode') === 'internal');
ok('D15 未知 mode 的输入框状态与 internal 一致（不残留灰态）',
  els['mgmtRateInp'].disabled === false && els['profitRateInp'].disabled === false);
DOMCFG.gone = true;
ok('D16 元素缺失时不抛异常（精简 DOM / 手机版复用同一状态机）',
  run('(function(){ try { setPricingMode("group"); setPricingMode("internal"); return true; } catch(e) { return "throw: " + e.message; } })()') === true);
DOMCFG.gone = false;
run('setPricingMode("group");');
ok('D17 group 模式暴露给 T4：pricingMode/getGroupBench/GROUP_RATES 均为顶层可读写',
  run('pricingMode') === 'group' && typeof run('getGroupBench') === 'function' && run('typeof GROUP_RATES') === 'object');

/* ────────────── E. 评审发现修复：rate 键 NULL 守护（F1）+ 数据到达后补渲染（F2） ────────────── */
console.log('\n── E. rate 键缺失守护（保留 T01 默认 + 判失败可重试）/ 数据到达后补渲染 ──');
const RATE_RESET = 'GROUP_RATES = {mgmt:0.17,profit:0.12,green:0.13,baogan:0.03,tax:0.09,coordFee:null};';
const FLAG_RESET = 'groupDataLoaded=false; groupBenchLoaded=false; groupRulesLoaded=false; _groupLoading=null;';
const tick = () => new Promise(r => setTimeout(r, 0));   // 排空沙箱内 .then 微任务

// F1-1：单个 rate 键被 admin 置 NULL，其余有效
reset();
run(FLAG_RESET + ' ' + RATE_RESET);
run('RESP = {group_pricing_rules: [{key:"mgmt_rate",value:null},{key:"profit_rate",value:0.11},'
  + '{key:"green_safety_rate",value:0.13},{key:"lump_sum_rate",value:0.03},{key:"tax_rate",value:0.09},'
  + '{key:"fitout_coordination_fee",value:null}]};');
ok('E1 rate 键遇 NULL：loader 判失败返回 false（不再「成功加载」地放行）',
  await runA('return loadGroupPricingRules();') === false);
ok('E2 GROUP_RATES.mgmt 保留 T01 默认 0.17，未被库 NULL 覆盖（T4 里管理费不会静默归零）',
  run('GROUP_RATES.mgmt') === 0.17, 'mgmt=' + run('GROUP_RATES.mgmt'));
ok('E3 同批有效 rate 键照常覆盖库值（守护是逐键的，不整批丢弃）', run('GROUP_RATES.profit') === 0.11,
  'profit=' + run('GROUP_RATES.profit'));
ok('E4 缺失 toast 点名缺失键并声明保持 T01 默认',
  TOASTS.some(t => /集团费率缺失/.test(String(t)) && /保持 T01 默认/.test(String(t))), JSON.stringify(TOASTS));
reset();
run(FLAG_RESET + ' ' + RATE_RESET);
run('RESP = {group_benchmark_items: [G009, D003], group_pricing_rules: [{key:"mgmt_rate",value:null}]};');
ok('E5 经整条加载链：一个 rate 键缺失则 loadGroupDataOnce 返回 false，且两个幂等标志均不置位（可重试）',
  (await runA('return loadGroupDataOnce();')) === false && run('groupRulesLoaded') === false && run('groupDataLoaded') === false);
ok('E5b 但基准价库那一组自身成功（分项标志只锁失败的那组）', run('groupBenchLoaded') === true);
run(FLAG_RESET);

// F1-2：NaN 坏值同属「坏值」，与 NULL 同等守护
reset();
run(RATE_RESET);
run('RESP = {group_pricing_rules: [{key:"mgmt_rate",value:0.17},{key:"profit_rate",value:0.12},{key:"green_safety_rate",value:0.13},{key:"lump_sum_rate",value:0.03},{key:"tax_rate",value:"abc"}]};');
ok('E6 rate 键坏值（parseFloat → NaN）：返回 false 且 tax 保持 0.09',
  await runA('return loadGroupPricingRules();') === false && run('GROUP_RATES.tax') === 0.09, 'tax=' + run('GROUP_RATES.tax'));

// F1-3：仅 fee 类允许写 null —— coordFee 为 NULL 不构成缺失
reset();
run(RATE_RESET);
run('RESP = {group_pricing_rules: RULES_SEED};');
ok('E7 五个 rate 键有效 + 仅 coordFee(fee 类) 为 NULL：加载成功且 coordFee 记 null',
  await runA('return loadGroupPricingRules();') === true && run('GROUP_RATES.coordFee') === null && run('GROUP_RATES.mgmt') === 0.17);
ok('E8 GROUP_RATES 六键中无任何 rate 键被写成 null（报价命脉全数值）',
  run('[GROUP_RATES.mgmt,GROUP_RATES.profit,GROUP_RATES.green,GROUP_RATES.baogan,GROUP_RATES.tax].every(function(v){return typeof v === "number" && !isNaN(v);})') === true);

// F2：异步数据到达后补一次渲染
reset();
run(FLAG_RESET + ' ' + RATE_RESET + ' _render=0; _sum=0;');
run('RESP = {group_benchmark_items: [G009, D003], group_pricing_rules: RULES_SEED};');
run('setPricingMode("group");');
ok('E9 首切 group 先同步渲染一次（不阻塞等数据）', run('_render') === 1 && run('_sum') === 1,
  'render=' + run('_render') + ' sum=' + run('_sum'));
await runA('return ensureGroupData();');
await tick();
ok('E10 数据真正到达后 renderBoq 与 updateSum 各被再调一次（清单不再停在「数据未到」）',
  run('_render') === 2 && run('_sum') === 2, 'render=' + run('_render') + ' sum=' + run('_sum'));
ok('E11 补渲染发生在数据就绪之后：groupDataLoaded 已 true', run('groupDataLoaded') === true);

reset();
run(FLAG_RESET + ' _render=0; _sum=0;');
run('RESP = {};');
run('setPricingMode("group");');
await runA('return ensureGroupData();');
await tick();
ok('E12 加载失败不补渲染（避免无数据的空重排；失败仍只保留首轮那一次）',
  run('_render') === 1 && run('_sum') === 1, 'render=' + run('_render') + ' sum=' + run('_sum'));

run('setPricingMode("internal");');

/* ═══════════ F. Task 4：集团公式引擎 + subs 契约 ═══════════ */
console.log('\n── F. groupSubPrice / addGroupSub / 行级 group 分支（黄金值 4.0779 · 81.5085）──');
function near(name, a, b, tol) {
  const good = typeof a === 'number' && isFinite(a) && Math.abs(a - b) <= (tol === undefined ? 1e-9 : tol);
  if (good) { pass++; console.log('  ✓ ' + name + ' = ' + a); }
  else { fail++; console.log('  ✗ ' + name + '  → 实得 ' + JSON.stringify(a) + ' / 期望 ' + b + ' (tol ' + (tol === undefined ? 1e-9 : tol) + ')'); }
}
run(RATE_RESET + ' globalCoef=1.0; batchMode=false; hourlyRate=350;');
run('rebuildGroupBenchMap([G009, D003]);');

/* ── F① groupSubPrice：黄金值 + 分量 + 基数口径 ── */
run(`var S_D003 = {gtype:'group', coef:1, conv:1, lab:1.51, aux:0.23, mech:0,
  mats:[{name:'PVC保护膜', price:2, unit:'m2', consumption:0.95}]};`);
const PD = run('(function(){var p=groupSubPrice(S_D003);return JSON.stringify(p);})()');
ok('F1 groupSubPrice 返回八字段契约 {h,lab,mat,aux,mech,mgmt,profit,pending}',
  JSON.stringify(Object.keys(JSON.parse(PD)).sort()) === JSON.stringify(['aux', 'h', 'lab', 'mat', 'mech', 'mgmt', 'pending', 'profit']), PD);
ok('F2 D-003 已定价：pending=false', run('groupSubPrice(S_D003).pending') === false, PD);
near('F2b D-003 黄金值 h=1.51+2×0.95+0.23+0+(1.51+0)×.17+(1.51+0)×.12', run('groupSubPrice(S_D003).h'), 4.0779, 0.001);
near('F3 分量 lab', run('groupSubPrice(S_D003).lab'), 1.51);
near('F4 分量 mat = Σ(price×consumption) 消耗量口径（2×0.95、不乘损耗率/换算）', run('groupSubPrice(S_D003).mat'), 1.9);
near('F5 分量 aux（D 辅材）', run('groupSubPrice(S_D003).aux'), 0.23);
near('F6 分量 mech（E 机械）', run('groupSubPrice(S_D003).mech'), 0);
near('F7 分量 mgmt = (lab+mech)×0.17', run('groupSubPrice(S_D003).mgmt'), 0.2567);
near('F8 分量 profit = (lab+mech)×0.12', run('groupSubPrice(S_D003).profit'), 0.1812);
near('F9 勾稽：h = lab+mat+aux+mech+mgmt+profit', run('(function(){var p=groupSubPrice(S_D003);return p.h-(p.lab+p.mat+p.aux+p.mech+p.mgmt+p.profit);})()'), 0, 1e-12);

console.log('\n  · pending 判据：存在 price:null 才待询价');
run(`var S_A009 = {gtype:'group', coef:1, conv:1, lab:61.65, aux:1.98, mech:0,
  mats:[{name:'瓷砖', price:null, unit:'m2', consumption:1.4469},
        {name:'1:3干硬性水泥砂浆', price:null, unit:'m3', consumption:0.0147}]};`);
ok('F10 A-009 甲供未定价 → pending=true', run('groupSubPrice(S_A009).pending') === true);
near('F10b pending 时 h 仍按甲供 0 计（仅供显示，行价另判）：黄金值 81.5085', run('groupSubPrice(S_A009).h'), 81.5085, 0.001);
ok('F11 mats==[]（源表「——」已入导入过滤）是合法常态 → 不 pending',
  run('groupSubPrice({gtype:\'group\',lab:1,aux:0,mech:0,mats:[]}).pending') === false);
ok('F12 price=0 是有效价 → 不 pending（与「未询价」不同义）',
  run('groupSubPrice({gtype:\'group\',lab:1,aux:0,mech:0,mats:[{price:0,consumption:2}]}).pending') === false &&
  run('groupSubPrice({gtype:\'group\',lab:1,aux:0,mech:0,mats:[{price:0,consumption:2}]}).mat') === 0);
ok('F13 多主材其一 null → pending（整条子目不许半套价）',
  run('groupSubPrice({gtype:\'group\',lab:1,aux:0,mech:0,mats:[{price:5,consumption:1},{price:null,consumption:1}]}).pending') === true);
ok('F14 mats 缺字段/非数组 → 不抛异常且不 pending（库行兜底 [] 后仍可用）',
  run('(function(){try{return groupSubPrice({lab:1,aux:0,mech:0}).pending===false && groupSubPrice({lab:1,mats:"坏字符串"}).pending===false;}catch(e){return "throw:"+e.message;}})()') === true);

console.log('\n  · 费率不写死：GROUP_RATES 驱动 + 基数只认人工+机械');
run('GROUP_RATES.mgmt = 0.15;');
near('F15 mgmt 改库值 0.15 即随行变（前端不硬编码 17）', run('groupSubPrice(S_D003).mgmt'), 1.51 * 0.15);
near('F15b h 同步变为 4.0477', run('groupSubPrice(S_D003).h'), 4.0477, 0.001);
run(RATE_RESET);
near('F15c 复位 0.17 后 h 回到黄金值', run('groupSubPrice(S_D003).h'), 4.0779, 0.001);
run(`var S_MECH = {gtype:'group', coef:1, conv:1, lab:1.51, aux:0.23, mech:10, mats:[{price:2,consumption:0.95}]};`);
near('F16 管理费基数 = 人工+机械（主材/辅材不进基数）', run('groupSubPrice(S_MECH).mgmt'), (1.51 + 10) * 0.17);
near('F16b 利润基数同', run('groupSubPrice(S_MECH).profit'), (1.51 + 10) * 0.12);

/* ── F② 行级：rowUnitPrice / rowTotal / compUnitPrice 的 group 分支 ── */
run(`function _mkRows() {
  groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[]}]}];
  uid = 100;
  var rg = makeRow({name:'瓷砖地面对甲', unit:'m2', qty:'3'});        // id 100
  var rd = makeRow({name:'成品保护对甲', unit:'m2', qty:'10'});       // id 101
  var ru = makeRow({name:'单位不一致行', unit:'m', qty:'1'});         // id 102
  var r2 = makeRow({name:'平方米行', unit:'㎡', qty:'1'});            // id 103
  var ru2 = makeRow({name:'批量行', unit:'m2', qty:'1'});             // id 104
  var ri = makeRow({name:'石材墙面（内部夹具）', unit:'m2', qty:'3'}); // id 105
  ri.auxCost = 5; ri.matPrice = 100; ri.matName = '石材';
  ri.subs = [
    {bid:'NS-020', bsh:'泥水班组', coef:2.0, conv:1.5, matName:'石材', matPrice:100, wasteRate:3},
    {bid:'NS-030', bsh:'泥水班组', coef:1.0, conv:1.0, matName:'', matPrice:20, wasteRate:0}
  ];
  groups[0].sections[0].rows = [rg, rd, ru, r2, ru2, ri];
  rebuildRowMap();
}`);
run('pricingMode = "group";');
run('_mkRows();');
ok('F17 group 模式无子目 → 行单价 null（同内部「未套价」语义）', run('rowUnitPrice(findRow(100))') === null);
run('addGroupSub(100, "ZS02-D-003"); addGroupSub(101, "ZS02-D-003"); addGroupSub(100, "ZS02-A-009");');
ok('F18 挂载后 subs 长度 2（D-003 + A-009）', run('findRow(100).subs.length') === 2);
ok('F19 任一子目 pending → 整行单价 null（不拼假值）', run('rowUnitPrice(findRow(100))') === null);
ok('F20 行合价同步 0（pending 不计假值）', run('rowTotal(findRow(100))') === 0);
near('F21 行单价 = Σ h×coef×conv（单子目 D-003）', run('rowUnitPrice(findRow(101))'), 4.0779, 0.001);
run('updCoef(101, "ZS02-D-003", "ZS02-D", "2"); updConv(101, "ZS02-D-003", "ZS02-D", "1.5");');
near('F22 coef=2 × conv=1.5 参与行单价（子目级系数/换算复用 updCoef/updConv）',
  run('rowUnitPrice(findRow(101))'), 4.0779 * 2 * 1.5, 0.001);
near('F23 行合价 = 行单价 × qty（qty=10）', run('rowTotal(findRow(101))'), 4.0779 * 2 * 1.5 * 10, 0.005);
near('F24 综合单价 = 行单价（h 已含管理费/利润，不叠加内部 mgmt/profit 与行主材费）',
  run('compUnitPrice(findRow(101))'), run('rowUnitPrice(findRow(101))'), 0.001);
ok('F24b 且不等于内部加成值（10%/15% 未乘上）', run('compUnitPrice(findRow(101)) < rowUnitPrice(findRow(101)) * 1.2') === true);
run('findRow(101).hourlyMode = true;');
near('F25 时工模式在 group 下被忽略（group 分支先于 hourlyMode 判定，不吃 hourlyRate）',
  run('rowUnitPrice(findRow(101))'), 4.0779 * 2 * 1.5, 0.001);
run('findRow(101).hourlyMode = false; globalCoef = 2;');
near('F26 内部人工系数 globalCoef 不污染集团行价', run('rowUnitPrice(findRow(101))'), 4.0779 * 2 * 1.5, 0.001);
run('globalCoef = 1.0;');
run('findRow(100).subs[1].mats = [{price:100, consumption:1.4469}, {price:300, consumption:0.0147}];');
near('F27 甲供补齐价后整行出数：h(A-009)=230.6085 ×1 + h(D-003)=4.0779 ×1',
  run('rowUnitPrice(findRow(100))'), 230.6085 + 4.0779, 0.001);
ok('F28 补齐后 pending 消除', run('groupSubPrice(findRow(100).subs[1]).pending') === false);
run('findRow(100).subs.push({bid:"NS-020", bsh:"泥水班组", coef:1, conv:1, matName:"石材", matPrice:100, wasteRate:3});');
near('F29 混合行（内部子目 + 集团子目）group 模式只认集团子目，内部子目 h=0 不双计',
  run('rowUnitPrice(findRow(100))'), 230.6085 + 4.0779, 0.001);
run('_mkRows();');

/* ── F③ addGroupSub 契约 ── */
console.log('\n  · addGroupSub：字段映射 / 深拷贝 / 拦截 / 单位 toast');
reset();
run('batchMode=false; _render=0;');
ok('F30 挂载成功返回 true 且展开行（r.open=true）、触发一次 renderBoq',
  run('addGroupSub(102, "ZS02-D-003")') === true && run('findRow(102).open') === true && run('_render') === 1);
const GSUB = JSON.parse(run('JSON.stringify(findRow(102).subs[0])'));
ok('F31 字段映射表→sub：bid=code / bsh=\'ZS02-\'+discipline / gtype=\'group\' / coef=conv=1.0',
  GSUB.bid === 'ZS02-D-003' && GSUB.bsh === 'ZS02-D' && GSUB.gtype === 'group' && GSUB.coef === 1.0 && GSUB.conv === 1.0,
  JSON.stringify(GSUB));
ok('F32 workType/lab/aux/mech 取自表行（work_type/lab_price/aux_cost/mech_cost）',
  GSUB.workType === '油漆' && GSUB.lab === 1.51 && GSUB.aux === 0.23 && GSUB.mech === 0, JSON.stringify(GSUB));
ok('F33 sub 字段全集 = 契约八字段（不多不少：无 matPrice/wasteRate 等内部字段）',
  JSON.stringify(Object.keys(GSUB).sort()) === JSON.stringify(['aux', 'bid', 'bsh', 'coef', 'conv', 'gtype', 'lab', 'mats', 'mech', 'workType'].sort()),
  JSON.stringify(Object.keys(GSUB)));
ok('F34 bsh 随 discipline：A 类挂 ZS02-A', run('addGroupSub(100,"ZS02-A-009"), findRow(100).subs[0].bsh') === 'ZS02-A');
ok('F35 mats 深拷贝：值与库行一致但不是同一引用',
  run('findRow(100).subs[0].mats[0].price === G009.mats[0].price') === true &&
  run('findRow(100).subs[0].mats === G009.mats') === false &&
  run('findRow(100).subs[0].mats[0] === G009.mats[0]') === false);
run('findRow(100).subs[0].mats[0].price = 88;');
ok('F36 修改 sub.mats 不反写库行（getGroupBench 仍为原值，不脏化基准价库）',
  run('G009.mats[0].price') === null && run('getGroupBench("ZS02-A-009").mats[0].price') === null, 'G009.mats[0].price=' + run('G009.mats[0].price'));
run('_mkRows();');
reset();
ok('F37 重复挂载拦截：首次 true、第二次 false 且不新增',
  run('addGroupSub(102,"ZS02-D-003")') === true &&
  run('addGroupSub(102,"ZS02-D-003")') === false && run('findRow(102).subs.length') === 1);
ok('F38 拦截 toast 沿用 addSub 文案「该子目已添加」', TOASTS.some(t => String(t).includes('该子目已添加')), JSON.stringify(TOASTS));
run('_mkRows();');   // F37 在 102 上留了子目，重建后才验得出「未知 code 不写空 sub」
reset();
ok('F39 未知 code：返回 false + 点名 toast，不写空 sub',
  run('addGroupSub(102,"ZS02-A-999")') === false && run('findRow(102).subs.length') === 0 &&
  TOASTS.some(t => String(t).includes('ZS02-A-999')), JSON.stringify(TOASTS));
ok('F40 不存在的 rid：返回 false 不抛', run('(function(){try{return addGroupSub(9999,"ZS02-D-003");}catch(e){return "throw:"+e.message;}})()') === false);
reset();
run('_mkRows(); addGroupSub(102, "ZS02-D-003");');
ok('F41 单位不一致 toast（行 m / 表 m2）沿用 addSub 语义',
  TOASTS.some(t => /单位不一致/.test(String(t)) && /换算系数/.test(String(t))), JSON.stringify(TOASTS));
reset();
run('addGroupSub(103, "ZS02-D-003");');
ok('F42 ㎡/m2 归一化后不误报警（同 addSub L1096 做法）',
  !TOASTS.some(t => /单位不一致/.test(String(t))) && TOASTS.some(t => String(t).includes('子目已挂载')), JSON.stringify(TOASTS));
reset();
run('_mkRows(); findRow(101).matPrice = 500; findRow(101).matName = "PVC膜"; addGroupSub(101, "ZS02-D-003");');
ok('F43 不走 syncRowMat：集团子目无 matPrice 字段，行级暂存价不被分配（主材价只存 mats[].price）',
  run('findRow(101).subs[0].matPrice') === undefined && run('findRow(101).matPrice') === 500);
reset();
run('batchMode = true; _render=0; addGroupSub(105, "ZS02-D-003");');
ok('F44 batchMode 抑制 toast/render（沿用 addSub 批量语义）', run('_render') === 0 && TOASTS.length === 0, JSON.stringify(TOASTS));
run('batchMode = false; findRow(105).subs = [];');
reset();
run('addGroupSub(102, "ZS02-D-003");');   // F44 的 batchMode 与后续 _mkRows 会重建行，这里重新挂一次
ok('F45 挂载后 updSubField/updCoef 按 bid+bsh 可定位（既有处理器零改动复用）',
  run('updCoef(102,"ZS02-D-003","ZS02-D","3"), findRow(102).subs[0].coef') === 3 &&
  run('updSubField(102,"ZS02-D-003","ZS02-D","lab","2.5"), findRow(102).subs[0].lab') === '2.5');
run('_mkRows();');

/* ── F④ 内部公式回归双夹具：同数据 internal 模式逐分不变 ── */
console.log('\n  · 内部公式回归双夹具（qty=3 / coef=2 / conv=1.5 / 损耗 3%）');
run('setPricingMode("internal");');
run(`DB = { '泥水班组': [
  {id:'NS-020', name:'墙面铺贴-石材', unit:'m2', price:120, waste_rate:3, auxType:'', auxFixedK:0, auxRateDetail:null},
  {id:'NS-030', name:'墙面基层-抹灰', unit:'m2', price:28,  waste_rate:0, auxType:'', auxFixedK:0, auxRateDetail:null}
]};`);
run('rebuildBenchMap();');
ok('F46 internal 模式入口：pricingMode 已切回', run('pricingMode') === 'internal');
near('F47 夹具行 rowUnitPrice = 120×2×1×1.5 + 28×1×1×1 = 388（原 effPrice 口径）', run('rowUnitPrice(findRow(105))'), 388);
near('F48 夹具行 rowMatCost = 100×1.03×2×1.5 + 20×1×1 = 329', run('rowMatCost(findRow(105))'), 329);
near('F49 夹具行 compUnitPrice = 388+329+5+38.8+58.2 = 819（管 10%/利 15% 基数=人工）', run('compUnitPrice(findRow(105))'), 819);
near('F50 夹具行 rowTotal = (388+329+5+38.8+58.2)×3 = 2457', run('rowTotal(findRow(105))'), 2457);
const SNAP_I = run('JSON.stringify([rowUnitPrice(findRow(105)),rowMatCost(findRow(105)),compUnitPrice(findRow(105)),rowTotal(findRow(105))])');
run('addGroupSub(105, "ZS02-D-003");');
const SNAP_G = run('JSON.stringify([rowUnitPrice(findRow(105)),rowMatCost(findRow(105)),compUnitPrice(findRow(105)),rowTotal(findRow(105))])');
ok('F51 双夹具②：同一行挂上集团子目后，internal 三件套数值逐分不变（内部语句未被改写）',
  SNAP_I === SNAP_G, SNAP_I + ' vs ' + SNAP_G);
ok('F52 internal 时工分支仍生效（group 守卫在 internal 下不拦路）：单价 = hourlyRate',
  run('findRow(105).hourlyMode = true, rowUnitPrice(findRow(105))') === 350);
run('findRow(105).hourlyMode = false;');
ok('F53 internal 无子目仍返回 null', run('_mkRows(), rowUnitPrice(findRow(100))') === null);
ok('F54 内部子目 gtype 缺省（不被 addGroupSub 契约污染）', run('findRow(105).subs.every(function(s){return s.gtype === undefined || s.gtype === "group";})') === true);
run('findRow(105).subs = [];');
const rtNullQty = run('(function(){var r=findRow(105);r.qty="abc";return rowTotal(r);})()');
ok('F55 internal 脏 qty 行为原样保留（qty 非数 → 合价 NaN，group 守卫未改写内部语义）',
  Number.isNaN(rtNullQty) === true, 'rowTotal=' + rtNullQty);
run('_mkRows();');

/* ── F⑤ 提示条：数字从 GROUP_RATES 动态取 ── */
console.log('\n  · 管理费/利润旁提示条（数字取自 GROUP_RATES，不硬编码）');
DOMCFG.gone = true;
ok('F56 提示条元素缺失不抛（精简 DOM）',
  run('(function(){try{updateGroupRateHint();return true;}catch(e){return "throw:"+e.message;}})()') === true);
DOMCFG.gone = false;
run('setPricingMode("internal");');
ok('F57 internal 模式提示条隐藏', els['groupRateHint'].style.display === 'none', JSON.stringify(els['groupRateHint'].style));
run('setPricingMode("group");');
ok('F58 group 模式提示条可见且文案含写死口径',
  els['groupRateHint'].style.display !== 'none' && /基数=人工\+机械（写死）/.test(els['groupRateHint'].textContent),
  els['groupRateHint'].textContent);
ok('F59 标准费率下显示 17% / 12%',
  /管理17%\/利润12%/.test(els['groupRateHint'].textContent), els['groupRateHint'].textContent);
run('GROUP_RATES.mgmt = 0.15; GROUP_RATES.profit = 0.11; setPricingMode("group");');
ok('F60 费率变化后文案随行（含 15%/11%、不再含 17%）',
  /管理15%\/利润11%/.test(els['groupRateHint'].textContent) && !/17%/.test(els['groupRateHint'].textContent),
  els['groupRateHint'].textContent);
run(FLAG_RESET + ' ' + RATE_RESET);
run('RESP = {group_benchmark_items:[G009,D003], group_pricing_rules:[{key:"mgmt_rate",value:0.16},{key:"profit_rate",value:0.12},{key:"green_safety_rate",value:0.13},{key:"lump_sum_rate",value:0.03},{key:"tax_rate",value:0.09}]};');
run('setPricingMode("group");');
await runA('return ensureGroupData();');
await tick();
ok('F61 库费率落地后提示条同步刷新（不停在 T01 默认值）',
  /管理16%/.test(els['groupRateHint'].textContent), els['groupRateHint'].textContent);
run('setPricingMode("internal"); groupDataLoaded=false; groupBenchLoaded=false; groupRulesLoaded=false; _groupLoading=null; ' + RATE_RESET);

/* ═══════════ G. Task 5：行渲染派生单元格 + 待询价态 + ZS02 挂载面板 + gtype 护栏 ═══════════ */
console.log('\n── G. rowGroupAgg / groupSubCells / updGroupMat / groupPicker / EXP_COLS group 分支 / 护栏 ──');
run(RATE_RESET + ' globalCoef=1.0; batchMode=false; hourlyRate=350;');
run('rebuildGroupBenchMap([G009, D003]);');
run('pricingMode = "group";');
run('_mkRows(); addGroupSub(100, "ZS02-D-003"); addGroupSub(100, "ZS02-A-009");');   // 一行：已定价 + 甲供未定价

/* ── G① rowGroupAgg：契约 + 待询价判定 ── */
const AGG_KEYS = run('Object.keys(rowGroupAgg(findRow(100))).sort().join(",")');
ok('G1 rowGroupAgg 返回八字段契约 {lab,mat,aux,mech,mgmt,profit,unit,ready}',
  AGG_KEYS === 'aux,lab,mat,mech,mgmt,profit,ready,unit', AGG_KEYS);
ok('G2 任一子目 pending → ready:false 且 unit:null（行不拼假值）',
  run('(function(){var a=rowGroupAgg(findRow(100));return a.ready===false&&a.unit===null;})()') === true);
ok('G2b rowGroupPending(r)===true（渲染层据此挂黄底 +「待询价」徽标）', run('rowGroupPending(findRow(100))') === true);
near('G3 待询价时分量仍按已知值累计（子目行要显示各自的 A/D/E/F/G）：lab=1.51+61.65', run('rowGroupAgg(findRow(100)).lab'), 1.51 + 61.65);
near('G3b mat 只含已定价部分（D-003：2×0.95）', run('rowGroupAgg(findRow(100)).mat'), 1.9);
near('G3c aux=0.23+1.98', run('rowGroupAgg(findRow(100)).aux'), 0.23 + 1.98);

console.log('\n  · 补齐甲供价后出数：各分量精确断言');
run('findRow(100).subs[1].mats = [{name:"瓷砖",price:100,unit:"m2",consumption:1.4469},{name:"1:3干硬性水泥砂浆",price:300,unit:"m3",consumption:0.0147}];');
ok('G4 补齐甲供价 → ready:true', run('rowGroupAgg(findRow(100)).ready') === true);
ok('G4b 待询价消除', run('rowGroupPending(findRow(100))') === false);
near('G4c unit = Σ h×coef×conv（与 groupRowUnitPrice 同值）', run('rowGroupAgg(findRow(100)).unit'), run('groupRowUnitPrice(findRow(100))'), 1e-9);
near('G4d lab = 1.51 + 61.65', run('rowGroupAgg(findRow(100)).lab'), 63.16, 1e-9);
near('G4e mat = 2×0.95 + 100×1.4469 + 300×0.0147（消耗量口径）', run('rowGroupAgg(findRow(100)).mat'), 2 * 0.95 + 100 * 1.4469 + 300 * 0.0147, 1e-9);
near('G4f aux = 0.23 + 1.98', run('rowGroupAgg(findRow(100)).aux'), 2.21, 1e-9);
near('G4g mech = 0', run('rowGroupAgg(findRow(100)).mech'), 0, 1e-12);
near('G4h mgmt = (Σlab+Σmech)×0.17', run('rowGroupAgg(findRow(100)).mgmt'), 63.16 * 0.17, 1e-9);
near('G4i profit = (Σlab+Σmech)×0.12', run('rowGroupAgg(findRow(100)).profit'), 63.16 * 0.12, 1e-9);
near('G4j 勾稽：unit = lab+mat+aux+mech+mgmt+profit',
  run('(function(){var a=rowGroupAgg(findRow(100));return a.unit-(a.lab+a.mat+a.aux+a.mech+a.mgmt+a.profit);})()'), 0, 1e-9);

run('_mkRows(); addGroupSub(101, "ZS02-D-003");');
run('updCoef(101, "ZS02-D-003", "ZS02-D", "2"); updConv(101, "ZS02-D-003", "ZS02-D", "1.5");');
near('G5 子目 coef×conv 参与聚合：lab = 1.51×3', run('rowGroupAgg(findRow(101)).lab'), 1.51 * 3, 1e-9);
near('G5b mgmt = (1.51×0.17)×3', run('rowGroupAgg(findRow(101)).mgmt'), 1.51 * 0.17 * 3, 1e-9);
near('G5c unit = 4.0779×3', run('rowGroupAgg(findRow(101)).unit'), 4.0779 * 3, 0.001);

console.log('\n  · 「未套集团价」判定（group 模式不得显示 0.00 误导）');
run('_mkRows();');
ok('G6 纯内部子目行（subs 无 gtype）→ ready:false 且 unit:null',
  run('(function(){var a=rowGroupAgg(findRow(105));return a.ready===false&&a.unit===null;})()') === true,
  run('JSON.stringify(rowGroupAgg(findRow(105)))'));
ok('G6b 且不算待询价（rowGroupPending false）——渲染层据此显示「—」而不是「待询价」', run('rowGroupPending(findRow(105))') === false);
near('G6c 内部子目在集团口径无值可汇 → 分量 0', run('rowGroupAgg(findRow(105)).lab'), 0, 1e-12);
ok('G6d 无子目行 → ready:false', run('rowGroupAgg(findRow(100)).ready') === false && run('rowGroupSubs(findRow(100)).length') === 0);
run('_mkRows(); addGroupSub(105, "ZS02-D-003");');
ok('G7 混合行（内部子目 + 集团子目）只聚合集团子目', run('(function(){var a=rowGroupAgg(findRow(105));return a.ready===true&&Math.abs(a.lab-1.51)<1e-12;})()') === true);
near('G7b unit = 集团子目 h（内部子目不双计）', run('rowGroupAgg(findRow(105)).unit'), 4.0779, 0.001);
run('GROUP_RATES.mgmt = 0.15;');
near('G7c 费率驱动：改 GROUP_RATES 聚合随行（不硬编码 17%）', run('rowGroupAgg(findRow(105)).mgmt'), 1.51 * 0.15, 1e-9);
run(RATE_RESET + ' _mkRows();');

/* ── G② COLS（EXP_COLS）管理费/利润列：group 取 rowGroupAgg，internal 表达式原样 ── */
console.log('\n  · EXP_COLS 管理费/利润列的模式分支');
run('addGroupSub(105, "ZS02-D-003"); pricingMode="group"; globalMgmtRate=10; globalProfitRate=15;');
near('G8 group 模式 mgmt 列 = rowGroupAgg(r).mgmt（不乘 globalMgmtRate）',
  run('EXP_COLS.find(function(c){return c.key==="mgmt"}).get(findRow(105))'), 1.51 * 0.17, 1e-9);
near('G8b group 模式 profit 列 = rowGroupAgg(r).profit',
  run('EXP_COLS.find(function(c){return c.key==="profit"}).get(findRow(105))'), 1.51 * 0.12, 1e-9);
run('_mkRows(); addGroupSub(100, "ZS02-A-009");');
near('G8c 待询价行导出 mgmt = 0（ready:false 不放假值，与 rowTotal 同口径）',
  run('EXP_COLS.find(function(c){return c.key==="mgmt"}).get(findRow(100))'), 0, 1e-12);
near('G8d 未套集团价行导出 mgmt = 0', run('EXP_COLS.find(function(c){return c.key==="mgmt"}).get(findRow(101))'), 0, 1e-12);
run('_mkRows(); pricingMode="internal";');
near('G8e internal 模式表达式原样保留：(rowUnitPrice||0)×10%',
  run('EXP_COLS.find(function(c){return c.key==="mgmt"}).get(findRow(105))'), 388 * 0.1, 1e-9);
near('G8f internal profit 列同（×15%）', run('EXP_COLS.find(function(c){return c.key==="profit"}).get(findRow(105))'), 388 * 0.15, 1e-9);
run('pricingMode="group";');

/* ── G③ groupSubCells：集团子目派生单元格（name 来自 getGroupBench，不走 getBench） ── */
console.log('\n  · groupSubCells：集团子目单元格派生值');
run('_mkRows(); addGroupSub(100, "ZS02-A-009");');
const CELLS = JSON.parse(run('JSON.stringify(groupSubCells(findRow(100).subs[0]))'));
ok('G9 code/bsh 与 sub 一致（派生视图定位回子目靠 bid+bsh）', CELLS.code === 'ZS02-A-009' && CELLS.bsh === 'ZS02-A', JSON.stringify(CELLS));
ok('G9b name/spec/unit/section 取自 getGroupBench 库行',
  CELLS.name === '瓷砖地面' && CELLS.spec === 'SA级600×600' && CELLS.unit === 'm2' && CELLS.section === '楼地面工程');
ok('G9c 工种取 sub.workType（源自表行 work_type）', CELLS.workType === '泥水', CELLS.workType);
ok('G9d 主材逐条：name×consumption 原样，未定价位 pending + 文案「甲供待询价」',
  CELLS.mats.length === 2 && CELLS.mats[0].consumption === 1.4469 && CELLS.mats[0].pending === true &&
  CELLS.mats[0].label === '甲供待询价' && CELLS.mats[0].cost === 0, JSON.stringify(CELLS.mats));
ok('G9e 整条 pending 且 h/lab/aux 分量齐备',
  CELLS.pending === true && CELLS.lab === 61.65 && CELLS.aux === 1.98 && CELLS.mech === 0 && CELLS.h === 81.5085,
  JSON.stringify([CELLS.lab, CELLS.h]));
run('findRow(100).subs[0].mats[0].price = 100;');
const CELLS2 = JSON.parse(run('JSON.stringify(groupSubCells(findRow(100).subs[0]))'));
ok('G9f 已定价位：pending:false、price/cost 出数（100×1.4469）',
  CELLS2.mats[0].pending === false && CELLS2.mats[0].price === 100 && Math.abs(CELLS2.mats[0].cost - 144.69) < 1e-9,
  JSON.stringify(CELLS2.mats[0]));
ok('G9g 其一未定价 → 整条 pending（不半套价）', CELLS2.pending === true);
ok('G9h mats 非数组 / 缺字段 → 视图 [] 且不抛（T3 遗留守卫）',
  run('(function(){try{return groupSubCells({gtype:"group",bid:"ZS02-X",mats:"坏字符串"}).mats.length===0 && groupSubCells({gtype:"group",bid:"ZS02-X"}).mats.length===0;}catch(e){return "throw:"+e.message;}})()') === true);
ok('G9i rowGroupAgg 对 mats 非数组子目不抛（消费处同守卫）',
  run('(function(){try{var r={id:9,subs:[{gtype:"group",bid:"ZS02-A-009",bsh:"ZS02-A",lab:1,aux:0,mech:0,mats:"坏字符串"}]};var a=rowGroupAgg(r);return a.ready===true&&a.lab===1;}catch(e){return "throw:"+e.message;}})()') === true);
// T8 核对（T3 遗留 mats 非数组）：脏 mats 的唯一语义 = 兜空数组（mat 0、不算待询价，与 T3 导入过滤
// 「——」后 mats==[] 为常态同口径）；填价入口 updGroupMat 直接拒写（Array.isArray 闸），不猜结构
ok('G9j mats 非数组脏值全链不抛：groupSubPrice 兜 []（mat 0 / pending false / h 只剩人工+管理利润），updGroupMat 拒写返回 false',
  run('(function(){try{var s={gtype:"group",bid:"ZS02-A-009",bsh:"ZS02-A",lab:1,aux:0,mech:0,mats:"[{\\"price\\":null}]"};var p=groupSubPrice(s);return p.pending===false&&p.mat===0&&Math.abs(p.h-1.29)<1e-9;}catch(e){return "throw:"+e.message;}})()') === true &&
  run('(function(){_mkRows(); addGroupSub(100,"ZS02-A-009"); findRow(100).subs[0].mats="坏字符串"; return updGroupMat(100,"ZS02-A-009","ZS02-A",0,"100")===false;})()') === true);

/* ── G④ updGroupMat：甲供待询价 → 填价 → 出数 ── */
console.log('\n  · updGroupMat：待询价的唯一填价入口');
run('_mkRows(); addGroupSub(100, "ZS02-A-009");');
reset(); run('_render=0;');
ok('G10 填入第 0 条主材价 → 数值写进 mats[0].price',
  run('updGroupMat(100,"ZS02-A-009","ZS02-A",0,"100"), findRow(100).subs[0].mats[0].price') === 100);
ok('G10b 只填一条仍 pending（整条子目不许半套价）', run('rowGroupPending(findRow(100))') === true);
run('_render=0;');
ok('G10c updGroupMat 写值后重渲染（沿用 updSubField 同款刷新链路）',
  run('updGroupMat(100,"ZS02-A-009","ZS02-A",1,"300"), _render') === 1);
ok('G10d 补齐 → rowGroupAgg.ready true', run('rowGroupAgg(findRow(100)).ready') === true);
ok('G10e 清空回到待询价（空串 → null，而不是 0：0 是有效报价）',
  run('updGroupMat(100,"ZS02-A-009","ZS02-A",1,""), findRow(100).subs[0].mats[1].price') === null &&
  run('rowGroupPending(findRow(100))') === true);
ok('G10f 脏值（非数）同样落回 null，不产生 NaN 价',
  run('updGroupMat(100,"ZS02-A-009","ZS02-A",1,"abc"), findRow(100).subs[0].mats[1].price') === null);
ok('G10g 库行不被反写（getGroupBench 仍为原值）', run('G009.mats[0].price') === null);
ok('G10h 越界 idx / 非集团子目 → false 不抛',
  run('updGroupMat(100,"ZS02-A-009","ZS02-A",9,"1")') === false &&
  run('updGroupMat(100,"NS-020","泥水班组",0,"1")') === false);

/* ── G⑤ gtype 隔离护栏 ── */
console.log('\n  · gtype 隔离护栏：含集团子目的行一律跳过 syncRowMat');
run('_mkRows(); addGroupSub(101, "ZS02-D-003"); findRow(101).matPrice = 500; findRow(101).matName = "PVC膜";');
run('syncRowMat(101);');
ok('G11 唯一子目是集团子目：syncRowMat 不写 groupSub.matPrice（八字段契约不破）',
  run("'matPrice' in findRow(101).subs[0]") === false);
ok('G11b 契约字段集不变（护栏被绕过就会多出 matPrice）',
  run('Object.keys(findRow(101).subs[0]).sort().join(",")') === 'aux,bid,bsh,coef,conv,gtype,lab,mats,mech,workType',
  run('Object.keys(findRow(101).subs[0]).sort().join(",")'));
near('G11c 行级暂存价保持（不被消耗/清空）', run('findRow(101).matPrice'), 500);
ok('G11d 内部 rowMatCost 不被污染（集团子目无 matPrice → 0）', run('rowMatCost(findRow(101))') === 0);
run('addSub(101, "NS-020", "泥水班组"); syncRowMat(101);');
ok('G11e 混合行（集团 + 内部）同样跳过：内部子目 matPrice 保持 0，不猜落点',
  run('findRow(101).subs[1].matPrice') === 0 && run("'matPrice' in findRow(101).subs[0]") === false);
// 主材价导入（applyQuoteImport）直接调 routeRowMat，绕过 syncRowMat 入口闸 → 护栏必须在写入点前置
run('_mkRows(); addGroupSub(101, "ZS02-D-003");');
ok('G11f routeRowMat 直连路径（导入主材价）也被拦：唯一集团子目不落 matPrice、行也不暂存',
  run('routeRowMat(findRow(101), 88, "", "over")') === 'kept' &&
  run("'matPrice' in findRow(101).subs[0]") === false && run('(parseFloat(findRow(101).matPrice)||0)') === 0);
// T8 收尾（T5 遗留硬性项）：护栏判据是 some(gtype==='group')，与「行内还剩几条集团子目」无关——
// 双集团子目行删掉其一（delSub→syncRowMat）后，剩下的那条仍不得被写入 matPrice
run('_mkRows(); addGroupSub(100, "ZS02-D-003"); addGroupSub(100, "ZS02-A-009"); findRow(100).matPrice = 500; findRow(100).matName = "石材";');
ok('G11g 双集团子目行删之前：两条子目均无 matPrice（护栏与子目条数无关）',
  run("'matPrice' in findRow(100).subs[0]") === false && run("'matPrice' in findRow(100).subs[1]") === false);
run('delSub(100, "ZS02-D-003", "ZS02-D");');
ok('G11g b delSub 其一后（delSub→syncRowMat）：剩下的集团子目仍无 matPrice 键',
  run('findRow(100).subs.length') === 1 && run("'matPrice' in findRow(100).subs[0]") === false);
ok('G11g c 剩下子目契约八字段集不变（护栏被绕过就会多出 matPrice）',
  run('Object.keys(findRow(100).subs[0]).sort().join(",")') === 'aux,bid,bsh,coef,conv,gtype,lab,mats,mech,workType',
  run('Object.keys(findRow(100).subs[0]).sort().join(",")'));
ok('G11g d 内部 rowMatCost 不被污染（0）且行级暂存价保持（删除路径不消耗）',
  run('rowMatCost(findRow(100))') === 0 && run('findRow(100).matPrice') === 500);
run('_mkRows(); addGroupSub(100, "ZS02-D-003"); findRow(100).matPrice = 500; findRow(100).matName = "石材"; addSub(100, "NS-020", "泥水班组");');
run('delSub(100, "NS-020", "泥水班组");');
ok('G12 删掉行内一个内部子目后（delSub→syncRowMat）：group sub 上仍不出现 matPrice',
  run("'matPrice' in findRow(100).subs[0]") === false && run('findRow(100).subs.length') === 1);
near('G12b 删除路径不动行级暂存价', run('findRow(100).matPrice'), 500);
run('delSub(100, "ZS02-D-003", "ZS02-D");');
ok('G12c 集团子目本身可正常删除（bid+bsh 定位复用 delSub）', run('findRow(100).subs.length') === 0);
run('_mkRows(); findRow(100).matPrice = 200; addSub(100, "NS-020", "泥水班组");');
ok('G13 纯内部行 syncRowMat 正常分配（护栏不伤内部路径）', run('findRow(100).subs[0].matPrice') === 200);
run('_mkRows(); pricingMode="internal"; findRow(100).matPrice = 200; addSub(100, "NS-020", "泥水班组");');
ok('G13b internal 模式同样正常（护栏只看 gtype，不看模式）', run('findRow(100).subs[0].matPrice') === 200);
run('pricingMode="group"; _mkRows();');

/* ── G⑥ ZS02 挂载面板 ── */
console.log('\n  · openGroupPicker：本地模糊过滤 + 空库守卫 + 点选挂载');
ok('G14 openGroupPicker / groupPickerItems 为顶层函数',
  run('typeof openGroupPicker') === 'function' && run('typeof groupPickerItems') === 'function');
run('rebuildGroupBenchMap([G009, D003]);');
ok('G14b 空查询返回全量（296 条本地过滤，不分页）', run('groupPickerItems("").length') === 2 && run('groupPickerItems("   ").length') === 2);
ok('G14c 按名称模糊命中', run('groupPickerItems("瓷砖").map(function(x){return x.code}).join()') === 'ZS02-A-009');
ok('G14d 大小写不敏感（PVC → 成品保护-PVC保护膜）', run('groupPickerItems("PVC").map(function(x){return x.code}).join()') === 'ZS02-D-003');
ok('G14e 按特征 spec 命中', run('groupPickerItems("600×600").length') === 1);
ok('G14f 按 code 命中', run('groupPickerItems("ZS02-D-003").length') === 1);
ok('G14g 多关键词 AND（名称+特征）', run('groupPickerItems("瓷砖 600").length') === 1 && run('groupPickerItems("瓷砖 不存在").length') === 0);
ok('G14h 未命中返回空数组（不是 undefined）',
  run('Array.isArray(groupPickerItems("不存在zzz"))') === true && run('groupPickerItems("不存在zzz").length') === 0);
ok('G14i 空库（未建表/加载失败）→ 空数组不抛',
  run('(function(){var keep=groupBenchRows.slice(); rebuildGroupBenchMap([]); try{ return groupPickerItems("瓷砖").length===0; } finally { rebuildGroupBenchMap(keep); } })()') === true);
run('openGroupPicker(101);');
ok('G14j 弹窗打开：groupPickerMod 去掉 hidden', els['groupPickerMod']._clsOps.removed.indexOf('hidden') >= 0, JSON.stringify(els['groupPickerMod']._clsOps));
ok('G14k 表头列齐 code/name/unit/A人工/D辅材/E机械/甲供',
  /A人工/.test(els['gpList'].innerHTML) && /D辅材/.test(els['gpList'].innerHTML) &&
  /E机械/.test(els['gpList'].innerHTML) && /甲供/.test(els['gpList'].innerHTML), String(els['gpList'].innerHTML).slice(0, 200));
ok('G14l 候选行含 code 与 name，且甲供未定价位打「待填价」tag',
  /ZS02-A-009/.test(els['gpList'].innerHTML) && /瓷砖地面/.test(els['gpList'].innerHTML) && /待填价/.test(els['gpList'].innerHTML));
ok('G14m 已定价行不误标（D-003 那行无「待填价」）',
  run('groupMatPending(getGroupBench("ZS02-D-003"))') === false && run('groupMatPending(getGroupBench("ZS02-A-009"))') === true);
run('closeGroupPicker();');
ok('G14n 关闭加回 hidden 并清空目标行',
  els['groupPickerMod']._clsOps.added.indexOf('hidden') >= 0 && run('groupPickerRowId') === null);
reset();
run('rebuildGroupBenchMap([]); openGroupPicker(101);');
ok('G14o 空库时 picker 显示「ZS02 库未加载」+ 重试按钮',
  /ZS02 库未加载/.test(els['gpList'].innerHTML) && /groupPickerRetry\(/.test(els['gpList'].innerHTML),
  String(els['gpList'].innerHTML).slice(0, 160));
run('RESP = {group_benchmark_items:[G009,D003], group_pricing_rules:RULES_SEED}; ' + FLAG_RESET);
run('groupPickerRetry();');
await tick();   // loadGroupDataOnce 是两张表串行 await：等微任务排空才看得到两次 _get
ok('G14p 重试走 ensureGroupData 链路（两张表各一次，不自发 fetch）', GETS.length === 2, JSON.stringify(GETS));
await tick();
ok('G14q 重试成功后库可查（picker 数据源恢复）', run('groupBenchRows.length') === 2);
run('rebuildGroupBenchMap([G009, D003]); closeGroupPicker();');
reset();
run('_mkRows(); _render=0; openGroupPicker(101);');
ok('G15 点选 → addGroupSub 挂载到目标行 + 关闭弹窗',
  run('gpPick("ZS02-D-003")') === true && run('findRow(101).subs.length') === 1 &&
  run('findRow(101).subs[0].gtype') === 'group' && els['groupPickerMod']._clsOps.added.indexOf('hidden') >= 0);
// 弹窗流水是全测试累加的（els 不重置）：拿长度做基线，只判「本次失败有没有新增 close」
run('openGroupPicker(101);');
const CLS_ADDED0 = els['groupPickerMod']._clsOps.added.length;
ok('G15b 重复挂载：addGroupSub 拦截 → 弹窗保持开着（用户可换一条）',
  run('gpPick("ZS02-D-003")') === false && run('findRow(101).subs.length') === 1 &&
  els['groupPickerMod']._clsOps.added.length === CLS_ADDED0);
ok('G15c 未知 code 同样不写 sub', run('gpPick("ZS02-A-999")') === false && run('findRow(101).subs.length') === 1);
run('closeGroupPicker();');
ok('G15d 未指定行（rid=null）点选不抛',
  run('(function(){try{return gpPick("ZS02-D-003")===false;}catch(e){return "throw:"+e.message;}})()') === true);
DOMCFG.gone = true;
ok('G15e 精简 DOM 下开关弹窗不抛',
  run('(function(){try{openGroupPicker(101);closeGroupPicker();groupPickerRetry();renderGroupPicker();return true;}catch(e){return "throw:"+e.message;}})()') === true);
DOMCFG.gone = false;
run('closeGroupPicker(); _mkRows();');

/* ── groupSubRowHtml：集团子目行渲染本体（浏览器冒烟不可用的代替：在沙箱里真跑一次拼接）── */
console.log('\n  · groupSubRowHtml 实渲：列对齐 / 待询价态 / 甲供逐条 / 既有处理器接线');
run('addGroupSub(100, "ZS02-A-009");');
const GH = run('groupSubRowHtml(findRow(100), findRow(100).subs[0])');
ok('G17a 待询价集团子目行输出单个 tr，单元格数 =16（与主表 16 列对齐）',
  /^<tr class="sub-r grp-pend"/.test(GH) && (GH.match(/<td/g) || []).length === 16 && /<\/tr>$/.test(GH),
  (GH.match(/<td/g) || []).length + ' 个 td');
ok('G17b 行内同时挂「集团」+「待询价」两个徽标（.zone-badge 家族，只加 modifier）',
  /zone-badge grp/.test(GH) && /zone-badge pend/.test(GH));
ok('G17c 主材逐条 name×consumption，未定价位显「甲供待询价」黄底输入框',
  /瓷砖×1\.4469/.test(GH) && /1:3干硬性水泥砂浆×0\.0147/.test(GH) &&
  (GH.match(/甲供待询价<\/span>/g) || []).length === 2 && /cof-i pend/.test(GH),
  '待询价文案标签命中 ' + (GH.match(/甲供待询价<\/span>/g) || []).length + ' 个');
ok('G17d 填价入口逐条带 mats 下标（updGroupMat(rid,bid,bsh,idx,value)），不走内部 updSubField',
  /updGroupMat\(100,'ZS02-A-009','ZS02-A',0,this\.value\)/.test(GH) &&
  /updGroupMat\(100,'ZS02-A-009','ZS02-A',1,this\.value\)/.test(GH) && !/updSubField\(/.test(GH));
ok('G17e 系数/换算/删除沿用既有处理器（bid+bsh 定位，零改动复用）',
  /updCoef\(100,'ZS02-A-009','ZS02-A',this\.value\)/.test(GH) &&
  /updConv\(100,'ZS02-A-009','ZS02-A',this\.value\)/.test(GH) &&
  /delSub\(100,'ZS02-A-009','ZS02-A'\)/.test(GH));
ok('G17f 名称/特征/工种取自 getGroupBench（不查内部基准价库 → 不会误报缺失）',
  /瓷砖地面/.test(GH) && /SA级600×600/.test(GH) && /泥水/.test(GH) && !/子目数据缺失/.test(GH));
ok('G17g 待询价时金额列显「待询价」文案而不是 0.00',
  (GH.match(/grp-pend-txt/g) || []).length >= 3);
run('updGroupMat(100,"ZS02-A-009","ZS02-A",0,"100"); updGroupMat(100,"ZS02-A-009","ZS02-A",1,"300");');
const GH2 = run('groupSubRowHtml(findRow(100), findRow(100).subs[0])');
ok('G17h 补齐甲供价后不再挂待询价态，主材费出实数 144.69（100×1.4469）',
  !/grp-pend/.test(GH2) && !/zone-badge pend/.test(GH2) && !/甲供待询价/.test(GH2) && /144\.69/.test(GH2));
ok('G17i 已定价位输入框回显原值（不被 fmt 千分位污染，避免回写脏数据）',
  /value="100"/.test(GH2) && /value="300"/.test(GH2));
run('_mkRows();');

/* ── G⑦ renderBoq 源码结构：集团子目绝不走「子目数据缺失」红底 ── */
console.log('\n  · renderBoq 分流与模式门控（源码结构断言，渲染本体不进沙箱）');
const RB_START = TOOL.indexOf('function renderBoq() {');
const RB_END = TOOL.indexOf('\nfunction importBoq()', RB_START);
if (RB_START < 0 || RB_END < 0) throw new Error('未找到 renderBoq 边界锚点');
const RB = TOOL.slice(RB_START, RB_END);
// 锚到「代码串」本身（不按四个字的通用词找）：源码注释里也会引用「子目数据缺失」，按普通词定位会先 hit 注释而假阴
const GT_IDX = RB.indexOf("gtype === 'group'");
const MISS_IDX = RB.indexOf('⚠️ 子目数据缺失（编号');
const GB_IDX = RB.indexOf('getBench(sub.bid, sub.bsh)');
ok('G16 renderBoq 存在集团子目分流', GT_IDX >= 0);
ok('G16b 分流先于 getBench→「⚠️子目数据缺失」红底路径（集团子目不得被打红底）',
  GT_IDX >= 0 && GT_IDX < MISS_IDX && GT_IDX < GB_IDX, 'gtype@' + GT_IDX + ' / 红底@' + MISS_IDX + ' / getBench@' + GB_IDX);
ok('G16c 红底路径本身保留（内部子目仍需缺失告警）', MISS_IDX >= 0 && /\u26a0\ufe0f 子目数据缺失/.test(RB) && GB_IDX >= 0);
ok('G16d 集团子目行派生单元格交给 groupSubRowHtml（渲染层不内联公式）', /groupSubRowHtml\(/.test(RB));
ok('G16e 待询价行挂 CSS 类（黄底 + 徽标由样式层承担，不在 JS 里拼颜色）', /grp-pend/.test(RB) && /zone-badge pend|badge pend/.test(RB));
ok('G16f 「＋ 集团子目」按钮仅 group 模式渲染（内部 UI 零变化）',
  /pricingMode === 'group'[\s\S]{0,240}openGroupPicker\(/.test(RB), RB.slice(RB.indexOf('addsub-tr'), RB.indexOf('addsub-tr') + 420));
ok('G16g 既有内部 picker 按钮仍无条件保留（并排而非替换）', /openPicker\('\+r.id\+'\)/.test(RB) && /挂子目（从基准价库选择）/.test(RB));
const GSRH = TOOL.indexOf('function groupSubRowHtml');
const GSRH_END = TOOL.indexOf('function renderBoq()', GSRH);
ok('G16h 集团子目行主材价录入走 updGroupMat（不是内部 updSubField matPrice）',
  GSRH >= 0 && GSRH_END > GSRH && /updGroupMat\(/.test(TOOL.slice(GSRH, GSRH_END)) &&
  !/updSubField\([^)]*'matPrice'/.test(TOOL.slice(GSRH, GSRH_END)));
ok('G16i group 模式行级汇总列走既有分支函数（compUnitPrice/rowTotal）',
  /compUnitPrice\(r\)/.test(RB) && /rowTotal\(r\)/.test(RB));

/* ── G⑧ updateSum 底部合计：「人工费合计」在 group 下不得拿全费用单价乘 qty（真实函数依赖整页 DOM，同按结构断言）── */
const US_START = TOOL.indexOf('function updateSum() {');
const US_END = TOOL.indexOf('// ═══════════ PICKER', US_START);
if (US_START < 0 || US_END < 0) throw new Error('未找到 updateSum 边界锚点');
const US = TOOL.slice(US_START, US_END);
ok('G18 updateSum 有 group 分支且人工费走 rowGroupAgg(r).lab（不拿全费用单价乘 qty）',
  /pricingMode === 'group'/.test(US) && /rowGroupAgg\(r\)\.lab \* q/.test(US), US.slice(0, 200));
ok('G18b internal 路径原样保留（rowUnitPrice×qty）', US.indexOf('rowUnitPrice(r)||0') >= 0 && /\* q;/.test(US));
ok('G18c 合计仍走 rowTotal（group 下自动包含待询价行计 0 的口径）', /rowTotal\(r\)\|\|0/.test(US));

/* ── G⑦ T8 收尾：group 模式下旧导出入口门控（源码级：内部导出链零改动） ── */
console.log('\n  · 旧导出入口门控：group 模式拦方式一/方式二/辅材清单/导出弹窗（内部模式恒 false）');
const GMB_SRC = grabAnyFn(TOOL, 'groupModeBlock');
ok('G19/F2 groupModeBlock 守卫收口：group 拦截（消息指向对甲汇总）· 混合态拦截（消息=清单中存在集团子目）· 纯内部清单恒 false',
  /typeof pricingMode/.test(GMB_SRC) && /pricingMode === 'group'/.test(GMB_SRC) &&
  /gtype === 'group'/.test(GMB_SRC) && /清单中存在集团子目，请在对甲报价模式下处理/.test(GMB_SRC) &&
  /toast\(/.test(GMB_SRC) && /导出对甲报价汇总/.test(GMB_SRC));
ok('G19b 四个用户可触发入口首行一律 groupModeBlock 拦截（含 splitByTrade 对账弹窗所在的 doConfigExport）',
  ['showExportModal', 'doConfigExport', 'doAuxExport', 'doTemplateExport'].every(function (n) {
    const f = grabAnyFn(TOOL, n);
    return /if \(groupModeBlock\(\)\) return;/.test(f.slice(f.indexOf('{') + 1).split('\n').slice(0, 2).join('\n'));
  }));
ok('G19c 集团导出链与 EXP_COLS 零交集：doGroupSummaryExport/collectGroupSummaryPayload 不引用 EXP_COLS，lab/mat/aux/waste 列内部口径原样',
  !/EXP_COLS/.test(grabAnyFn(TOOL, 'doGroupSummaryExport')) &&
  !/EXP_COLS/.test(grabAnyFn(TOOL, 'collectGroupSummaryPayload')) &&
  !/groupModeBlock|pricingMode/.test(grabAnyFn(TOOL, 'collectExportData')) &&
  /key:'mat',\s*label:'主材费',\s*get:r=>rowMatCost\(r\)\|\|0/.test(TOOL));

/* ── F2 防御收口：混合态 4 入口被拦（逻辑）+ 恢复含 gtype 数据触发切换（源码） ── */
console.log('\n  · F2：模式守卫防御收口（混合态拦截 / 纯内部零变更 / restoreProject 自动切换）');
run('pricingMode = "internal"; groups = [{id:1, sheetName:"S", open:true, sections:[{id:2, name:"分部", open:true, rows:[]}]}]; uid = 220;');
run('var rg22 = makeRow({name:"集团行", unit:"m2", qty:"1"}); rg22.subs = [{bid:"ZS02-A-009",bsh:"ZS02-A",gtype:"group",coef:1,conv:1,lab:1,aux:0,mech:0,mats:[]}]; var ri22 = makeRow({name:"内部行", unit:"m2", qty:"1"}); groups[0].sections[0].rows = [rg22, ri22]; rebuildRowMap();');
reset();
ok('F2a 混合态（internal 模式 + 存量集团子目）→ groupModeBlock 拦下，消息可操作',
  run('groupModeBlock()') === true && TOASTS.some(t => /清单中存在集团子目，请在对甲报价模式下处理（或先删除集团子目）/.test(t)), JSON.stringify(TOASTS));
ok('F2b 调用方自定义 msg 优先（4 入口不改调用点的兼容前提）',
  run('groupModeBlock("自定义")') === true && TOASTS[TOASTS.length - 1] === '自定义');
run('groups[0].sections[0].rows = [ri22]; rebuildRowMap();');
reset();
ok('F2c 纯内部清单（internal 模式、无集团子目）→ 恒 false 且零 toast（内部模式零行为变更）',
  run('groupModeBlock()') === false && TOASTS.length === 0);
run('pricingMode = "group";');
reset();
ok('F2d group 模式照旧拦截，消息指向「导出对甲报价汇总」',
  run('groupModeBlock()') === true && TOASTS.some(t => /导出对甲报价汇总/.test(t)), JSON.stringify(TOASTS));
run('pricingMode = "internal";');
const RP_SRC = grabAnyFn(TOOL, 'restoreProject');
ok('F2e restoreProject 回写后扫描 gtype:\'group\' → 复用 setPricingMode(\'group\')（含懒加载路径）并 toast 已切换',
  /gtype === 'group'/.test(RP_SRC) && /setPricingMode\('group'\)/.test(RP_SRC) && /已切换至对甲报价模式/.test(RP_SRC),
  RP_SRC.slice(-260));

/* ═══════════ H. Task 6：T02 四部分汇总预览计算 + 导出 payload 收集 ═══════════ */
console.log('\n── H. buildGroupSummary / collectGroupSummaryPayload（勾稽：四=(一+二+三)×tax · 五=一+二+三+四 · D 类不进 part1）──');
run(RATE_RESET + ' globalCoef=1.0; batchMode=false;');
run('rebuildGroupBenchMap([G009, D003]);');
run('pricingMode = "group";');
run(`function _mkSumRows() {
  groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[]}]}];
  uid = 200;
  var ra = makeRow({name:'瓷砖地面', unit:'m2', qty:'5'});    // id200：已补价 A-009
  var rd = makeRow({name:'成品保护', unit:'m2', qty:'10'});   // id201：D-003（行名≠库名，验证 item 取库 raw 名）
  var rp = makeRow({name:'待询价行', unit:'m2', qty:'2'});    // id202：A-009 未补价（pending）
  groups[0].sections[0].rows = [ra, rd, rp];
  rebuildRowMap();
}`);
run('_mkSumRows(); addGroupSub(200,"ZS02-A-009"); addGroupSub(201,"ZS02-D-003"); addGroupSub(202,"ZS02-A-009");');
run('findRow(200).subs[0].mats = [{name:"瓷砖",price:100,unit:"m2",consumption:1.4469},{name:"1:3干硬性水泥砂浆",price:300,unit:"m3",consumption:0.0147}];');
run('var OPTS = {fitoutArea:100, manualFees:{}}; var SUM = buildGroupSummary(getAllRows(), OPTS);');

near('H1 黄金值：part1 = 已套价行合价 230.6085×5（A-009 唯一来源）', run('SUM.part1'), 1153.0425, 0.01);
near('H1b 单价复核：A-009 补齐价后行 unit = T4/T5 黄金值 230.6085', run('rowGroupAgg(findRow(200)).unit'), 230.6085, 0.001);
const SECS = JSON.parse(run('JSON.stringify(SUM.sections)'));
ok('H2 sections 按 discipline+section 归集，只含分部分项（A 类楼地面）',
  SECS.length === 1 && /A/.test(SECS[0].name) && /楼地面/.test(SECS[0].name), JSON.stringify(SECS));
near('H2b 勾稽：Σsections = part1', SECS.reduce((s, x) => s + x.amount, 0), run('SUM.part1'), 0.01);
ok('H2c D 类绝不进 part1/sections（成品保护/措施 不出现在 sections）',
  !SECS.some(x => /D|措施|成品保护/.test(x.name)), JSON.stringify(SECS));
near('H3 part2 = Σ D类合价(4.0779×10=40.779) + 绿安费(308.25×0.13=40.0725)', run('SUM.part2'), 80.8515, 0.01);
near('H4 绿安/baogan 基数只含 part1 人工+机械(308.25)，不含 D 类', run('SUM.laborMechBase'), 308.25, 0.01);
near('H5 part3 = 预算包干费 308.25×0.03（coordFee=null 不计取 · manualFees 空 · 暂列=0）', run('SUM.part3'), 9.2475, 0.01);
near('H6 勾稽：part4 = (part1+part2+part3)×GROUP_RATES.tax',
  run('SUM.part4'), run('(SUM.part1+SUM.part2+SUM.part3)*GROUP_RATES.tax'), 0.01);
near('H6b 数值：四 = 1243.1415×0.09 = 111.8827', run('SUM.part4'), 111.8827, 0.01);
near('H7 勾稽：total = 一+二+三+四', run('SUM.total'), run('SUM.part1+SUM.part2+SUM.part3+SUM.part4'), 0.01);
near('H7b 数值：总造价 1355.0242', run('SUM.total'), 1355.0242, 0.01);
near('H8 perSqm = total ÷ fitoutArea(100)', run('SUM.perSqm'), run('SUM.total/100'), 0.01);
near('H8b 数值：单方造价 13.5502', run('SUM.perSqm'), 13.5502, 0.01);
ok('H9 待询价行（202）不进 part1 且被计数 unpriced=1', run('SUM.unpriced') === 1, 'unpriced=' + run('SUM.unpriced'));

console.log('\n  · 费率不硬编码：green/baogan/tax 全走 GROUP_RATES');
run('GROUP_RATES.green = 0.20; GROUP_RATES.baogan = 0.05; GROUP_RATES.tax = 0.10; var SUM2 = buildGroupSummary(getAllRows(), OPTS);');
near('H10 part2 随 GROUP_RATES.green 变（0.13→0.20，不写死）', run('SUM2.part2'), run('40.779 + 308.25*0.20'), 0.01);
near('H10b part3 随 GROUP_RATES.baogan 变（0.03→0.05，不写死）', run('SUM2.part3'), run('308.25*0.05'), 0.01);
near('H10c part4 随 GROUP_RATES.tax 变：四 =(一+二+三)×0.10（不写死 0.09）',
  run('SUM2.part4'), run('(SUM2.part1+SUM2.part2+SUM2.part3)*0.10'), 0.01);
run(RATE_RESET);

console.log('\n  · coordFee：null≠0（未配不计取，面板标注「参数未配置」）· 配置后 = 单价×装修面积');
run('var SUMA = buildGroupSummary(getAllRows(), OPTS);');
ok('H11 coordFee=null → coordFeeConfigured:false（part3 不含配合费，见 H5）', run('SUMA.coordFeeConfigured') === false);
run('GROUP_RATES.coordFee = 50; var SUMB = buildGroupSummary(getAllRows(), OPTS);');
ok('H11b coordFee=50 → coordFeeConfigured:true', run('SUMB.coordFeeConfigured') === true);
near('H12 coordFee=50 元/m2 × 100m2 → part3 增加 5000', run('SUMB.part3'), run('SUMA.part3 + 50*100'), 0.01);
run(RATE_RESET + ' var SUMC = buildGroupSummary(getAllRows(), OPTS);');
near('H12b 复位 coordFee=null 后 part3 回到不含配合费', run('SUMC.part3'), run('SUMA.part3'), 0.01);

console.log('\n  · manualFees：Σ 计入 part3（赶工/变更/涨幅 手工金额）');
run('var SUMM = buildGroupSummary(getAllRows(), {fitoutArea:100, manualFees:{overtime_fee:1000, contract_change_fee:500, inflation_fee:0}});');
near('H14 part3 含 ΣmanualFees=1500 + 预算包干费', run('SUMM.part3'), run('SUMA.part3 + 1500'), 0.01);

console.log('\n  · fitoutArea 缺失/0 → perSqm=null 不除零 + needsArea 提示');
run('var SUM0 = buildGroupSummary(getAllRows(), {fitoutArea:0, manualFees:{}});');
ok('H13 fitoutArea=0 → perSqm 为 null（不产生 Infinity/除零）', run('SUM0.perSqm') === null, String(run('SUM0.perSqm')));
ok('H13b 并置 needsArea:true（面板据此提示填写装修面积）', run('SUM0.needsArea') === true);
run('var SUMN = buildGroupSummary(getAllRows(), {});');
ok('H13c opts 缺 fitoutArea 同样 perSqm:null（undefined 非数值）', run('SUMN.perSqm') === null);

console.log('\n  · collectGroupSummaryPayload：raw 字段集 + 不下发前端 h');
run('_mkSumRows(); addGroupSub(200,"ZS02-A-009"); addGroupSub(201,"ZS02-D-003");');
run('findRow(200).subs[0].mats = [{name:"瓷砖",price:100,unit:"m2",consumption:1.4469},{name:"1:3干硬性水泥砂浆",price:300,unit:"m3",consumption:0.0147}];');
run('document.getElementById("projName").value="天河精装一期"; document.getElementById("fitoutAreaInp").value="100"; document.getElementById("manualFeeOvertimeInp").value="1000"; document.getElementById("manualFeeChangeInp").value=""; document.getElementById("manualFeeInflationInp").value="";');
const PL = run('collectGroupSummaryPayload();');
ok('H15 顶层键 = {project_name,fitout_area,rates,manual_fees,items}',
  JSON.stringify(Object.keys(PL).sort()) === JSON.stringify(['fitout_area', 'items', 'manual_fees', 'project_name', 'rates']), JSON.stringify(Object.keys(PL)));
ok('H15b project_name 取项目表单，fitout_area 取新输入并数值化 100',
  PL.project_name === '天河精装一期' && PL.fitout_area === 100, JSON.stringify([PL.project_name, PL.fitout_area]));
ok('H15c rates = GROUP_RATES 原样六键',
  JSON.stringify(Object.keys(PL.rates).sort()) === JSON.stringify(['baogan', 'coordFee', 'green', 'mgmt', 'profit', 'tax']), JSON.stringify(Object.keys(PL.rates)));
ok('H15d manual_fees 三键 snake_case（赶工/变更/涨幅）',
  JSON.stringify(Object.keys(PL.manual_fees).sort()) === JSON.stringify(['contract_change_fee', 'inflation_fee', 'overtime_fee']), JSON.stringify(PL.manual_fees));
ok('H15e 赶工费取输入 1000，其余空为 0',
  PL.manual_fees.overtime_fee === 1000 && PL.manual_fees.contract_change_fee === 0 && PL.manual_fees.inflation_fee === 0, JSON.stringify(PL.manual_fees));
const ITEMS = PL.items;
ok('H16 items = 每行×集团子目一条（本夹具两行两子目）', ITEMS.length === 2, JSON.stringify(ITEMS.length));
const ITEM_KEYS = JSON.stringify(Object.keys(ITEMS[0]).sort());
ok('H16b item raw 键集精确 =14 键（snake_case，不多不少）',
  ITEM_KEYS === JSON.stringify(['aux', 'coef', 'code', 'conv', 'discipline', 'lab', 'mats', 'mech', 'name', 'qty', 'section_name', 'spec', 'unit', 'work_type'].sort()), ITEM_KEYS);
ok('H16c 不下发前端算得的 h（后端重算）', ITEMS.every(it => !('h' in it)), JSON.stringify(Object.keys(ITEMS[0])));
const AIT = ITEMS.find(x => x.code === 'ZS02-A-009');
const DIT = ITEMS.find(x => x.code === 'ZS02-D-003');
ok('H16d code=子目 bid；discipline/section_name/name/spec/unit 取库行 raw（非行名：D 行名「成品保护」→ item 取库「成品保护-PVC保护膜」）',
  AIT && AIT.discipline === 'A' && AIT.section_name === '楼地面工程' && AIT.name === '瓷砖地面' && AIT.unit === 'm2' && AIT.spec === 'SA级600×600' &&
  DIT && DIT.name === '成品保护-PVC保护膜', JSON.stringify(AIT));
ok('H16e qty 取行工程量（A 行 5 / D 行 10）', AIT && AIT.qty === 5 && DIT && DIT.qty === 10);
ok('H16f lab/mats/aux/mech/coef/conv 取子目 raw（补齐后的 mats 价原样下发）',
  AIT && AIT.lab === 61.65 && AIT.aux === 1.98 && AIT.mech === 0 && AIT.coef === 1 && AIT.conv === 1 &&
  AIT.mats[0].price === 100 && AIT.mats[1].price === 300, JSON.stringify(AIT && AIT.mats));
ok('H16g work_type 取 raw 值（A 泥水 / D 油漆）', AIT && AIT.work_type === '泥水' && DIT && DIT.work_type === '油漆');
run('_mkSumRows(); document.getElementById("fitoutAreaInp").value=""; document.getElementById("manualFeeOvertimeInp").value="";');
const PL0 = run('collectGroupSummaryPayload();');
ok('H17 无集团子目的行不产出 item（内部行零影响）', PL0.items.length === 0, JSON.stringify(PL0.items));
ok('H17b fitout_area 空输入 → 数值 0（不抛、不 NaN）', PL0.fitout_area === 0, String(PL0.fitout_area));

console.log('\n  · 负值钳制（M-1）：负面积/负手工费不得倒扣 part3');
run('_mkSumRows(); addGroupSub(200,"ZS02-A-009"); addGroupSub(201,"ZS02-D-003"); addGroupSub(202,"ZS02-A-009");');
run('findRow(200).subs[0].mats = [{name:"瓷砖",price:100,unit:"m2",consumption:1.4469},{name:"1:3干硬性水泥砂浆",price:300,unit:"m3",consumption:0.0147}];');
run('GROUP_RATES.coordFee = 50; var SUMNEG = buildGroupSummary(getAllRows(), {fitoutArea:-100, manualFees:{overtime_fee:-1000, contract_change_fee:-500, inflation_fee:-200}});');
ok('M1 负面积钳到 0 → coordAmount 不为负（按 0 面积计=0，不产生负配合费）', run('SUMNEG.coordFee') === 0 && run('SUMNEG.coordFee') >= 0, 'coordFee=' + run('SUMNEG.coordFee'));
ok('M1b 负手工费逐项钳到 ≥0 → manualFees 汇总为 0（不被负数拉低）', run('SUMNEG.manualFees') === 0, 'manualFees=' + run('SUMNEG.manualFees'));
near('M1c part3 不被倒扣：负面积+负手工费下 part3 = 纯预算包干费', run('SUMNEG.part3'), run('SUMNEG.laborMechBase * GROUP_RATES.baogan'), 0.01);
run(RATE_RESET);

console.log('\n  · 采集点下钳（M-1b）：负值在进汇总 opts / 后端 payload / 持久化列之前钳 0');
run('document.getElementById("fitoutAreaInp").value="-50"; document.getElementById("manualFeeOvertimeInp").value="-1000"; document.getElementById("manualFeeChangeInp").value="-500"; document.getElementById("manualFeeInflationInp").value="-200";');
const PLNEG = run('collectGroupSummaryPayload();');
ok('M1d 负面积/负手工费 → payload fitout_area 与 manual_fees 三键全为 0（Task 7 后端重算拿不到负数）',
  PLNEG.fitout_area === 0 && PLNEG.manual_fees.overtime_fee === 0 && PLNEG.manual_fees.contract_change_fee === 0 && PLNEG.manual_fees.inflation_fee === 0,
  JSON.stringify([PLNEG.fitout_area, PLNEG.manual_fees]));
ok('M1e 钳制只改值不改键：负值 payload 顶层键集/manual_fees 键集 = 正值 payload（items 14 键契约不受影响）',
  JSON.stringify(Object.keys(PLNEG).sort()) === JSON.stringify(Object.keys(PL).sort()) &&
  JSON.stringify(Object.keys(PLNEG.manual_fees).sort()) === JSON.stringify(Object.keys(PL.manual_fees).sort()),
  JSON.stringify([Object.keys(PLNEG), Object.keys(PLNEG.manual_fees)]));
ok('M1f getGroupSummaryOpts 同源下钳（面板输入 → 汇总 opts 与 collect 不分叉）',
  run('getGroupSummaryOpts().fitoutArea') === 0 && run('getGroupSummaryOpts().manualFees.overtime_fee') === 0,
  JSON.stringify(run('getGroupSummaryOpts()')));
run('document.getElementById("fitoutAreaInp").value="120.5"; document.getElementById("manualFeeOvertimeInp").value="800";');
ok('M1g 正值路径逐字不变：120.5 / 800 原样透传（Math.max 不裁剪正数）',
  run('getGroupSummaryOpts().fitoutArea') === 120.5 && run('getGroupSummaryOpts().manualFees.overtime_fee') === 800,
  JSON.stringify(run('getGroupSummaryOpts()')));
const SAVE_START = TOOL.indexOf('async function doAutoSave');
const RESTORE_START = TOOL.indexOf('async function restoreProject');
const SAVEBLK = TOOL.slice(SAVE_START, RESTORE_START);          // doAutoSave 草稿 + saveProject 正式
const RESTOREBLK = TOOL.slice(RESTORE_START, TOOL.indexOf('async function deleteProject'));   // 写回侧
const CLAMPED = (SAVEBLK.match(/Math\.max\(0, parseFloat\(document\.getElementById\('(fitoutAreaInp|manualFeeOvertimeInp|manualFeeChangeInp|manualFeeInflationInp)'\)\?\.value\) \|\| 0\)/g) || []).length;
ok('M1h 两处保存 payload（doAutoSave 草稿 + saveProject 正式）的 4 个新列读值全部已下钳（源码级 8/8）',
  CLAMPED === 8, 'clamped=' + CLAMPED);
ok('M1hb 恢复写回侧保持 != null ? x : \'\' 回落（不进钳制，旧快照缺列回落空串→计算 0）',
  (RESTOREBLK.match(/snap\.(fitout_area|overtime_fee|contract_change_fee|inflation_fee) != null \? snap\.\1 : ''/g) || []).length === 4
  && RESTOREBLK.indexOf('Math.max(0, parseFloat(snap.') < 0,
  'restore_lines=' + (RESTOREBLK.match(/snap\.(fitout_area|overtime_fee|contract_change_fee|inflation_fee) != null/g) || []).length);
run('document.getElementById("fitoutAreaInp").value=""; document.getElementById("manualFeeOvertimeInp").value=""; document.getElementById("manualFeeChangeInp").value=""; document.getElementById("manualFeeInflationInp").value="";');

console.log('\n  · payload.rates 浅拷贝（M-6）：不共享 GROUP_RATES 活引用，费率补写不回溯漂移已构造 payload');
run('document.getElementById("projName").value="拷贝测试"; document.getElementById("fitoutAreaInp").value="100";');
ok('M6 payload.rates 与 GROUP_RATES 非同一引用（!==）', run('collectGroupSummaryPayload().rates !== GROUP_RATES') === true);
ok('M6b payload.rates 六键值与 GROUP_RATES 逐一相等（拷贝不失真）', run('(function(){var r=collectGroupSummaryPayload().rates;return Object.keys(GROUP_RATES).every(function(k){return r[k]===GROUP_RATES[k];}) && Object.keys(r).length===Object.keys(GROUP_RATES).length;})()') === true);
ok('M6c 构造后改 GROUP_RATES.tax 不回写已生成 payload.rates（活引用漂移被切断）', run('(function(){var p=collectGroupSummaryPayload();var before=p.rates.tax;GROUP_RATES.tax=0.99;var drifted=(p.rates.tax!==before);GROUP_RATES.tax=before;return drifted===false;})()') === true);
run(RATE_RESET + ' pricingMode = "internal";');

/* ── M-2（T6 遗留）：汇总面板「coordFee 已配置但面积未填」补注（源码级：面板函数不在沙箱内） ── */
const PANEL_SRC = grabAnyFn(TOOL, 'renderGroupSummaryPanel');
ok('M2 面板预警：coordFeeConfigured 且 needsArea → 配合费行补注「暂按 0 计，待装修面积确认」（未配置时的告警行原样保留）',
  /coordFeeConfigured\s*\?\s*fmt\(s\.coordFee\)\s*\+\s*\(s\.needsArea\s*\?\s*'（暂按 0 计，待装修面积确认）'/.test(PANEL_SRC) &&
  /if \(!s\.coordFeeConfigured\)/.test(PANEL_SRC));
run('pricingMode = "group";');

/* ── F4 导出 400 分类补全 + 客户端预检（源码级：导出函数走真实 fetch，不进沙箱） ── */
console.log('\n  · F4：fitout_area_required 分支 + needsArea 预检拦截');
const DGE_SRC = grabAnyFn(TOOL, 'doGroupSummaryExport');
ok('F4a 400 分类补全：fitout_area_required 分支存在，文案与后端闸门同源且聚焦 #fitoutAreaInp',
  /detail\.error === 'fitout_area_required'/.test(DGE_SRC) && /请先填写装修面积（单方造价分母）/.test(DGE_SRC) &&
  (DGE_SRC.match(/fitoutAreaInp/g) || []).length >= 2, (DGE_SRC.match(/fitoutAreaInp/g) || []).length + ' 处');
ok('F4b 客户端预检：needsArea 在 await fetch 之前 toast 拦截不发请求',
  /pre\.needsArea/.test(DGE_SRC) && DGE_SRC.indexOf('pre.needsArea') < DGE_SRC.indexOf('await fetch') &&
  /buildGroupSummary\(getAllRows\(\), getGroupSummaryOpts\(\)\)/.test(DGE_SRC));

/* ── F5 集团模式下 AI 套价与内部 picker 关门（源码级：两函数不进沙箱） ── */
const SAP_SRC = grabAnyFn(TOOL, 'startAiPricing');
ok('F5a startAiPricing 首行 groupModeBlock 拦截（AI 套价仅支持对内模式）',
  SAP_SRC.slice(SAP_SRC.indexOf('{') + 1).trim().startsWith("if (groupModeBlock('AI 套价仅支持对内模式，请切回对内成本')) return;"),
  SAP_SRC.slice(SAP_SRC.indexOf('{') + 1, SAP_SRC.indexOf('{') + 130));
const RB_SRC = grabAnyFn(TOOL, 'renderBoq');
ok('F5b renderBoq 内部「＋ 挂子目」与集团按钮互斥渲染：group 下隐藏、内部模式原样',
  /pricingMode !== 'group' \? '<button class="addsub-btn" onclick="openPicker\(/.test(RB_SRC) &&
  /pricingMode === 'group' \? ' <button class="addsub-btn grp" onclick="openGroupPicker\(/.test(RB_SRC));

/* ── F1 镜像夹具：一行挂 2 个集团子目、其一 pending → 子目级排除（与后端 group_summary_export.compute 同口径） ── */
console.log('\n  · F1：一行两子目其一待询价 —— 子目级剔除，兄弟子目照常进 part1（双向钉镜像后端）');
run(`groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[]}]}];
     uid = 210;
     var rmix = makeRow({name:'混合待询价行', unit:'m2', qty:'5'});
     groups[0].sections[0].rows = [rmix]; rebuildRowMap();`);
run('addGroupSub(210,"ZS02-A-009");');   // 子目①：A-009 未补价（G009 mats 价格均 null → pending）
run('findRow(210).subs.push({bid:"ZS02-A-009",bsh:"ZS02-A",gtype:"group",coef:1.0,conv:1.0,workType:"泥水",lab:61.65,aux:1.98,mech:0,mats:[{name:"瓷砖",price:100,unit:"m2",consumption:1.4469},{name:"1:3干硬性水泥砂浆",price:300,unit:"m3",consumption:0.0147}]});');  // 子目②：同编码已定价（addGroupSub 查重拒绝同 bid+bsh，手工入同一 subs 通道）
run('var SUMF1 = buildGroupSummary(getAllRows(), OPTS);');
near('F1a part1 只含已定价子目合价 230.6085×5（pending 兄弟子目不拖累整行）', run('SUMF1.part1'), 1153.0425, 0.01);
ok('F1b unpriced 按子目级计数：1 条 pending 子目 = 1', run('SUMF1.unpriced') === 1, 'unpriced=' + run('SUMF1.unpriced'));
near('F1c 绿安/包干基数同样子目级：laborMechBase = 61.65×5', run('SUMF1.laborMechBase'), 308.25, 1e-6);
const SECSF1 = JSON.parse(run('JSON.stringify(SUMF1.sections)'));
ok('F1d sections 只归集已定价子目（Σsections = part1，A·楼地面）',
  SECSF1.length === 1 && Math.abs(SECSF1[0].amount - run('SUMF1.part1')) < 0.01 && /楼地面/.test(SECSF1[0].name), JSON.stringify(SECSF1));
near('F1e 跨端镜像常数：part1 与后端同夹具值 1153.0425 严格一致（tol 2e-6）', run('SUMF1.part1'), 230.6085 * 5, 2e-6);
ok('F1f 行级展示语义不变：混合行仍 ready:false + rowGroupPending:true（BOQ 黄底照旧）',
  run('rowGroupAgg(findRow(210)).ready') === false && run('rowGroupPending(findRow(210))') === true);

console.log('\n════════ 结果：' + pass + ' 通过 / ' + fail + ' 失败 ════════');
console.log(fail ? '❌ 集团契约被破坏（库查询/费率映射/懒加载/开关互斥/公式引擎/派生单元格与挂载面板）\n' : '✅ ZS02 数据基座、模式开关状态机、集团公式引擎、派生单元格/待询价态/挂载面板与内部公式回归全部成立\n');
process.exit(fail ? 1 : 0);

})().catch(e => { console.error('\n💥 测试异常：' + (e && e.message ? e.message : e)); process.exit(1); });

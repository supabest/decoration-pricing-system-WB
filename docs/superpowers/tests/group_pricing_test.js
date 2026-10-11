/* 对甲报价（集团基准价 ZS02）数据基座验证：库可查 + 集团费率映射 + 模式开关状态机（懒加载）
 * 只读 tool.html 源码（不修改它），沿用 quote_import_test.js 的抽函数沙箱模式：
 * grabFn/closeIdx 抽顶层函数声明 → vm 沙箱执行 → DOM/_get/toast 打桩。
 * 覆盖 Task 3 契约：pricingMode / groupBenchMap / getGroupBench / GROUP_RATES /
 *   loadGroupBenchmark / loadGroupPricingRules / ensureGroupData / setPricingMode
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

/* ── DOM 打桩：getElementById 惰性建元素，宿主侧可直接读 disabled/checked/textContent ── */
const els = {};
const DOMCFG = { gone: false };   // 置 true 可模拟「元素不存在」的精简 DOM
function mkEl(id) {
  return { id, value: '', checked: false, disabled: false, textContent: '', title: '', className: '',
    style: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } } };
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

/* ── 沙箱：只搬 group 数据基座 + 它依赖的桩，对内模式的费率/系数状态一并声明用于污染检查 ── */
const LINES = ['let pricingMode', 'let groupDataLoaded', 'let groupBenchLoaded', 'let groupRulesLoaded', 'let _groupLoading'];
const DECLS = ['let GROUP_RATES', 'let groupBenchMap', 'let groupBenchRows', 'const GROUP_RULE_KEY_MAP'];
const FNS = ['rebuildGroupBenchMap', 'getGroupBench', 'groupRateLabel', 'loadGroupBenchmark',
  'loadGroupPricingRules', 'loadGroupDataOnce', 'ensureGroupData', 'setPricingMode'];

let ctx;
const HEAD = [
  '// 对内引擎状态：模式开关不得触碰',
  'let globalCoef=1.0, globalMgmtRate=10, globalProfitRate=15;',
  '// renderBoq/updateSum 用计数器桩：本测试只验开关接线，不跑真实渲染',
  'let _render=0, _sum=0; function renderBoq(){_render++;} function updateSum(){_sum++;}',
  'function toast(m){TOASTS.push(m);}',
  'let RESP={}; let _get=async function(t,p){GETS.push(t); return (RESP[t]||[]).slice();};',
];
function buildSandbox() {
  ctx = vm.createContext({
    console, JSON, Math, Number, parseFloat, parseInt, String, Object, Array, isNaN, Set, Date, RegExp, Promise,
    document, GETS, TOASTS, DOMCFG,
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

console.log('\n════════ 结果：' + pass + ' 通过 / ' + fail + ' 失败 ════════');
console.log(fail ? '❌ 集团数据基座契约被破坏（库查询/费率映射/懒加载/开关互斥）\n' : '✅ ZS02 库与集团费率基座、报价模式开关状态机全部成立\n');
process.exit(fail ? 1 : 0);

})().catch(e => { console.error('\n💥 测试异常：' + (e && e.message ? e.message : e)); process.exit(1); });

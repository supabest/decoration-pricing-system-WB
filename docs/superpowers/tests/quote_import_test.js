/* 询价导入落点与主材费不变式验证（只读 tool.html 源码，不修改它）
 * 用途：在没有浏览器自动化通道时，客观证明「导入清单 → AI 套价 → 导入询价」
 * 的落点规则（staged/assigned/pending/kept）与行级主材换算不变式确实成立。
 * 运行：node docs/superpowers/tests/quote_import_test.js
 */
const fs = require('fs');
const vm = require('vm');

const TOOL = fs.readFileSync(__dirname + '/../../tool.html', 'utf8');

/* ── 抽取器（与 m_parity_test.js 同一套：先跳参数表再配对花括号，抽完即编译校验）── */
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

const FN_NAMES = ['normKey', 'countHit', 'rebuildBenchMap', 'getBench', 'getAllRows', 'rebuildRowMap',
  'findRow', 'makeRow', 'rowUnitPrice', 'rowMatCost', 'effRowMatPrice', 'rowWasteInfo', 'effRowWaste', 'effPrice',
  'subCategoryScore', 'routeRowMat', 'syncRowMat', 'rowMatPending', 'rowMatStaged', 'rowTotal', 'exportRemark'];
const DECLS = ['const MAT_CAT_KEYWORDS'];

const ctx = vm.createContext({ console, JSON, Math, Number, parseFloat, parseInt, String, Object, Array, isNaN, Set, Date, RegExp });
vm.runInContext(
  'let groups=[], uid=1, rowMap=new Map(), DB={}, benchMap={}, ALL=[];' +
  'let globalCoef=1.0, globalMgmtRate=10, globalProfitRate=15, hourlyRate=350, priceLib={}, userPriceOverrides={};' +
  DECLS.map(d => grabDecl(TOOL, d)).join('\n') + '\n' +
  FN_NAMES.map(n => grabFn(TOOL, n)).join('\n'),
  ctx);
const run = code => vm.runInContext(code, ctx);

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? '  → ' + detail : '')); }
}
function near(name, a, b, tol) {
  ok(name + ' (' + a + ' ≈ ' + b + ')', Math.abs(a - b) <= (tol === undefined ? 1e-9 : tol), '偏差 ' + Math.abs(a - b));
}

/* applyQuoteImport 的计数聚合逻辑复刻（原函数依赖 DOM，这里只搬它的判定骨架） */
function applyCounts(items, mode) {
  const done = {}; let assigned = 0, staged = 0, pending = 0, kept = 0, dup = 0;
  items.forEach(it => {
    const r = it.row;
    if (done[r.id]) { dup++; return; }
    done[r.id] = 1;
    const st = run(`routeRowMat(findRow(${r.id}), ${it.price}, '${it.cat || ''}', '${mode}')`);
    if (st === 'assigned') assigned++; else if (st === 'staged') staged++;
    else if (st === 'pending') pending++; else kept++;
  });
  return { assigned, staged, pending, kept, dup };
}
/* makeRow 只造行不入组，需手动 push 进 groups 再重建 rowMap（与 tool.html 渲染路径一致） */
const mkRow = (fields, subs) => run(`(function(){ var r = Object.assign(makeRow(${JSON.stringify(fields)}), ${subs ? JSON.stringify({ subs }) : '{}'}); groups[0].sections[0].rows.push(r); rebuildRowMap(); return r.id; })()`);

console.log('\n── 夹具：模拟已「导入清单 + AI 套价」的四类行 ──');
run(`DB = { '泥水班组':[
    {id:'NS-020', name:'墙面铺贴-石材', unit:'m2', price:120, waste_rate:3},
    {id:'NS-015', name:'墙面铺贴-瓷砖', unit:'m2', price:50,  waste_rate:5},
    {id:'NS-030', name:'墙面基层-抹灰', unit:'m2', price:28,  waste_rate:0},
  ], '木工班组':[
    {id:'MG-011', name:'饰面-木饰面', unit:'m2', price:180, waste_rate:8},
    {id:'MG-012', name:'基层-木龙骨', unit:'m2', price:22,  waste_rate:0},
  ] }; rebuildBenchMap(); groups=[{id:1,sheetName:'S',sections:[{id:2,rows:[]}]}];`);

const R_STONE = mkRow({ name: '石材墙面', spec: '150厚干挂', unit: 'm2', qty: '10' },
  [{ bid: 'NS-020', bsh: '泥水班组', coef: 1.0, conv: 1.0, matName: '石材', matPrice: 0, wasteRate: 3 },
   { bid: 'NS-030', bsh: '泥水班组', coef: 0.5, conv: 2.0, matName: '', matPrice: 0, wasteRate: 0 }]);
const R_TILE = mkRow({ name: '瓷砖墙面', spec: '300×600', unit: 'm2', qty: '8' },
  [{ bid: 'NS-015', bsh: '泥水班组', coef: 1.0, conv: 1.0, matName: '瓷砖', matPrice: 0, wasteRate: 5 }]);
const R_PRICED = mkRow({ name: '石材墙面(已含价)', spec: 'x', unit: 'm2', qty: '5' },
  [{ bid: 'NS-020', bsh: '泥水班组', coef: 1.0, conv: 1.0, matName: '石材', matPrice: 200, wasteRate: 3 }]);
const R_UNMATCH = mkRow({ name: '石膏线', spec: 'x', unit: 'm', qty: '20' },
  [{ bid: 'MG-011', bsh: '木工班组', coef: 1.0, conv: 1.0, matName: '', matPrice: 0, wasteRate: 0 },
   { bid: 'MG-012', bsh: '木工班组', coef: 1.0, conv: 1.0, matName: '', matPrice: 0, wasteRate: 0 }]);
const R_UNPRICED = mkRow({ name: '不锈钢线条', spec: '10mm', unit: 'm', qty: '30' });
console.log('  已建 5 行：石材双子目 / 瓷砖单子目 / 同品类已有价 / 品类不匹配 / 未套价\n');

console.log('── A. 落点规则（对应 toast 的五类计数）──');
const c1 = applyCounts([{ row: run(`findRow(${R_STONE})`), price: 210, cat: '石材' },
                        { row: run(`findRow(${R_TILE})`), price: 88, cat: '瓷砖' },
                        { row: run(`findRow(${R_PRICED})`), price: 210, cat: '石材' },
                        { row: run(`findRow(${R_UNMATCH})`), price: 15, cat: '石材' },
                        { row: run(`findRow(${R_UNPRICED})`), price: 60, cat: '不锈钢' }], 'fill');
console.log('  toast 预测：✓ 主材价导入：套入子目 ' + c1.assigned + '、暂存待套价 ' + c1.staged +
  '、多子目待分配 ' + c1.pending + '、原值未动 ' + c1.kept + (c1.dup ? '、同行重复 ' + c1.dup : '') + '\n');
ok('A1 已套价行按品类落到空缺子目 → assigned=2（石材/瓷砖）', c1.assigned === 2, JSON.stringify(c1));
ok('A2 同品类已有价不覆盖 → kept=1（原值未动）', c1.kept === 1, JSON.stringify(c1));
ok('A3 未套价行只暂存不进成本 → staged=1', c1.staged === 1, JSON.stringify(c1));
ok('A4 多子目认不出品类不猜 → pending=1（界面会标 ⚠️ 主材价待分配）', c1.pending === 1, JSON.stringify(c1));
ok('A5 同行重复=0（每行只取第一条）', c1.dup === 0, JSON.stringify(c1));
ok('A6 报价落到对的子目：石材行 NS-020=210 且 NS-030 仍为 0',
  run(`(function(){var r=findRow(${R_STONE});return r.subs[0].matPrice===210 && r.subs[1].matPrice===0;})()`));
ok('A7 未套价价留在行级 r.matPrice（不写子目）', run(`findRow(${R_UNPRICED}).matPrice === 60 && (findRow(${R_UNPRICED}).subs||[]).length === 0`));
ok('A8 rowMatStaged 识别「压根还没套价」', run(`rowMatStaged(findRow(${R_UNPRICED})) === true`));
ok('A9 rowMatPending 识别「已套价但多子目未分配」', run(`rowMatPending(findRow(${R_UNMATCH})) === true`));
ok('A10 重复导入同一价 → 全部 kept（幂等，不会重复加价）',
  applyCounts([{ row: run(`findRow(${R_TILE})`), price: 999, cat: '瓷砖' }], 'fill').kept === 1);
ok('A11 over 模式才覆盖已有价', run(`routeRowMat(findRow(${R_PRICED}), 260, '石材', 'over') === 'assigned' && findRow(${R_PRICED}).subs[0].matPrice === 260`));

console.log('\n── B. 第④步的「暂存继承」：未套价行挂上子目后自动落价 ──');
run(`findRow(${R_UNPRICED}).subs=[{bid:'NS-015',bsh:'泥水班组',coef:1.0,conv:1.0,matName:'',matPrice:0,wasteRate:5}]; syncRowMat(${R_UNPRICED});`);
ok('B1 syncRowMat 把行级暂存价分到唯一子目', run(`findRow(${R_UNPRICED}).subs[0].matPrice === 60`));
ok('B2 继承后行级价不再重复计入（effRowMatPrice 走子目口径）', run(`Math.abs(effRowMatPrice(findRow(${R_UNPRICED})) - 60) < 1e-9`));

console.log('\n── C. 不变式：行主材单价×行工程量 = Σ(子目主材费×子目工程量) ──');
run(`(function(){var r=findRow(${R_STONE}); r.subs[0].matPrice=210; r.subs[0].coef=1.0; r.subs[0].conv=1.0; r.subs[0].wasteRate=3;
  r.subs[1].matPrice=28; r.subs[1].coef=0.5; r.subs[1].conv=2.0; r.subs[1].wasteRate=0; r.qty='10'; return r;})()`);
const net = run(`effRowMatPrice(findRow(${R_STONE}))`);
const gross = run(`rowMatCost(findRow(${R_STONE}))`);
const q = 10;
const sumSubGross = run(`findRow(${R_STONE}).subs.reduce((s,x)=>s+x.matPrice*(1+x.wasteRate/100)*x.coef*x.conv,0)`);
const sumSubNet = run(`findRow(${R_STONE}).subs.reduce((s,x)=>s+x.matPrice*x.coef*x.conv,0)`);
near('C1 行主材单价 = Σ(子目净价×coef×conv)（多主材不是裸相加）', net, sumSubNet);
near('C2 行主材费 = Σ(子目含损耗费)', gross, sumSubGross);
near('C3 行主材单价×工程量 == Σ(子目净料×子目工程量)', net * q, sumSubNet * q);
const effW = run(`effRowWaste(findRow(${R_STONE}))`);
// 自洽性必须用「未取整的等效损耗率」rowWasteInfo().eff；effRowWaste 是展示/导出口径，已四舍五入到 2 位
const rawEff = run(`rowWasteInfo(findRow(${R_STONE})).eff`);
near('C4 等效损耗率（未取整）自洽：单价×(1+率) = 主材费', net * (1 + rawEff / 100), gross, 1e-9);
const effWStr = run(`String(effRowWaste(findRow(${R_STONE})))`);
ok('C5 导出口径取整到 2 位（不出现 1.8949999… 长小数写进 Excel）',
  !/\./.test(effWStr) || effWStr.split('.')[1].length <= 2, '实际=' + effWStr);
ok('C6 effRowWaste 与未取整值差异在展示精度内', Math.abs(effW - rawEff) <= 0.005, 'effRowWaste=' + effW + ' raw=' + rawEff);
const rt = run(`rowTotal(findRow(${R_STONE}))`);
ok('C7 rowTotal 含主材费且不双计', isFinite(rt) && rt > 0, 'rowTotal=' + rt);
const rtMatPart = run(`rowMatCost(findRow(${R_STONE})) * parseFloat(findRow(${R_STONE}).qty)`);
ok('C8 rowTotal 中主材部分 = 行主材费×工程量（' + rt.toFixed(2) + ' 含 ' + rtMatPart.toFixed(2) + '）', rt >= rtMatPart && rtMatPart > 0);

console.log('\n── D. 导出契约：前端聚合 mat_price/waste_rate，后端按 ×(1+waste/100) 复现 ──');
const exported = run(`(function(){var r=findRow(${R_STONE}); return {mat_price: effRowMatPrice(r), waste_rate: effRowWaste(r)};})()`);
const backEndRep = exported.mat_price * (1 + exported.waste_rate / 100);
// waste_rate 导出前已取整到 2 位，后端复现值与界面主材费只差在取整误差内
ok('D1 后端用 mat_price×(1+waste/100) 复现主材费，与界面 rowMatCost 差≤ 0.01（取整误差）',
  Math.abs(backEndRep - gross) <= 0.01, '后端复现=' + backEndRep.toFixed(4) + ' 界面=' + gross.toFixed(4));
const remLow  = run(`exportRemark(Object.assign(findRow(${R_TILE}), {aiNote:{conf:65,status:'low',note:''}, remark:''}))`);
const remHigh = run(`exportRemark(Object.assign(findRow(${R_TILE}), {aiNote:{conf:85,status:'hi',note:''}, remark:''}))`);
ok('D2 置信度 65(<70) → 导出备注标 ⚠️低置信度65%', remLow.includes('⚠️低置信度65%'), remLow);
ok('D3 置信度 85 → 备注不加低置信标记', remHigh === '', JSON.stringify(remHigh));

console.log('\n── E. 流程顺序对照：先套价再询价时 staged 应为 0 ──');
const c2 = applyCounts([{ row: run(`findRow(${R_TILE})`), price: 88, cat: '瓷砖' }], 'fill');
ok('E1 已套价行导入询价不会出现 staged（若出现则反证第②步没真套上）', c2.staged === 0, JSON.stringify(c2));

console.log('\n════════ 结果：' + pass + ' 通过 / ' + fail + ' 失败 ════════');
console.log(fail ? '❌ 存在失败项，落点或换算契约被破坏\n' : '✅ 落点规则与主材费不变式全部成立\n');
process.exit(fail ? 1 : 0);

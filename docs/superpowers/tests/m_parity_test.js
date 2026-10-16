/* 跨端一致性测试：同一份夹具，分别跑 tool.html 与 m.html 的函数实现，逐数值比对
 * ——「手机版与电脑端算出同一个数」的机器证据（spec §8.4）
 * 只读取 tool.html 源码，不修改它（电脑端零改动）。
 */
const fs = require('fs');
const vm = require('vm');

const TOOL = fs.readFileSync(__dirname + '/../../tool.html', 'utf8');
const MOBILE = fs.readFileSync(__dirname + '/../../m.html', 'utf8');

/* ── 抽取函数 / 常量声明 ──
 * 先跳过参数列表再配对花括号（naive 计数会在 `function makeRow(d={})` 的默认参数上提前归零），
 * 每抽一个都用 new Function 编译校验，抽取错位会直接报错而不是静默输出半截函数 */
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
  const pOpen = i + key.length - 1;
  const pClose = closeIdx(src, pOpen, '(', ')');
  const open = src.indexOf('{', pClose);
  const close = closeIdx(src, open, '{', '}');
  const code = src.slice(i, close + 1);
  try { new Function(code); } catch (e) { throw new Error('抽取 ' + name + ' 语法不完整: ' + e.message); }
  return code;
}
function grabDecl(src, decl) {   // decl 形如 'const MAT_CAT_KEYWORDS'
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

const FN_NAMES = ['normKey', 'countHit', 'colLetter', 'bigrams', 'jaccard', 'parseQuotePrice',
  'qHeaderScore', 'analyzeQuoteSheet', 'detectQuoteCategory', 'quoteColLabel', 'buildRowIndex', 'rowCatScore', 'catConverge', 'matchQuoteRow',
  'rebuildBenchMap', 'getBench', 'getAllRows', 'rebuildRowMap', 'findRow', 'makeRow',
  'effPrice', 'rowUnitPrice', 'rowMatCost', 'compUnitPrice', 'rowTotal', 'effRowMatPrice', 'rowWasteInfo', 'effRowWaste',
  'subCategoryScore', 'routeRowMat', 'syncRowMat', 'rowMatPending', 'rowMatStaged'];
const DECLS = ['const MAT_CAT_KEYWORDS', 'const QH_POS', 'const QH_NEG'];

function buildSandbox(src) {
  const ctx = vm.createContext({console, JSON, Math, Number, parseFloat, parseInt, String, Object, Array, isNaN, Set, Date, RegExp});
  const head = 'let groups=[], uid=1, rowMap=new Map(), DB={}, benchMap={}, ALL=[], SHEETS=[];' +
    'let globalCoef=1.0, globalMgmtRate=0, globalProfitRate=0, hourlyRate=350, priceLib={}, userPriceOverrides={};' +
    'let _quoteSheets=[];';
  const body = DECLS.map(d => { try { return grabDecl(src, d); } catch (e) { return ''; } }).join('\n') + '\n' +
    FN_NAMES.map(n => grabFn(src, n)).join('\n');
  vm.runInContext(head + '\n' + body, ctx);
  return ctx;
}
const A = buildSandbox(TOOL);      // 电脑端实现
const B = buildSandbox(MOBILE);     // 手机端实现
const run = (ctx, code) => vm.runInContext(code, ctx);

let pass = 0, fail = 0;
function same(name, a, b, tol) {
  const okk = (typeof a === 'number' && typeof b === 'number') ? Math.abs(a - b) <= (tol === undefined ? 1e-9 : tol) : JSON.stringify(a) === JSON.stringify(b);
  if (okk) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + '  电脑端=' + JSON.stringify(a) + ' / 手机端=' + JSON.stringify(b)); }
}

/* ── 同一份夹具分别注入两个沙箱 ── */
function fixture(ctx, variant) {
  run(ctx, `
    DB = {
      '泥水班组':[
        {id:'NS-015', name:'墙面铺贴-瓷砖', unit:'m2', price:50, waste_rate:5, auxType:'', auxFixedK:0, auxRateDetail:null},
        {id:'NS-020', name:'墙面铺贴-石材', unit:'m2', price:120, waste_rate:3, auxType:'', auxFixedK:0, auxRateDetail:null},
        {id:'NS-030', name:'墙面基层-抹灰', unit:'m2', price:28, waste_rate:0, auxType:'', auxFixedK:0, auxRateDetail:null},
      ],
      '木工班组':[
        {id:'MG-011', name:'饰面-木饰面', unit:'m2', price:180, waste_rate:8, auxType:'', auxFixedK:0, auxRateDetail:null},
        {id:'MG-012', name:'基层-木龙骨', unit:'m2', price:22, waste_rate:0, auxType:'', auxFixedK:0, auxRateDetail:null},
      ],
    };
    globalCoef=${variant === 'wild' ? 1.13 : 1.0}; globalMgmtRate=${variant === 'wild' ? 7 : 10}; globalProfitRate=${variant === 'wild' ? 12 : 15};
    priceLib={}; userPriceOverrides={};
    rebuildBenchMap();
    groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[
      Object.assign(makeRow({name:'石材墙面', spec:'150厚干挂', unit:'m2', qty:'10.5'}), {subs:[
        {bid:'NS-020', bsh:'泥水班组', coef:${variant === 'wild' ? 0.7 : 1.0}, conv:${variant === 'wild' ? 1.5 : 1.0}, matName:'石材', matPrice:200, wasteRate:3},
        {bid:'NS-030', bsh:'泥水班组', coef:${variant === 'wild' ? 0.35 : 0.5}, conv:2.0, matName:'', matPrice:20, wasteRate:0},
      ]}),
      Object.assign(makeRow({name:'瓷砖墙面', spec:'300×600', unit:'m2', qty:'8'}), {subs:[
        {bid:'NS-015', bsh:'泥水班组', coef:1.0, conv:1.0, matName:'瓷砖', matPrice:100, wasteRate:5},
      ]}),
      Object.assign(makeRow({name:'木饰面墙', spec:'硬包', unit:'m', qty:'26'}), {subs:[
        {bid:'MG-011', bsh:'木工班组', coef:1.0, conv:3.0, matName:'木饰面', matPrice:300, wasteRate:8},
        {bid:'MG-012', bsh:'木工班组', coef:1.0, conv:3.0, matName:'', matPrice:0, wasteRate:0},
      ]}),
      makeRow({name:'不锈钢线条', spec:'10mm', unit:'m', qty:'30'}),
      Object.assign(makeRow({name:'石材墙面', spec:'简装', unit:'m2', qty:'5'}), {matPrice:120, matName:'石材'}),
    ]}]}];
    uid = 500;
    groups[0].sections[0].rows.forEach((r, i) => { r.id = i + 10; });
    rebuildRowMap();
  `);
}
fixture(A, 'std'); fixture(B, 'std');

console.log('\n【1】计价数值：同一数据两端必须一模一样');
['rowUnitPrice', 'rowMatCost', 'compUnitPrice', 'rowTotal', 'effRowMatPrice', 'effRowWaste'].forEach(fn => {
  for (let i = 0; i < 5; i++) {
    const a = run(A, `(function(){try{return ${fn}(groups[0].sections[0].rows[${i}]);}catch(e){return 'ERR:'+e.message;}})()`);
    const b = run(B, `(function(){try{return ${fn}(groups[0].sections[0].rows[${i}]);}catch(e){return 'ERR:'+e.message;}})()`);
    if (a === 0 && b === 0) continue;
    same(`${fn}(第${i + 1}行)`, a, b, 1e-9);
  }
});
same('总合价', run(A, 'groups[0].sections[0].rows.reduce((s,r)=>s+rowTotal(r),0)'), run(B, 'groups[0].sections[0].rows.reduce((s,r)=>s+rowTotal(r),0)'), 1e-9);

fixture(A, 'wild'); fixture(B, 'wild');
same('乱参数下 rowMatCost（coef/conv/globalCoef 混合）', run(A, 'rowMatCost(groups[0].sections[0].rows[0])'), run(B, 'rowMatCost(groups[0].sections[0].rows[0])'), 1e-9);
same('乱参数下 effRowMatPrice', run(A, 'effRowMatPrice(groups[0].sections[0].rows[0])'), run(B, 'effRowMatPrice(groups[0].sections[0].rows[0])'), 1e-9);
same('乱参数下 effRowWaste', run(A, 'effRowWaste(groups[0].sections[0].rows[2])'), run(B, 'effRowWaste(groups[0].sections[0].rows[2])'), 1e-9);
same('不变式两端同成立（行主材费×量 = Σ子目主材费×子目量）',
  run(A, '(function(){const r=groups[0].sections[0].rows[0];const q=parseFloat(r.qty);const l=rowMatCost(r)*q;const s=r.subs.reduce((a,sb)=>a+sb.matPrice*(1+sb.wasteRate/100)*(q*sb.conv*sb.coef),0);return Math.abs(l-s)<1e-6;})()'),
  run(B, '(function(){const r=groups[0].sections[0].rows[0];const q=parseFloat(r.qty);const l=rowMatCost(r)*q;const s=r.subs.reduce((a,sb)=>a+sb.matPrice*(1+sb.wasteRate/100)*(q*sb.conv*sb.coef),0);return Math.abs(l-s)<1e-6;})()'));

console.log('\n【2】routeRowMat：五场景落点 + 落价结果');
const SCEN = [
  "routeRowMat(Object.assign(makeRow({name:'x'}), {id:900,subs:[]}), 100, '瓷砖', 'fill')",
  "routeRowMat(Object.assign(makeRow({name:'x'}), {id:901,subs:[{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]}), 100, '瓷砖', 'fill')",
  "(function(){const r=Object.assign(makeRow({name:'x'}),{id:902,subs:[{bid:'NS-030',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0},{bid:'NS-020',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]});const st=routeRowMat(r,300,'石材','fill');return st+'|'+r.subs.map(s=>s.matPrice).join(',');})()",
  "(function(){const r=Object.assign(makeRow({name:'x'}),{id:903,subs:[{bid:'NS-030',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0},{bid:'MG-011',bsh:'木工班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]});const st=routeRowMat(r,300,'','fill');return st+'|'+r.matPrice;})()",
  "(function(){const r=Object.assign(makeRow({name:'x'}),{id:904,subs:[{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'瓷砖',matPrice:88,wasteRate:0}]});const st=routeRowMat(r,100,'瓷砖','fill');return st+'|'+r.subs[0].matPrice;})()",
  "(function(){const r=Object.assign(makeRow({name:'x'}),{id:905,subs:[{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'瓷砖',matPrice:88,wasteRate:0}]});const st=routeRowMat(r,100,'瓷砖','over');return st+'|'+r.subs[0].matPrice;})()",
  "(function(){const r=Object.assign(makeRow({name:'x'}),{id:906,subs:[],matPrice:50});const st=routeRowMat(r,100,'瓷砖','fill');return st+'|'+r.matPrice;})()",
];
SCEN.forEach((s, i) => { same('场景 ' + (i + 1), run(A, s), run(B, s)); });

console.log('\n【3】询价匹配：同一批报价行两端判定一致');
const QUERIES = [
  ['瓷砖墙面', '300×600', 'm2', ''], ['瓷砖墙面', '别的', 'm2', ''], ['瓷砖墙面', '别的', '㎡', ''],
  ['石材墙面', '随便写', 'm2', ''], ['石材墙面', '随便写', 'm2', '石材'], ['石材墙面', '别的', 'm', ''],
  ['不锈钢线条', '10mm', 'm', ''], ['背景墙', '乳胶漆', 'm2', ''], ['木饰面墙', '硬包', 'm', '木饰面/木门/柜体'],
  ['供应商增项XYZ', '', 'm2', ''], ['木饰面墙收口', '硬包处理', 'm', ''],
];
['', '石材', '瓷砖'].forEach(cat => {
  const res = QUERIES.map(q => run(A, `JSON.stringify((function(){const m=matchQuoteRow({name:${JSON.stringify(q[0])},spec:${JSON.stringify(q[1])},unit:${JSON.stringify(q[2])}}, getAllRows(), ${JSON.stringify(cat)}, buildRowIndex(getAllRows())); return {how:m.how, sim:m.sim||0, row:m.row?m.row.name+'@'+m.row.spec:null, cands:m.cands?m.cands.length:0};})())`));
  const res2 = QUERIES.map(q => run(B, `JSON.stringify((function(){const m=matchQuoteRow({name:${JSON.stringify(q[0])},spec:${JSON.stringify(q[1])},unit:${JSON.stringify(q[2])}}, getAllRows(), ${JSON.stringify(cat)}, buildRowIndex(getAllRows())); return {how:m.how, sim:m.sim||0, row:m.row?m.row.name+'@'+m.row.spec:null, cands:m.cands?m.cands.length:0};})())`));
  same('品类「' + (cat || '不校验') + '」全部 ' + QUERIES.length + ' 条判定', res.join(' | '), res2.join(' | '));
});

console.log('\n【4】Excel 解析：列画像与表头识别');
const QB = `
_quoteSheets = [];
const _data = [
  ['序号','项目名称','项目特征','计量单位','工程量','主材单价','人工费','综合单价'],
  ['1','瓷砖墙面','300×600','m2',8,180,50,300],
  ['2','石材墙面','150厚干挂','m2',10.5,300,120,600],
  ['3','木饰面墙','硬包','m',26,320,100,520],
];
const _ns = new Set(getAllRows().map(r=>normKey(r.name)).filter(Boolean));
const _us = new Set(getAllRows().map(r=>normKey(r.unit)).filter(Boolean));
const _qs = new Set(getAllRows().map(r=>(parseFloat(r.qty)||0).toFixed(4)));
JSON.stringify((function(){const s=analyzeQuoteSheet(_data,_ns,_us,_qs,'Sheet1'); return {hdr:s.hdr, cols:s.cols, cands:s.cands.map(c=>c.col), labels: s.cands.map(c => quoteColLabel(c))};})())`;
same('analyzeQuoteSheet（表头/语义列/填价列候选）', run(A, QB), run(B, QB));
/* 品类识别只比 cat/score；why 是 UI 文案，各自与自己的下拉选项用词保持一致，不入契约 */
const DC = (args) => `JSON.stringify((function(){const r=detectQuoteCategory(${args});return {cat:r.cat, score:r.score, whyOk:!!r.why};})())`;
same('品类识别（文件名+内容）', run(A, DC(`'石材报价单.xlsx',['Sheet1'],'大理石 300 石英石'`)), run(B, DC(`'石材报价单.xlsx',['Sheet1'],'大理石 300 石英石'`)));
same('品类识别（无关键词）', run(A, DC(`'报价.xlsx',['Sheet1'],' abc '`)), run(B, DC(`'报价.xlsx',['Sheet1'],' abc '`)));
same('表头打分（主材/综合/人工）', run(A, `JSON.stringify([qHeaderScore('主材单价'),qHeaderScore('综合单价'),qHeaderScore('人工费'),qHeaderScore('工程量')])`), run(B, `JSON.stringify([qHeaderScore('主材单价'),qHeaderScore('综合单价'),qHeaderScore('人工费'),qHeaderScore('工程量')])`));

/* ──【5】F3 gtype 护栏对偶：集团子目不被 matPrice 写入（纯集团行 + 混合行，两个入口）── */
console.log('\n【5】F3 gtype 护栏：集团子目不被 matPrice 写入（两端对偶）');
const GUARD_CODE = `(function(){
  groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[
    Object.assign(makeRow({name:'集团行', unit:'m2', qty:'1'}), {id:910, matPrice:0, matName:'', subs:[{bid:'ZS02-A-009',bsh:'ZS02-A',gtype:'group',coef:1,conv:1,lab:61.65,aux:0,mech:0,matName:'',matPrice:0,wasteRate:0,mats:[{name:'瓷砖',price:null,consumption:1.4469}]}]}),
    Object.assign(makeRow({name:'混合行', unit:'m2', qty:'1'}), {id:911, matPrice:0, matName:'瓷砖', subs:[{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'瓷砖',matPrice:0,wasteRate:5},{bid:'ZS02-D-003',bsh:'ZS02-D',gtype:'group',coef:1,conv:1,lab:1.51,aux:0,mech:0,matPrice:0,wasteRate:0,mats:[]}]})
  ]}]}];
  rebuildRowMap();
  var st1 = routeRowMat(findRow(910), 100, '瓷砖', 'over');   // 纯集团行：连 over 模式也不落点
  var st2 = routeRowMat(findRow(911), 100, '瓷砖', 'over');   // 混合行（内部+集团）：整行不落点
  findRow(910).matPrice = 88; syncRowMat(910);                // 行级暂存价分配入口
  findRow(911).matPrice = 66; syncRowMat(911);
  return JSON.stringify({st1:st1, st2:st2, g910:findRow(910).subs.map(s=>s.matPrice), g911:findRow(911).subs.map(s=>s.matPrice)});
})()`;
const gA = run(A, GUARD_CODE), gB = run(B, GUARD_CODE);
same('routeRowMat/syncRowMat gtype 护栏两端行为一致', gA, gB);
const GJ = JSON.parse(gA);
function okD(name, cond, detail) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + ' → ' + detail); } }
okD('护栏：两行均返回 kept（不落点、原值不动）', GJ.st1 === 'kept' && GJ.st2 === 'kept', gA);
okD('护栏：集团子目 matPrice 未被写入（纯集团行/混合行均为 0）',
  GJ.g910.length === 1 && GJ.g910[0] === 0 && GJ.g911.length === 2 && GJ.g911[0] === 0 && GJ.g911[1] === 0, gA);

console.log('\n────────────────────────────');
console.log('两端一致 ' + pass + ' / ' + (pass + fail) + (fail ? '  ❌ 差异 ' + fail : '  ✅ 无差异（电脑端零改动，仅读取）'));
process.exit(fail ? 1 : 0);

/* m.html 逻辑回归测试：在 Node 里用 stub DOM 跑真实函数（不开浏览器） */
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync(__dirname + '/../../m.html', 'utf8');
const blocks = [...html.matchAll(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const src = blocks.join('\n;\n');

/* ── stub ── */
const els = {};
function mkEl(id) {
  return {id, _html: '', value: '', textContent: '', checked: false, disabled: false,
    classList: {add(){}, remove(){}, toggle(){}, contains(){return false}},
    style: {}, addEventListener(){}, appendChild(){}, remove(){}, querySelectorAll(){return []},
    get innerHTML() { return this._html; }, set innerHTML(v) { this._html = v; },
    closest(){ return null; }, insertBefore(){} };
}
global.document = {getElementById(id) { return els[id] || (els[id] = mkEl(id)); }, createElement(t) { return mkEl('tmp_' + Math.random()); },
  body: {appendChild(){}, removeChild(){}}, querySelectorAll() { return []; }, querySelector() { return null; }, addEventListener(){}};
global.window = global;
global.localStorage = {getItem(){return null}, setItem(){}, removeItem(){}};
global.location = {hostname: 'localhost', href: ''};
global.navigator = {canShare(){return false}};
global.fetch = async () => ({ok: false, status: 0, json: async () => [], text: async () => '', blob: async () => ({})});
global.XLSX = {
  read: () => ({SheetNames: [], Sheets: {}}),
  utils: {sheet_to_json: () => [], decode_range: () => ({s:{r:0,c:0}, e:{r:0,c:0}}), encode_cell: () => 'A1'},
};
global.confirm = () => true;
global.alert = () => {};
global.setTimeout = (fn) => 0;   // 让 debounce 不自动触发，测试自己显式调用

const ctx = vm.createContext(global);
vm.runInContext(src, ctx);
const G = k => vm.runInContext(k, ctx);

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (extra !== undefined ? '  → ' + JSON.stringify(extra) : '')); }
}
function eq(name, a, b) { ok(name + ' (' + JSON.stringify(a) + ' === ' + JSON.stringify(b) + ')', Math.abs(a - b) < 1e-9, {a, b}); }

/* ── 造基准价库 ── */
G(`
DB = {};
DB['泥水班组'] = [
  {id:'NS-015', name:'墙面铺贴-瓷砖', unit:'m2', price:50, waste_rate:5, auxType:'RATE', auxFixedK:2, auxRateDetail:{type:'RATE', materialName:'水泥', consume:0.5}},
  {id:'NS-020', name:'墙面铺贴-石材', unit:'m2', price:120, waste_rate:3, auxType:'', auxFixedK:0, auxRateDetail:null},
  {id:'NS-030', name:'墙面基层-抹灰', unit:'m2', price:28, waste_rate:0, auxType:'', auxFixedK:0, auxRateDetail:null},
];
DB['木工班组'] = [
  {id:'MG-010', name:'天棚吊顶-石膏板', unit:'m2', price:65, waste_rate:0, auxType:'', auxFixedK:0, auxRateDetail:null},
  {id:'MG-011', name:'饰面-木饰面', unit:'m2', price:180, waste_rate:8, auxType:'', auxFixedK:0, auxRateDetail:null},
];
ALL=[]; Object.keys(DB).forEach(sh=>DB[sh].forEach(it=>ALL.push(Object.assign({},it,{sheet:sh}))));
SHEETS=Object.keys(DB); rebuildBenchMap();
priceLib = {'水泥':{price:6,unit:'kg'}};
userPriceOverrides = {};
globalCoef = 1.0; globalMgmtRate = 10; globalProfitRate = 15;
`);

console.log('\n【A】计价不变式（coef / conv / 损耗率）');
G(`
groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部一', open:true, rows:[
  Object.assign(makeRow({name:'石材墙面', unit:'m2', qty:'10'}), {subs:[
    {bid:'NS-020', bsh:'泥水班组', coef:1.0, conv:1.0, matName:'石材', matPrice:200, wasteRate:3},
    {bid:'NS-030', bsh:'泥水班组', coef:0.5, conv:2.0, matName:'', matPrice:20, wasteRate:0},
  ]}),
  Object.assign(makeRow({name:'瓷砖墙面', unit:'m2', qty:'8'}), {subs:[
    {bid:'NS-015', bsh:'泥水班组', coef:1.0, conv:1.0, matName:'瓷砖', matPrice:100, wasteRate:5},
  ]}),
]}]}];
uid = 999; rebuildRowMap(); recomputeAllAux();
`);
// 行主材单价 × 行工程量 = Σ(子目主材费 × 子目工程量)，子目工程量 = 行量 × conv × coef
const inv = G(`(function(){
  const r = groups[0].sections[0].rows[0];
  const lhs = rowMatCost(r) * 10;
  const rhs = r.subs.reduce((s,sb)=> s + (sb.matPrice*(1+sb.wasteRate/100)) * (10*sb.conv*sb.coef), 0);
  return {lhs:lhs, rhs:rhs};
})()`);
eq('多子目含 coef/conv 主材费守恒', inv.lhs, inv.rhs);
eq('行主材费 = 200×1.03 + 20×1.0×0.5×2', G('rowMatCost(groups[0].sections[0].rows[0])'), 200 * 1.03 + 20);
eq('人工单价 = 120 + 28×0.5×2', G('rowUnitPrice(groups[0].sections[0].rows[0])'), 120 + 28);
eq('综合单价 = 人工+主材+辅材+管+利', G('compUnitPrice(groups[0].sections[0].rows[0])'),
   (120 + 28) + (200 * 1.03 + 20) + G('parseFloat(groups[0].sections[0].rows[0].auxCost)') + (120 + 28) * 0.1 + (120 + 28) * 0.15);
eq('辅材费走配方（NS-015: 固定2 + 水泥6×0.5）', G('computeAuxForSub({bid:"NS-015",bsh:"泥水班组"})'), 2 + 3);
const rt = G('(function(){const r=groups[0].sections[0].rows[1];const lab=rowUnitPrice(r);return (lab+rowMatCost(r)+parseFloat(r.auxCost)+lab*0.1+lab*0.15)*8;})()');
eq('行合价（公式口径）', G('rowTotal(groups[0].sections[0].rows[1])'), rt);
ok('effRowMatPrice × (1+等效损耗) 与 rowMatCost 同口径',
   Math.abs(G('effRowMatPrice(groups[0].sections[0].rows[0])') * (1 + G('effRowWaste(groups[0].sections[0].rows[0])') / 100) - G('rowMatCost(groups[0].sections[0].rows[0])')) < 0.01,
   G('[effRowMatPrice, effRowWaste, rowMatCost]'));

console.log('\n【B】routeRowMat 落点状态机');
G(`function freshRow(subs, matPrice){ const r = makeRow({name:'x', unit:'m2', qty:'1'}); r.subs = subs; r.matPrice = matPrice||0; return r; }`);
ok('未套价 → staged（暂存行上）', G(`routeRowMat(freshRow([]), 100, '瓷砖', 'fill')`) === 'staged');
ok('唯一子目 → assigned', G(`routeRowMat(freshRow([{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]), 100, '瓷砖', 'fill')`) === 'assigned');
ok('同品类落到正确子目', G(`(function(){const r=freshRow([{bid:'NS-030',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0},{bid:'NS-020',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]);const st=routeRowMat(r,300,'石材','fill');return st==='assigned'&&r.subs[1].matPrice===300&&r.subs[0].matPrice===0;})()`));
ok('多子目且无品类 → pending（不猜）', G(`routeRowMat(freshRow([{bid:'NS-030',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0},{bid:'MG-010',bsh:'木工班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}]), 300, '', 'fill')`) === 'pending');
ok('已有价 fill → kept', G(`routeRowMat(freshRow([{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'瓷砖',matPrice:88,wasteRate:0}]), 100, '瓷砖', 'fill')`) === 'kept');
ok('已有价 over → assigned 覆盖', G(`(function(){const r=freshRow([{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'瓷砖',matPrice:88,wasteRate:0}]);const st=routeRowMat(r,100,'瓷砖','over');return st==='assigned'&&r.subs[0].matPrice===100;})()`));
ok('暂存价不被第二条报价覆盖（kept）', G(`routeRowMat(freshRow([], 50), 100, '瓷砖', 'fill')`) === 'kept');
ok('套价继承：syncRowMat 把行价分到唯一空子目', G(`(function(){const r=freshRow([{bid:'NS-015',bsh:'泥水班组',coef:1,conv:1,matName:'',matPrice:0,wasteRate:0}],100);r.id=777;groups[0].sections[0].rows.push(r);rebuildRowMap();syncRowMat(777);return r.subs[0].matPrice===100;})()`));

console.log('\n【C】matchQuoteRow 四级匹配 + 品类收敛');
G(`
groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[
  makeRow({name:'石材墙面', spec:'150厚干挂', unit:'m2', qty:'10'}),
  makeRow({name:'瓷砖墙面', spec:'300×600', unit:'m2', qty:'20'}),
  makeRow({name:'不锈钢线条', spec:'10mm', unit:'m', qty:'30'}),
  makeRow({name:'石材墙面', spec:'简装', unit:'m2', qty:'5'}),
  makeRow({name:'背景墙', spec:'石材干挂', unit:'m2', qty:'6'}),
  makeRow({name:'背景墙', spec:'乳胶漆', unit:'m2', qty:'7'}),
]}]}];
rebuildRowMap();
const ROWS = getAllRows();
const IDX = buildRowIndex(ROWS);
function M(name, spec, unit){ return matchQuoteRow({name:name, spec:spec, unit:unit}, ROWS, '', IDX); }
`);
ok('exact：名称+特征+单位全等', G(`M('瓷砖墙面','300×600','m2').how`) === 'exact');
ok('nameunit：特征对不上但名称+单位唯一', G(`M('不锈钢线条','别的','m').how`) === 'nameunit');
ok('nameonly：单位不一致 → 仅名称', G(`M('瓷砖墙面','别的','㎡').how`) === 'nameonly');
ok('ambiguous：同名两行且品类不收人 → 多候选', G(`M('石材墙面','别的','m2').how`) === 'ambiguous', G(`M('石材墙面','别的','m2')`));
ok('cat 收敛：同名两行靠品类关键词定到唯一行', G(`matchQuoteRow({name:'背景墙',spec:'随便写',unit:'m2'}, ROWS, '石材', IDX).how`) === 'cat'
   && G(`(function(){const m=matchQuoteRow({name:'背景墙',spec:'随便写',unit:'m2'}, ROWS, '石材', IDX); return m.row && m.row.spec==='石材干挂';})()`));
ok('similar：2-gram 兼容名称额外后缀（不锈钢线条收口 → 不锈钢线条）', G(`(function(){const m=M('不锈钢线条收口','10mm','m'); return m.how==='similar'&&m.sim>=60;})()`), G(`M('不锈钢线条收口','10mm','m')`));
ok('none：完全找不到', G(`M('供应商增项XYZ','','m2').how`) === 'none');
ok('normKey 大小写/空格归一（M 2 / m2）', G(`normKey(' M2 ')`) === 'm2');

console.log('\n【D】buildQuoteItems 默认勾选 + 三分类');
G(`
_quoteSheets = [{sheet:'Sheet1', cols:{name:0, spec:1, unit:2, qty:3}, body:[
  ['瓷砖墙面','300×600','m2',20,180],
  ['不锈钢线条','10mm','m',30,60],
  ['石材墙面','150厚干挂','m',10,300],
  ['石材墙面','随便写','m2',5,260],
  ['供应商增项XYZ','','m2',3,50],
  ['瓷砖墙面','别的特征','m2',1,'不报价'],
]}];
_quoteProf = [];
_quoteCat = '';
_quoteCol = 4;
_quoteItems = buildQuoteItems('', 4);
_quoteMatched = true;
_g = classifyQuote(_quoteItems);
`);
ok('① 精确 → 自动匹配且默认勾选', G(`(_quoteItems[0].match.how==='exact' && _quoteItems[0].checked && _g.ok.indexOf(_quoteItems[0])>=0)`));
ok('② 名称+单位全等 → 自动匹配', G(`(_quoteItems[1].match.how==='exact' && _quoteItems[1].checked)`));
ok('③ 单位不一致 m↔㎡ → 多候选归待确认且不劾选', G(`(function(){const it=_quoteItems[2]; return (it.match.how==='ambiguous'||it.match.how==='nameonly') && !it.checked && _g.warn.indexOf(it)>=0;})()`));
ok('④ 同名行默认不劾选（交人工）', G(`!_quoteItems[3].checked`));
ok('⑤ 未匹配 → none 且不可劾选', G(`(_quoteItems[4].match.how==='none') && !_quoteItems[4].checked`));
ok('⑥ 文本"不报价"→ skip 不计入未匹配', G(`_quoteItems[5].kind === 'skip' && _g.skip === 1`));
ok('分类总数守恒 ok+warn+none+skip = items', G(`_g.ok.length + _g.warn.length + _g.none.length + _g.skip === _quoteItems.length`),
   G(`[_g.ok.length,_g.warn.length,_g.none.length,_g.skip.length]`));
ok('疑非本类 catWarn 归入待确认', G(`(function(){const it=_quoteItems[0]; it.catWarn=true; it.checked=false; const g=classifyQuote(_quoteItems); return g.warn.indexOf(it)>=0 && g.ok.indexOf(it)<0;})()`));

console.log('\n【E】applyQuote 落点 + 导出 payload 契约');
G(`
// 重置一个已套价项目：瓷砖墙面 1 子目，石材墙面 2 子目
groups = [{id:1, sheetName:'S', open:true, sections:[{id:2, name:'分部', open:true, rows:[]}]}];
const sec = groups[0].sections[0];
const rA = makeRow({name:'瓷砖墙面', spec:'300×600', unit:'m2', qty:'20'});
rA.subs = [{bid:'NS-015', bsh:'泥水班组', coef:1, conv:1, matName:'', matPrice:0, wasteRate:5}];
const rB = makeRow({name:'石材墙面', spec:'150厚干挂', unit:'m2', qty:'10'});
rB.subs = [{bid:'NS-030', bsh:'泥水班组', coef:1, conv:1, matName:'', matPrice:0, wasteRate:0},
           {bid:'NS-020', bsh:'泥水班组', coef:1, conv:1, matName:'', matPrice:0, wasteRate:3}];
sec.rows.push(rA, rB);
uid = 500; rebuildRowMap();
_quoteItems = buildQuoteItems('瓷砖', 4);
`);
const ap = G(`(function(){
  const items = [
    {name:'瓷砖墙面', price:180, cat:'瓷砖', match:{row: rA, how:'exact'}, checked:true, kind:'num'},
    {name:'石材墙面', price:300, cat:'石材', match:{row: rB, how:'exact'}, checked:true, kind:'num'},
  ];
  const done = {}; let assigned=0, staged=0, pending=0, kept=0;
  items.forEach(it=>{ if(done[it.match.row.id]) return; done[it.match.row.id]=1;
    const st = routeRowMat(it.match.row, it.price, it.cat, 'fill');
    if(st==='assigned')assigned++; else if(st==='staged')staged++; else if(st==='pending')pending++; else kept++; });
  return {assigned:assigned, kept:kept, a:rA.subs[0].matPrice, b0:rB.subs[0].matPrice, b1:rB.subs[1].matPrice};
})()`);
ok('瓷砖报价落到瓷砖子目', ap.a === 180, ap);
ok('石材报价按品类落石材子目（不是抹灰子目）', ap.b0 === 0 && ap.b1 === 300 && ap.assigned === 2, ap);
const pl = G(`(function(){const p=collectExportData(); return {keys:Object.keys(p).sort(), cols:p.columns.map(c=>c.key), g0:p.groups[0].sections[0].rows.map(r=>Object.keys(r).sort())};})()`);
const EXPECT_TOP = ['columns','contract_amount','group_folding','groups','include_summary_sheet','mgmt_rate','profit_rate','project_name','show_subs','split_by_group','target_profit_rate','use_formula'];
ok('导出顶层字段与桌面端 collectExportData 一致', JSON.stringify(pl.cols.sort()) === JSON.stringify(['code','mat','mat_price','name','qty','remark','seq','spec','total','unit','usp']) && JSON.stringify(pl.keys) === JSON.stringify(EXPECT_TOP), pl.keys);
const EXP_ROW = ['aux_cost','labor_price','mat_price','name','qty','remark','seq','spec','subs','unit','waste_rate'];
ok('导出行字段全集一致', pl.g0.every(k => JSON.stringify(k) === JSON.stringify(EXP_ROW)), pl.g0);
ok('子目字段契约（bid/name/spec/unit/coef/conv/unit_price/mat_price/waste_rate）',
   JSON.stringify(G(`Object.keys(collectExportData().groups[0].sections[0].rows[1].subs[0]).sort()`)) ===
   JSON.stringify(['bid','coef','conv','mat_price','name','spec','unit','unit_price','waste_rate'].sort()),
   G(`Object.keys(collectExportData().groups[0].sections[0].rows[1].subs[0])`));
eq('导出 mat_price = 净料×含量×换算（石材 300）', G(`collectExportData().groups[0].sections[0].rows[1].mat_price`), 300);
eq('导出 waste_rate = 等效损耗（3%×占比）', G(`Math.round(collectExportData().groups[0].sections[0].rows[1].waste_rate*100)/100`), G(`Math.round(effRowWaste(rB)*100)/100`));

console.log('\n【F】草稿 payload schema（tool.html doAutoSave 字段全集）');
G(`CURRENT_USER = {id:'test-uuid', email:'t@example.com'};`);
const dp = G(`(function(){const p=buildDraftPayload(true); return Object.keys(p).sort();})()`);
const DRAFT_KEYS = ['contract_amount','created_at','global_coef','groups_json','hourly_rate','is_draft','mgmt_rate','name','price_overrides','priced_count','profit_rate','proj_date','proj_team','row_count','target_profit_rate','user_id'];
ok('草稿字段全集 = tool.html 的 16 个字段', JSON.stringify(dp) === JSON.stringify(DRAFT_KEYS), dp);
const rkeys = G(`(function(){const r=groups[0].sections[0].rows[0]; return Object.keys(r).sort().join(',');})()`);
const ROW_KEYS = ['aiNote','auxCost','hourlyMode','id','matName','matPrice','name','open','qty','remark','spec','subs','unit','wasteRate'];
ok('行字段全集 = makeRow() 契约', rkeys === ROW_KEYS.join(','), rkeys);
const skeys = G(`Object.keys(groups[0].sections[0].rows[0].subs[0]).sort().join(',')`);
ok('子目字段全集 = addSub() 契约', skeys === ['bid','bsh','coef','conv','matName','matPrice','wasteRate'].sort().join(','), skeys);
ok('makeRow 与 tool.html 完全同构（空行）',
   JSON.stringify(G(`makeRow({name:'a',unit:'m2'})`)).replace(/,?"id":\d+/, '"id":1') ===
   JSON.stringify({id:1, name:'a', spec:'', unit:'m2', qty:'', remark:'', open:false, subs:[], aiNote:null, hourlyMode:false, matName:'', matPrice:0, wasteRate:0, auxCost:0}));

console.log('\n【G】BOQ 解析契约（stub XLSX）');
G(`
XLSX = {utils:{sheet_to_json: () => [
  ['装修工程',''  ,''],
  ['序号','项目名称','项目特征','计量单位','工程量','备注'],
  ['','壹、地面工程','','','',''],
  ['1','地面瓷砖铺贴','300×300','m2','120',''],
  ['2','石材门槛石','','m','15',''],
  ['','贰、墙面工程','','','',''],
  ['3','墙面刮腻子','二遍','m2','300',''],
  ['','','','','',''],
  ['','合计','','','',''],
]}, SheetNames:['BOQ'], Sheets:{BOQ:{}}};
// 表头必须含「项目名称」才被认为有效表
XLSX.utils.sheet_to_json = () => [
  ['序号','项目名称','项目特征','计量单位','工程量','备注'],
  ['','壹、地面工程','','','',''],
  ['1','地面瓷砖铺贴','300×300','m2','120',''],
  ['2','石材门槛石','','m','15',''],
  ['','贰、墙面工程','','','',''],
  ['3','墙面刮腻子','二遍','m2','300',''],
];
_g2 = parseBoqWorkbook({SheetNames:['BOQ'], Sheets:{BOQ:{}}});
`);
ok('识别 3 条清单行（跳过分部标题与空行）', G(`_g2.total`) === 3, G(`[_g2.total, _g2.skip]`));
ok('分部标题识别为 section（2 个分部）', G(`_g2.groups[0].sections.length`) === 2, G(`_g2.groups[0].sections.map(s=>s.name)`));
ok('分部名正确', G(`_g2.groups[0].sections.map(s=>s.name).join('|')`) === '壹、地面工程|贰、墙面工程');
ok('列映射正确（名称/特征/单位/工程量/备注）',
   G(`(function(){const r=_g2.groups[0].sections[0].rows[0];return r.name==='地面瓷砖铺贴'&&r.spec==='300×300'&&r.unit==='m2'&&r.qty==='120';})()`));
ok('末行「合计」（有名称无单位无量）被当分部标题而非清单行', G(`_g2.groups[0].sections.reduce((a,s)=>a+s.rows.length,0)`) === 3);
ok('导入后行对象含 makeRow 全字段', G(`Object.keys(_g2.groups[0].sections[0].rows[0]).length`) === 14);

console.log('\n【H】询价 Excel 列画像（填价列识别）');
G(`
const data = [
  ['序号','项目名称','项目特征','计量单位','工程量','主材单价'],
  ['1','瓷砖墙面','300×600','m2',20,180],
  ['2','石材墙面','干挂','m2',10,300],
];
const nameSet = new Set(getAllRows().map(r=>normKey(r.name)).filter(Boolean));
const unitSet = new Set(getAllRows().map(r=>normKey(r.unit)).filter(Boolean));
const qtySet = new Set(getAllRows().map(r=>(parseFloat(r.qty)||0).toFixed(4)));
_sh = analyzeQuoteSheet(data, nameSet, unitSet, qtySet, 'Sheet1');
`);
ok('表头行 = 0', G(`_sh.hdr`) === 0);
ok('语义列识别（name=1, unit=3, qty=4）', G(`_sh.cols.name===1 && _sh.cols.unit===3 && _sh.cols.qty===4`), G(`_sh.cols`));
ok('填价列候选首选 = 主材单价列(5)', G(`_sh.cands[0].col`) === 5, G(`_sh.cands.map(c=>c.col)`));
ok('工程量列不被误判为填价列', G(`!_sh.cands.some(c=>c.col===4)`));
ok('品类识别：文件名含「石材」', G(`detectQuoteCategory('石材报价单.xlsx', ['Sheet1'], '大理石 300').cat`) === '石材');
ok('含税/综合价表头被降权（不首选）', G(`qHeaderScore('综合单价')`) < G(`qHeaderScore('主材单价')`), G(`[qHeaderScore('综合单价'), qHeaderScore('主材单价')]`));

console.log('\n────────────────────────────');
console.log('通过 ' + pass + ' / ' + (pass + fail) + (fail ? '  ❌ 失败 ' + fail : '  ✅ 全部通过'));
process.exit(fail ? 1 : 0);

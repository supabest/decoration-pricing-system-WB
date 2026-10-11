/* 子目字段编辑 → 清单行派生单元格刷新验证（只读 tool.html，不修改它）
 * 背景 bug：改子目损耗率/主材价/系数/换算后只调 updateSum()（仅刷底部总计），
 * 清单行上的 损耗率/主材单价/主材费 单元格不重渲染 → 显示旧值。
 * 契约：三个 upd* 处理器必须在写值后触发 renderBoq()。
 * 运行：node docs/superpowers/tests/sub_edit_refresh_test.js
 */
const fs = require('fs');
const vm = require('vm');

const TOOL = fs.readFileSync(__dirname + '/../../tool.html', 'utf8');

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

const FNS = ['updSubField', 'updCoef', 'updConv'];

const ctx = vm.createContext({ console, parseFloat, isNaN, String });
// updateSum / renderBoq 用计数器桩替代：本测试只验证「写值后刷新链路」的接线，不跑真实渲染
vm.runInContext(
  'let _sum=0, _render=0;' +
  'function updateSum(){_sum++;}' +
  'function renderBoq(){_render++;}' +
  'let rowMap = new Map([["r1",{id:"r1",matPrice:0,subs:[{bid:"B1",bsh:"S1",coef:1,conv:1,matPrice:100,wasteRate:0}]}]]);' +
  'function findRow(rid){return rowMap.get(rid)||null;}' +
  FNS.map(n => grabFn(TOOL, n)).join('\n'),
  ctx);
const run = c => vm.runInContext(c, ctx);

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? '  → ' + detail : '')); }
}

console.log('\n── 子目字段编辑处理器的刷新链路 ──');
run('_sum=0;_render=0;');
ok('T1 updSubField 改损耗率 → 数据写入', run(`updSubField("r1","B1","S1","wasteRate","5"), rowMap.get("r1").subs[0].wasteRate === "5"`));
ok('T2 updSubField 改损耗率 → 触发 renderBoq（清单行损耗率/主材费才跟着刷）', run('_render') === 1, 'renderBoq 调用次数=' + run('_render'));
ok('T3 updSubField 仍调用 updateSum（底部总计照旧更新）', run('_sum') === 1, 'updateSum 调用次数=' + run('_sum'));

run('_sum=0;_render=0;');
run(`updSubField("r1","B1","S1","matPrice","120")`);
ok('T4 updSubField 改主材价 → 触发 renderBoq', run('_render') === 1, 'renderBoq 调用次数=' + run('_render'));

run('_sum=0;_render=0;');
run(`updCoef("r1","B1","S1","2")`);
ok('T5 updCoef 改子目系数 → 触发 renderBoq', run('_render') === 1, 'renderBoq 调用次数=' + run('_render'));
ok('T6 updCoef 系数仍写入并 parseFloat', run(`rowMap.get("r1").subs[0].coef === 2`));

run('_sum=0;_render=0;');
run(`updConv("r1","B1","S1","1.5")`);
ok('T7 updConv 改换算系数 → 触发 renderBoq', run('_render') === 1, 'renderBoq 调用次数=' + run('_render'));
ok('T8 updConv 换算仍写入并 parseFloat', run(`rowMap.get("r1").subs[0].conv === 1.5`));

run('_sum=0;_render=0;');
run(`updSubField("ghost","B1","S1","wasteRate","5")`);
ok('T9 行不存在时不写不刷（无副作用）', run('_sum') === 0 && run('_render') === 0);

console.log('\n── 清单行损耗率计算本身（证明 bug 只在刷新链路，不在算法）──');
const calcCtx = vm.createContext({ console, Math, JSON, parseFloat, isNaN, String, Number, Object, Array });
vm.runInContext(
  'let subs=[];' +
  'function rowMatCost(r){return r.subs.reduce((sum,sub)=>{const smp=parseFloat(sub.matPrice)||0;const swr=parseFloat(sub.wasteRate)||0;const cf=parseFloat(sub.coef)||1.0;const cv=parseFloat(sub.conv)||1.0;return sum+smp*(1+swr/100)*cf*cv;},0);}' +
  grabFn(TOOL, 'rowWasteInfo').replace('rowWasteInfo', 'rowWasteInfo') , calcCtx);
const calc = c => vm.runInContext(c, calcCtx);
const effAfterEdit = calc(`(function(){ var r={subs:[{matPrice:100,wasteRate:5,coef:1,conv:1}]}; return rowWasteInfo(r).eff; })()`);
ok('T10 单子目 matPrice=100 损耗5% → 行等效损耗率=5', Math.abs(effAfterEdit - 5) < 1e-9, 'eff=' + effAfterEdit);
const effTwo = calc(`(function(){ var r={subs:[{matPrice:100,wasteRate:5,coef:1,conv:1},{matPrice:100,wasteRate:15,coef:1,conv:1}]}; return rowWasteInfo(r).eff; })()`);
ok('T11 双子目 5%/15% 等价 → 行等效损耗率=10（算法正确，缺的是重渲染）', Math.abs(effTwo - 10) < 1e-9, 'eff=' + effTwo);

console.log('\n════════ 结果：' + pass + ' 通过 / ' + fail + ' 失败 ════════');
console.log(fail ? '❌ 刷新链路未接通：子目编辑后清单行派生单元格不会变化\n' : '✅ 子目字段编辑均触发清单行重渲染，算法与链路都成立\n');
process.exit(fail ? 1 : 0);

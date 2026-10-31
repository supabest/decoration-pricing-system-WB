/* 离线兜底三级退（loadFallbackBench / _wasteRates）双端对偶验证
 * 背景：497 条价表与损耗率不再以明文发布到 Pages。Supabase 不可达时，兜底顺序必须是
 *   ① 后端解密快照（带 sb-access-token，走 /api/v1/benchmark/snapshot）
 *   ② 同目录明文 JSON（本机开发；该文件已 .gitignore，线上 404）
 *   ③ null → 调用方退回内置 4 条
 * 契约：外部（无 token）不得向后端要快照——那是保密边界的另一道门；
 *       tool.html 与 m.html 同名函数行为逐案一致（同源同形）。
 * 运行：node docs/superpowers/tests/bench_fallback_test.js
 */
const fs = require('fs');
const vm = require('vm');

const FILES = {
  'tool.html': __dirname + '/../../tool.html',
  'm.html': __dirname + '/../../m.html',
};
const FNS = ['loadFallbackBench', '_wasteRates'];
const BE = 'http://test-be';

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
function grabAsyncFn(src, name, fileName) {
  const key = 'async function ' + name + '(';
  const i = src.indexOf(key);
  if (i < 0) throw new Error(fileName + ' 未找到 async function ' + name);
  const pClose = closeIdx(src, i + key.length - 1, '(', ')');
  const open = src.indexOf('{', pClose);
  const close = closeIdx(src, open, '{', '}');
  const code = src.slice(i, close + 1);
  try { new Function('return ' + code); } catch (e) { throw new Error('抽取 ' + name + ' 语法不完整: ' + e.message); }
  return code;
}

const SNAP_ITEMS = [{ trade_team: '泥水班组', internal_code: 'NS-01', item_name: '地砖', unit: 'm2', unit_price: 100 }];
const LOCAL_ITEMS = [{ trade_team: '木工班组', internal_code: 'MG-01', item_name: '吊顶', unit: 'm2', unit_price: 200 }];

const RESP = {
  snap: { ok: true, json: async () => ({ items: SNAP_ITEMS, waste_rates: { 'NS-01': 5 } }) },
  snapEmpty: { ok: true, json: async () => ({ items: [], waste_rates: {} }) },
  snapRates: { ok: true, json: async () => ({ waste_rates: { 'R-01': 7 } }) },
  localItems: { ok: true, json: async () => LOCAL_ITEMS },
  localRates: { ok: true, json: async () => ({ 'L-01': 3 }) },
};

function makeCtx(srcCode, fileName, token, responses) {
  const calls = [];
  const ctx = vm.createContext({
    console, JSON, String, Promise,
    BACKEND_URL: BE,
    localStorage: { getItem: (k) => (k === 'sb-access-token' ? token : null) },
    fetch: (url, opt) => {
      calls.push({ url, auth: ((opt || {}).headers || {})['Authorization'] || '' });
      return Promise.resolve(responses[url] || { ok: false, status: 404, json: async () => ({}) });
    },
  });
  FNS.forEach((fn) => vm.runInContext(grabAsyncFn(srcCode, fn, fileName), ctx));
  return { ctx, calls };
}

async function run(fileName, token, responses, expr) {
  const src = fs.readFileSync(FILES[fileName], 'utf8');
  const { ctx, calls } = makeCtx(src, fileName, token, responses);
  const out = await vm.runInContext(expr, ctx);
  return { out: JSON.parse(JSON.stringify(out)), urls: calls.map((c) => c.url), auths: calls.map((c) => c.auth) };
}

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? '  → ' + detail : '')); }
}

const CASES = [
  {
    name: '有 token → 走后端解密快照（损耗率同源）',
    token: 'tok-1', responses: { [BE + '/api/v1/benchmark/snapshot']: RESP.snap },
    expr: 'loadFallbackBench()',
    expect: { items: SNAP_ITEMS, wrMap: { 'NS-01': 5 } },
    urls: [BE + '/api/v1/benchmark/snapshot'],
  },
  {
    name: '快照为空数组 → 继续退到本机 JSON',
    token: 'tok-1',
    responses: { [BE + '/api/v1/benchmark/snapshot']: RESP.snapEmpty, 'benchmark_data.json': RESP.localItems, 'waste_rates.json': RESP.localRates },
    expr: 'loadFallbackBench()',
    expect: { items: LOCAL_ITEMS, wrMap: { 'L-01': 3 } },
    urls: [BE + '/api/v1/benchmark/snapshot', 'benchmark_data.json',
           BE + '/api/v1/benchmark/waste-rates', 'waste_rates.json'],
  },
  {
    name: '无 token（外部/本机免登录）→ 绝不请求后端快照',
    token: null,
    responses: { 'benchmark_data.json': RESP.localItems, 'waste_rates.json': RESP.localRates },
    expr: 'loadFallbackBench()',
    expect: { items: LOCAL_ITEMS, wrMap: { 'L-01': 3 } },
    urls: ['benchmark_data.json', 'waste_rates.json'],
  },
  {
    name: '两个来源都没有 → null（调用方退回内置 4 条）',
    token: null, responses: {},
    expr: 'loadFallbackBench()',
    expect: null,
    urls: ['benchmark_data.json'],
  },
  {
    name: '损耗率补齐：有 token 走 /benchmark/waste-rates',
    token: 'tok-1', responses: { [BE + '/api/v1/benchmark/waste-rates']: RESP.snapRates },
    expr: '_wasteRates()',
    expect: { 'R-01': 7 },
    urls: [BE + '/api/v1/benchmark/waste-rates'],
  },
  {
    name: '损耗率补齐：后端不可达 → 本机 waste_rates.json',
    token: 'tok-1', responses: { 'waste_rates.json': RESP.localRates },
    expr: '_wasteRates()',
    expect: { 'L-01': 3 },
    urls: [BE + '/api/v1/benchmark/waste-rates', 'waste_rates.json'],
  },
  {
    name: '损耗率补齐：全无 → 空对象（不得抛）',
    token: null, responses: {},
    expr: '_wasteRates()',
    expect: {},
    urls: ['waste_rates.json'],
  },
];

(async () => {
  for (const c of CASES) {
    let a, b;
    try {
      a = await run('tool.html', c.token, c.responses, c.expr);
      b = await run('m.html', c.token, c.responses, c.expr);
    } catch (e) {
      ok(c.name, false, '执行异常 ' + e.message);
      continue;
    }
    ok(c.name + ' — 返回体', JSON.stringify(a.out) === JSON.stringify(c.expect),
       'tool.html 实得 ' + JSON.stringify(a.out));
    ok(c.name + ' — 双端一致', JSON.stringify(a) === JSON.stringify(b),
       'm.html 实得 ' + JSON.stringify(b.out) + ' / ' + b.urls.join(','));
    ok(c.name + ' — 请求序列', JSON.stringify(a.urls) === JSON.stringify(c.urls),
       a.urls.join(','));
  }

  // 带 token 时必须把凭据发出去，否则后端 require_auth 直接 401
  const t = await run('tool.html', 'tok-1', { [BE + '/api/v1/benchmark/snapshot']: RESP.snap }, 'loadFallbackBench()');
  ok('快照请求带 Bearer token', t.auths.some((h) => h === 'Bearer tok-1'), JSON.stringify(t.auths));

  console.log('\n════════ 结果：' + pass + ' 通过 / ' + fail + ' 失败 ════════');
  process.exit(fail ? 1 : 0);
})();

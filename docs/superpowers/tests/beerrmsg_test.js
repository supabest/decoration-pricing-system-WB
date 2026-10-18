/* 后端错误提示解析 beErrMsg 双端对偶验证（只读 tool.html / m.html，不修改）
 * 背景（P0-3）：导出端点 500 改为统一体 {"error":"export_failed","message":…}，
 *   前端工具函数负责把 message/error/detail 解析出来，纯文本兜底，
 *   不再把原始 JSON 或内部异常文本直接上屏。
 * 契约：tool.html 与 m.html 的 beErrMsg 行为逐案一致（同源同形）。
 * 运行：node docs/superpowers/tests/beerrmsg_test.js
 */
const fs = require('fs');
const vm = require('vm');

const TOOL = fs.readFileSync(__dirname + '/../../tool.html', 'utf8');
const MOBILE = fs.readFileSync(__dirname + '/../../m.html', 'utf8');

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

const ctxTool = vm.createContext({ console, JSON, String });
const ctxMob = vm.createContext({ console, JSON, String });
vm.runInContext(grabAsyncFn(TOOL, 'beErrMsg', 'tool.html'), ctxTool);
vm.runInContext(grabAsyncFn(MOBILE, 'beErrMsg', 'm.html'), ctxMob);

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? '  → ' + detail : '')); }
}

// 最小 Response 替身：只提供 beErrMsg 用到的 status / text()
function resp(status, body) {
  return { status, text: async () => body };
}

// 夹具：[用例名, HTTP 状态, body, 期望返回值]
const CASES = [
  ['500 统一体 → 取 message', 500, JSON.stringify({ error: 'export_failed', message: '导出服务异常，请重试；若持续失败请联系管理员' }),
    '导出服务异常，请重试；若持续失败请联系管理员'],
  ['400 字符串 detail → 取 detail', 400, JSON.stringify({ detail: 'Not Found' }), 'Not Found'],
  ['结构化 detail（集团待询价）→ JSON 序列化兜底，不上屏 [object Object]', 400,
    JSON.stringify({ detail: { pending: ['ZS02-A-009'] } }), JSON.stringify({ pending: ['ZS02-A-009'] })],
  ['非 JSON 纯文本 → 原文兜底', 502, 'Bad Gateway', 'Bad Gateway'],
  ['空 body → 状态码兜底', 500, '', 'HTTP 500'],
  ['message 为空串 → 落到 error 字段', 500, JSON.stringify({ error: 'export_failed', message: '' }), 'export_failed'],
];

(async () => {
  console.log('\n── beErrMsg 行为（tool.html） ──');
  for (const [name, status, body, want] of CASES) {
    const got = await vm.runInContext('beErrMsg', ctxTool)(resp(status, body));
    ok('T·' + name, got === want, 'got=' + JSON.stringify(got));
  }

  console.log('\n── 双端对偶（m.html 同源同形） ──');
  let same = 0;
  for (const [name, status, body, want] of CASES) {
    const a = await vm.runInContext('beErrMsg', ctxTool)(resp(status, body));
    const b = await vm.runInContext('beErrMsg', ctxMob)(resp(status, body));
    ok('M·两端一致：' + name, a === b && b === want, 'tool=' + JSON.stringify(a) + ' m=' + JSON.stringify(b));
    if (a === b && b === want) same++;
  }

  console.log('\n────────────────────────────');
  if (fail) { console.log('通过 ' + pass + ' / ' + (pass + fail) + '  ❌ 有失败'); process.exit(1); }
  console.log('通过 ' + pass + ' / ' + (pass + fail) + '  ✅ 全部通过（两端一致 ' + same + '/' + CASES.length + '）');
  process.exit(0);
})().catch(e => { console.error('\n💥 测试异常：' + (e && e.message ? e.message : e)); process.exit(1); });

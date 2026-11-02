/* /sb 同源反代回归（Pages Function 路由决策 + 前端 URL 收口）
 * 背景 bug：用户网络到 *.supabase.co 被干扰（需 VPN 才通），导致登录 Load failed、
 * 集团库「未加载」。根治 = 浏览器只连 pages.dev，由 Cloudflare 边缘转发 Supabase。
 * 本测试钉的是「这个转发绝不能变成开放代理」+「前端确实不再裸连 supabase.co」。
 * 运行：node docs/superpowers/tests/sb_proxy_test.js
 */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const ROUTE = path.resolve(__dirname, '../../../frontend/functions/sb/_route.js');
const UP = 'https://lnvtykghcpsjpwczbqsm.supabase.co';

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  \u2713 ' + name); }
  else { fail++; console.log('  \u2717 ' + name + (extra ? '  \u2190 ' + extra : '')); }
}

(async () => {
  const R = await import(pathToFileURL(ROUTE).href);
  const { resolveUpstream, filterRequestHeaders, filterResponseHeaders, isAllowedMethod } = R;

  console.log('\u2500\u2500 A 段：放行的两个前缀（前端全部流量只有这两类）\u2500\u2500');
  let r = resolveUpstream('/sb/rest/v1/benchmark_items', 'select=*&order=id.asc', UP);
  ok('A1 rest/v1 放行且查询串原样保留',
    r.ok === true && r.url === UP + '/rest/v1/benchmark_items?select=*&order=id.asc', JSON.stringify(r));
  r = resolveUpstream('/sb/auth/v1/token', 'grant_type=password', UP);
  ok('A2 auth/v1 放行（登录链必走）',
    r.ok === true && r.url === UP + '/auth/v1/token?grant_type=password', JSON.stringify(r));
  r = resolveUpstream('/sb/rest/v1/rpc/report_pricing_failure', '', UP);
  ok('A3 rpc 子路径仍在 rest/v1 白名单内',
    r.ok === true && r.url === UP + '/rest/v1/rpc/report_pricing_failure', JSON.stringify(r));
  r = resolveUpstream('/sb/rest/v1/projects', 'id=eq.7&select=*', UP);
  ok('A4 多级 query 不被截断', /id=eq\.7&select=\*$/.test(r.url || ''), JSON.stringify(r));

  console.log('\u2500\u2500 B 段：白名单外一律拒（防开放代理 / SSRF）\u2500\u2500');
  [['B1 storage 未放行', '/sb/storage/v1/object/x'],
   ['B2 rest/v2 不存在的前缀', '/sb/rest/v2/x'],
   ['B3 只有一段', '/sb/rest'],
   ['B4 空路径', '/sb/'],
   ['B5 根路径', '/sb'],
   ['B6 实时通道不放行（前端未用）', '/sb/realtime/v1/websocket'],
   ['B7 管理面', '/sb/api/v1/projects'],
  ].forEach(([n, p]) => {
    const x = resolveUpstream(p, '', UP);
    ok(n, x.ok === false && !!x.reason, JSON.stringify(x));
  });
  // 关键：路径里塞别的 host 也不能改变上游（上游域名只来自常量）
  let x = resolveUpstream('/sb/https://evil.com/x', '', UP);
  ok('B8 路径内嵌他域被拒', x.ok === false, JSON.stringify(x));
  x = resolveUpstream('/sb/rest/v1/../../api/v1/projects', '', UP);
  ok('B9 目录穿越（..）被拒', x.ok === false, JSON.stringify(x));
  x = resolveUpstream('/sb/rest/v1/x', '', UP);
  ok('B10 上游恒为传入的固定 project 域（不接受请求里的 host）',
    x.ok === true && x.url.indexOf(UP) === 0 && x.url.indexOf('evil') === -1, JSON.stringify(x));

  console.log('\u2500\u2500 C 段：方法白名单 \u2500\u2500');
  ok('C1 GET/POST/PATCH/DELETE/OPTIONS/HEAD 允许',
    ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'].every(isAllowedMethod));
  ok('C2 TRACE/CONNECT 拒绝', !isAllowedMethod('TRACE') && !isAllowedMethod('connect'));

  console.log('\u2500\u2500 D 段：请求头透传规则 \u2500\u2500');
  const reqH = filterRequestHeaders({
    apikey: 'sb_publishable_x', authorization: 'Bearer jwt', prefer: 'return=minimal',
    range: '0-999', 'content-type': 'application/json', accept: 'application/json',
    host: 'decoration-pricing-system.pages.dev', connection: 'keep-alive',
    'transfer-encoding': 'chunked', 'content-length': '123', cookie: 'session=abc',
    'user-agent': 'Mozilla/5.0', origin: 'https://decoration-pricing-system.pages.dev',
    referer: 'https://decoration-pricing-system.pages.dev/tool',
  });
  ok('D1 鉴权与 PostgREST 语义头保留',
    reqH.apikey === 'sb_publishable_x' && reqH.authorization === 'Bearer jwt' &&
    reqH.prefer === 'return=minimal' && reqH.range === '0-999' && reqH['content-type'] === 'application/json',
    JSON.stringify(reqH));
  ok('D2 hop-by-hop / host / content-length 被剥（否则上游报错）',
    !('host' in reqH) && !('connection' in reqH) && !('transfer-encoding' in reqH) && !('content-length' in reqH),
    JSON.stringify(reqH));
  ok('D3 浏览器侧 cookie/origin/referer 不透传（Supabase 不用 cookie 会话）',
    !('cookie' in reqH) && !('origin' in reqH) && !('referer' in reqH), JSON.stringify(reqH));

  console.log('\u2500\u2500 E 段：响应头规则（Content-Range 是前端计数依据，压缩/长度头必须剥）\u2500\u2500');
  const resH = filterResponseHeaders({
    'content-range': '0-295/*', 'content-type': 'application/json; charset=utf-8',
    'content-encoding': 'gzip', 'content-length': '4567', 'transfer-encoding': 'chunked',
    connection: 'keep-alive', server: 'cloudflare',
  });
  ok('E1 content-range / content-type 保留',
    resH['content-range'] === '0-295/*' && /^application\/json/.test(resH['content-type']), JSON.stringify(resH));
  ok('E2 content-encoding/content-length/transfer-encoding/connection 剥掉',
    !('content-encoding' in resH) && !('content-length' in resH) &&
    !('transfer-encoding' in resH) && !('connection' in resH), JSON.stringify(resH));

  console.log('\u2500\u2500 F 段：源码钩 \u2014 前端不再裸连 supabase.co，函数里也没有 service_role \u2500\u2500');
  const root = path.resolve(__dirname, '../../..');
  const read = p => fs.readFileSync(path.join(root, p), 'utf8');
  const htmlFiles = ['tool', 'admin', 'm', 'login', 'app', 'debug', 'editor', 'import-knowledge', 'import-rules', 'restore_benchmark']
    .map(n => 'docs/' + n + '.html');
  const bad = htmlFiles.filter(f => {
    const src = read(f);
    // 允许：localhost 分支里出现裸域名（开发路径不变）；不允许：SUPABASE_URL 常量直接等于 supabase.co
    return /const (SUPABASE_URL|S)\s*=\s*'https:\/\/lnvtykghcpsjpwczbqsm\.supabase\.co'/.test(src);
  });
  ok('F1 10 个页面都不再有「常量直连 supabase.co」的写法', bad.length === 0, bad.join(','));
  const proxied = htmlFiles.filter(f => read(f).indexOf("'/sb'") !== -1 || read(f).indexOf('"/sb"') !== -1);
  ok('F2 10 个页面都出现 /sb 代理前缀', proxied.length === htmlFiles.length, proxied.length + '/' + htmlFiles.length);
  const fnSrcRaw = read('frontend/functions/sb/[[path]].js') + read('frontend/functions/sb/_route.js');
  // 先剥注释：函数里有一句注释就在解释「为什么不能放 service_role」，不剥会自扫自
  const fnSrc = fnSrcRaw.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  ok('F3 函数代码里没有 service_role / JWT 形状的密钥', !/service_role|SERVICE_ROLE|eyJ[A-Za-z0-9_.-]{30,}/.test(fnSrc));
  ok('F4 函数只认一个固定上游 project 域',
    (fnSrcRaw.match(/lnvtykghcpsjpwczbqsm\.supabase\.co/g) || []).length >= 1);
  const routes = JSON.parse(read('frontend/public/_routes.json'));
  // 官方规则：exclude 命中即走静态资源，优先级高于 include。
  // 旧文件写的是 exclude:["/*"] —— /* 连 /sb/... 一起排除掉了，函数从不被调用，
  // 线上表现为登录与集团库全部拿到 index.html（2026-11-02 事故）。断言因此按「路由行为」写，
  // 而不是按字符串写死，否则同样的错误理解会被再钉一次。
  const toRe = p => new RegExp('^' + String(p).replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '$');
  const routedToFn = p => !(routes.exclude || []).some(re => toRe(re).test(p))
    && (routes.include || []).some(re => toRe(re).test(p));
  const staticPaths = ['/tool.html', '/index.html', '/assets/index-Bq4Pd6oN.js', '/benchmark_data.json', '/login'];
  ok('F5 _routes.json：/sb/* 进函数且静态路径不进（exclude 不得盖住 /sb）',
    routes.version === 1
    && routedToFn('/sb/rest/v1/benchmark_items') && routedToFn('/sb/auth/v1/token')
    && !staticPaths.some(routedToFn),
    JSON.stringify(routes));
  const cli = read('frontend/src/lib/supabaseClient.ts');
  ok('F6 React 客户端也走 /sb（supabase-js 需绝对 URL，用 location.origin 拼）',
    /location\.origin/.test(cli) && /\/sb/.test(cli) && !/createClient\(\s*'https:\/\/lnvtykgh/.test(cli), cli.split('\n').slice(0, 8).join(' | '));

  console.log('\u2500\u2500 G 段：错误可见性（本次排查被拖几轮的直接原因是它）\u2500\u2500');
  const tool = read('docs/tool.html');
  ok('G1 _get 失败时记录真实原因而不是静默 []',
    /const _dbFail\s*=/.test(tool) && /return _dbFail\(t,ab\?'timeout':'network'/.test(tool), '未找到 _dbFail 接入点');
  ok('G2 HTTP 非 2xx 带上状态码与 body 片段',
    /_dbFail\(t,'http',\{status:r\.status,ms,body:txt\.slice\(0,180\)\}\)/.test(tool));
  ok('G3 集团库 toast 说得出真实错因',
    /loadGroupBenchmark[\s\S]{0,400}dbErrorText\(\)/.test(tool));
  ok('G4 两处空库面板都不再是固定文案',
    (tool.match(/dbErrorText\(\)/g) || []).length >= 3 && !/集团基准价表读不到数据（后端不可用或表内无记录）/.test(tool),
    'dbErrorText 出现 ' + (tool.match(/dbErrorText\(\)/g) || []).length + ' 次');
  ok('G5 错因文本进 innerHTML 前转义（上游 body 可能含尖括号）',
    /'&lt;'/.test(tool) && /word-break:break-all/.test(tool));
  const authErr = read('frontend/src/lib/authErrors.ts');
  ok('G6 authErrors 接住 Safari 的 Load failed 与代理错因码',
    /Load failed/.test(authErr) && /upstream_unreachable/.test(authErr) && /proxy_path_denied/.test(authErr));
  ok('G7 docs/ 与 frontend/public/ 的 tool.html 逐字节一致',
    read('docs/tool.html') === read('frontend/public/tool.html'));

  console.log('\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 结果：' + pass + ' 通过 / ' + fail + ' 失败 \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('\uD83D\uDCA5 ' + (e && e.stack || e)); process.exit(2); });

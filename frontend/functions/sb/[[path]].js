/* Pages Function: /sb/* → Supabase 同源反代
 * 路由决策全在 ./_route.js（纯函数，node 可回归）；这里只做 CF 运行时的 I/O 粘合。
 *
 * 为什么需要它：用户侧网络到 *.supabase.co 被干扰（实测需 VPN 才通），
 * 而 pages.dev 一直可达。把数据流量挪到 Cloudflare 边缘出口，浏览器就不再需要连 supabase.co。
 *
 * 边界（硬）：只转发 rest/v1 与 auth/v1 两个前缀，其余 400；上游域名是常量，不接受请求里的 host。
 * 密钥边界：这里只允许出现 anon key 级别的公开值（它本来就在前端 bundle 里），
 *          service_role / SMTP 授权码等一律不放 —— 函数与前端同源同仓库，放进去等于公开。
 */
import {
  UPSTREAM, resolveUpstream, filterRequestHeaders, filterResponseHeaders, isAllowedMethod, methodHasBody,
} from './_route.js';

const UPSTREAM_TIMEOUT_MS = 15000;

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function onRequest(context) {
  const request = context.request;
  const url = new URL(request.url);

  if (!isAllowedMethod(request.method)) {
    return json({ error: 'proxy_method_denied', method: request.method }, 405);
  }

  const target = resolveUpstream(url.pathname, url.search.replace(/^\?/, ''), UPSTREAM);
  if (!target.ok) {
    // 400 而不是 404：让前端能区分「我们主动拒绝」和「上游说没有」
    return json({ error: 'proxy_path_denied', reason: target.reason, path: url.pathname }, 400);
  }

  const headers = filterRequestHeaders(Object.fromEntries(request.headers));

  // 请求体整体缓冲而非流式转发：Workers 的 streaming request body 需要 duplex 且各家运行时行为不一，
  // 而这里的载荷都是 JSON 行/草稿（KB 量级），缓冲换来的确定性更值。真出现大 body 场景再改。
  let body;
  if (methodHasBody(request.method)) {
    const buf = await request.arrayBuffer();
    if (buf.byteLength > 0) body = buf;
  }

  const started = Date.now();
  let upstream;
  try {
    upstream = await fetch(target.url, {
      method: request.method,
      headers,
      body,
      redirect: 'manual',
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
  } catch (e) {
    const timedOut = e && (e.name === 'TimeoutError' || e.name === 'AbortError');
    // 504/502 带上游域名与耗时：这是本次排查最缺的信息，别再让前端只显示「加载失败」
    return json({
      error: timedOut ? 'upstream_timeout' : 'upstream_unreachable',
      host: UPSTREAM,
      path: url.pathname,
      ms: Date.now() - started,
      message: String((e && e.message) || e || ''),
    }, timedOut ? 504 : 502);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: filterResponseHeaders(Object.fromEntries(upstream.headers)),
  });
}

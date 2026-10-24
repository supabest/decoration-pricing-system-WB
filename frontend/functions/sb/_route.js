/* /sb 同源反代的路由决策（纯函数，无 CF 全局 —— 可在 node 里直接回归）
 * 权威消费方：frontend/functions/sb/[[path]].js
 * 回归：node docs/superpowers/tests/sb_proxy_test.js
 *
 * 存在理由：用户网络到 *.supabase.co 被干扰（需 VPN 才通），浏览器改只连 pages.dev，
 * 由 Cloudflare 边缘把这两类路径转给 Supabase。前缀白名单是硬边界 ——
 * 放宽一寸，这里就从「同源代理」变成「任意人可借用的开放代理」。
 */

export const UPSTREAM = 'https://lnvtykghcpsjpwczbqsm.supabase.co';

// 前端实测只用到这两个子系统（docs/*.html 与 frontend/src 里 grep 过：无 realtime / storage）
export const ALLOWED_PREFIXES = ['rest/v1', 'auth/v1'];

// 方法白名单：TRACE/CONNECT 一类即使在白名单路径上也拒
const ALLOWED_METHODS = ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'];

// 请求头只走白名单，不做黑名单 —— 黑名单挡不住以后新加的浏览器头
const REQUEST_ALLOW = [
  'apikey', 'authorization',            // 鉴权（anon key + 用户 JWT，原样透传）
  'prefer', 'range',                    // PostgREST 语义：返回表示 / 分页计数
  'accept', 'content-type',             // 内容协商
  'accept-profile', 'content-profile',  // PostgREST schema 选择
  'x-client-info',                      // supabase-js 自报版本，上游日志用
];

// 响应必剥：我们回传的是已解码的 body，留着这些头浏览器会解不开/长度不符
const RESPONSE_DROP = ['content-encoding', 'content-length', 'transfer-encoding', 'connection'];

/** 把 /sb/... 解析成上游 URL。只接受传入的固定 upstream，绝不从请求里取 host。 */
export function resolveUpstream(pathname, search, upstream) {
  const raw = String(pathname || '');
  if (!raw.startsWith('/sb')) return { ok: false, reason: 'not_a_proxy_path' };

  const rest = raw.slice(3); // 去掉 '/sb'
  if (rest !== '' && !rest.startsWith('/')) return { ok: false, reason: 'malformed_prefix' }; // 挡 /sbx/...

  const segs = rest.split('/').filter(s => s !== '');
  if (segs.length < 2) return { ok: false, reason: 'too_few_segments' };

  for (const s of segs) {
    if (s === '..' || s === '.') return { ok: false, reason: 'dot_segment' };
    // 只挡真正的危险字符：协议分隔符、反斜杠、NUL。
    // 注意不要把 % 或数字挡掉 —— 表名带数字是合法的（projects2 / ZS02 一类）
    if (/[:\\\u0000]/.test(s)) return { ok: false, reason: 'suspicious_segment' };
  }

  const prefix = segs.slice(0, 2).join('/');
  if (ALLOWED_PREFIXES.indexOf(prefix) === -1) return { ok: false, reason: 'prefix_not_allowed', prefix };

  return { ok: true, url: upstream + '/' + segs.join('/') + (search ? '?' + search : ''), prefix };
}

export function isAllowedMethod(method) {
  return ALLOWED_METHODS.indexOf(String(method || '').toUpperCase()) !== -1;
}

/** 上游请求头：白名单过滤，键名统一小写比较 */
export function filterRequestHeaders(headers) {
  const out = {};
  Object.keys(headers || {}).forEach(k => {
    const lk = k.toLowerCase();
    if (REQUEST_ALLOW.indexOf(lk) !== -1) out[lk] = headers[k];
  });
  return out;
}

/** 回给浏览器的响应头：剥掉与压缩/长度/连接相关的，Content-Range 必须留（前端靠它计数与分页） */
export function filterResponseHeaders(headers) {
  const out = {};
  Object.keys(headers || {}).forEach(k => {
    const lk = k.toLowerCase();
    if (RESPONSE_DROP.indexOf(lk) === -1) out[lk] = headers[k];
  });
  return out;
}

/** 有 body 的方法（GET/HEAD/OPTIONS 不带体，带了会被上游拒） */
export function methodHasBody(method) {
  return ['POST', 'PATCH', 'PUT', 'DELETE'].indexOf(String(method || '').toUpperCase()) !== -1;
}

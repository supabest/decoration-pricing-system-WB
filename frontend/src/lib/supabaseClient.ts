import { createClient } from '@supabase/supabase-js'

// 数据链路：线上走同源反代 /sb（Pages Function → Supabase）——部分用户网络直连 *.supabase.co 会被干扰；
// localhost 保持直连。supabase-js 内部 new URL() 不接受相对路径，故必须用 location.origin 拼成绝对 URL。
// 回归：docs/superpowers/tests/sb_proxy_test.js
const SUPABASE_DIRECT = 'https://lnvtykghcpsjpwczbqsm.supabase.co'
const isLocal = typeof location !== 'undefined' && (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
// ★ 故意不读 VITE_SUPABASE_URL：Pages 项目遗留的这个构建变量会把直连 URL 烤进 bundle、
//   整个短路 /sb 反代（2026-11-03 线上 bundle 取证：有 10-24 报错文案、零 /sb 引用）。
//   数据链路只认 localhost 判定，任何构建环境变量都不参与。
const supabaseUrl = isLocal ? SUPABASE_DIRECT : (typeof location !== 'undefined' ? location.origin + '/sb' : SUPABASE_DIRECT)
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q'

export const hasSupabaseConfig = true

// ★ 存储键必须显式钉死：supabase-js 默认键 = `sb-${hostname.split('.')[0]}-auth-token`，
//   supabaseUrl 换成同源 /sb 后主机名变成了 pages.dev，键名会跟着漂移；
//   而 AuthContext.syncTokenForTool 与 tool.html/m.html 的桥接契约读的是这个固定键。
//   （2026-11-03 排障：键漂移导致登录后 sb-access-token 不落盘，tool.html 启动即弹回 index.html）
export const SUPABASE_STORAGE_KEY = 'sb-lnvtykghcpsjpwczbqsm-auth-token'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: { storageKey: SUPABASE_STORAGE_KEY },
})

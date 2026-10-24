import { createClient } from '@supabase/supabase-js'

// 数据链路：线上走同源反代 /sb（Pages Function → Supabase）——部分用户网络直连 *.supabase.co 会被干扰；
// localhost 保持直连。supabase-js 内部 new URL() 不接受相对路径，故必须用 location.origin 拼成绝对 URL。
// 回归：docs/superpowers/tests/sb_proxy_test.js
const SUPABASE_DIRECT = 'https://lnvtykghcpsjpwczbqsm.supabase.co'
const isLocal = typeof location !== 'undefined' && (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  || (isLocal ? SUPABASE_DIRECT : (typeof location !== 'undefined' ? location.origin + '/sb' : SUPABASE_DIRECT))
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_VQNxLrsKEZuZDeAGa7xOAg__SUeFH_Q'

export const hasSupabaseConfig = true

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

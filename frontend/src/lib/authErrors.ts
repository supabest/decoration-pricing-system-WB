/**
 * Supabase Auth 错误消息翻译成中文
 */
export function getChineseErrorMessage(err: any): string {
  if (!err) return '操作失败，请重试'

  const msg = err?.message || err?.error_description || String(err)

  // AuthApiError
  if (msg.includes('Invalid login credentials')) {
    return '邮箱或密码错误，请检查后重试'
  }
  if (msg.includes('Email not confirmed')) {
    return '账户尚未通过审核，请等待管理员审批后再登录'
  }
  if (msg.includes('User already registered')) {
    return '该邮箱已被注册'
  }
  if (msg.includes('Password should be at least 6 characters')) {
    return '密码长度至少为 6 位'
  }
  if (msg.includes('signup_disabled')) {
    return '注册功能已关闭，请联系管理员'
  }
  if (msg.includes('Invalid email')) {
    return '邮箱格式不正确'
  }
  if (msg.includes('Too many requests')) {
    return '操作过于频繁，请稍后再试'
  }
  if (msg.includes('expired') || msg.includes('Expired')) {
    return '登录已过期，请重新登录'
  }
  if (msg.includes('Invalid Refresh Token')) {
    return '登录已过期，请重新登录'
  }
  if (msg.includes('Session from session_id')) {
    return '会话异常，请重新登录'
  }
  // 网络层失败的原文各家浏览器不同：Chrome/Edge = "Failed to fetch"，Safari/WebKit = "Load failed"，
  // supabase-js 自己包一层 = "NetworkError ..."。漏掉任一种会把英文原文直接吐到界面上（2026-10 实际踩到）。
  // /sb 反代失败时函数返回结构化 JSON（upstream_timeout / upstream_unreachable / proxy_path_denied），一并接住。
  if (/NetworkError|Network Error|Failed to fetch|Load failed|upstream_timeout|upstream_unreachable|proxy_path_denied/i.test(msg)) {
    return '无法连接数据服务（当前网络访问不了）。若持续出现，请告知管理员你的网络到 supabase.co 是否被拦截'
  }
  if (msg.includes('timeout') || msg.includes('Timeout')) {
    return '请求超时，请稍后重试'
  }
  if (msg.includes('未找到用户信息')) {
    return '未找到用户信息，请联系管理员'
  }

  // 兜底
  return msg
}

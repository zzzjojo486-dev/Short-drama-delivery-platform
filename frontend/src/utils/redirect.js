// 登录后回跳仅允许站内路径，防开放重定向
export function safeRedirect(raw, fallback = '/', prefix = '') {
  if (typeof raw !== 'string') return fallback
  const path = raw.trim()
  if (!path.startsWith('/') || path.startsWith('//') || /[\\\r\n]/.test(path)) return fallback
  if (prefix && !path.startsWith(prefix)) return fallback
  return path
}
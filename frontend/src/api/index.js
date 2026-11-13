import axios from 'axios'
import { ElMessage } from 'element-plus'
import { safeRedirect } from '../utils/redirect'

const api = axios.create({
  // 相对路径 /api —— 由 Vite dev 代理转发到 Django(127.0.0.1:8000),同源请求,规避浏览器代理拦截/CORS/IPv6
  baseURL: '/api',
})

// 401 只处理一次,避免并发请求重复清会话/重复跳转
let handlingAuthFailure = false

function handleAuthFailure(error) {
  if (handlingAuthFailure) return
  handlingAuthFailure = true
  const url = error.config?.url || ''
  const current = window.location.pathname + window.location.search
  if (url.startsWith('/admin/')) {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    const target = current.startsWith('/admin/login') ? '/admin/users' : safeRedirect(current, '/admin/users', '/admin')
    window.location.assign(`/admin/login?redirect=${encodeURIComponent(target)}`)
  } else {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    const target = current.startsWith('/login') ? '/' : safeRedirect(current, '/')
    window.location.assign(`/login?redirect=${encodeURIComponent(target)}`)
  }
}

// JSON 接口统一按 code === 200 判断成功，保留 Axios 响应供页面读取 data。
// 错误提示统一在此弹出一次,页面 catch 只负责状态展示,不再重复弹。
api.interceptors.response.use(
  (response) => {
    const d = response.data
    if (!d || typeof d !== 'object' || d.code !== 200) {
      const message = d?.message || '接口响应格式错误'
      ElMessage.error(message)
      return Promise.reject(Object.assign(new Error(message), { response }))
    }
    return response
  },
  (error) => {
    const status = error.response?.status
    const d = error.response ? error.response.data : null
    if (status === 401) {
      handleAuthFailure(error)
    } else if (d && typeof d === 'object' && typeof d.message === 'string') {
      ElMessage.error(d.message)
    } else {
      ElMessage.error('请求失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

// 登录类请求单独设置超时:响应被代理/网络层丢失时给出可见错误,而不是永久挂起
export const login = (username, password) => api.post('/login', { username, password }, { timeout: 15000 })
export const adminLogin = (username, password) => api.post('/admin/login', { username, password }, { timeout: 15000 })
export const register = (username, password, nickname, avatar) => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  if (nickname) formData.append('nickname', nickname)
  if (avatar) formData.append('avatar', avatar)

  return api.post('/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000
  })
}
export const getPosts = (limit = 20, offset = 0, search = '', category = '') => 
  api.get('/posts', { params: { limit, offset, search, category } })
export const createPost = (formData) => api.post('/posts', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const getPostDetail = (id, userId = null) => {
  const params = {}
  if (userId) {
    params.user_id = userId
  }
  return api.get(`/posts/${id}`, { params })
}
export const getComments = (id, userId = null) => api.get(`/posts/${id}/comments`, { params: { user_id: userId } })
export const addComment = (postId, userId, content) => api.post(`/posts/${postId}/comments`, { user_id: userId, content })
export const toggleLike = (postId, userId) => api.post(`/posts/${postId}/like`, { user_id: userId })
export const toggleCommentLike = (commentId, userId) => api.post(`/comments/${commentId}/like`, { user_id: userId })
export const toggleCollection = (postId, userId) => api.post(`/posts/${postId}/collect`, { user_id: userId })
export const getUserPosts = (userId, currentUserId = null) => {
  const params = {}
  if (currentUserId) {
    params.current_user_id = currentUserId
  }
  return api.get(`/posts/user/${userId}`, { params })
}
export const getUserLikedPosts = (userId) => api.get(`/posts/user/${userId}/liked`)
export const getUserCollectedPosts = (userId) => api.get(`/posts/user/${userId}/collected`)
export const updateProfile = (formData) => api.put('/user/profile', formData)
export const getPublicUserProfile = (userId) => api.get(`/users/${userId}`)

// User Follow APIs
export const followUser = (targetUserId, currentUserId) => api.post(`/users/${targetUserId}/follow`, { user_id: currentUserId })
export const unfollowUser = (targetUserId, currentUserId) => api.post(`/users/${targetUserId}/unfollow`, { user_id: currentUserId })
export const checkIsFollowing = (targetUserId, currentUserId) => api.get(`/users/${targetUserId}/is_following`, { params: { current_user_id: currentUserId } })
export const getFollowers = (userId, currentUserId = null) => api.get(`/users/${userId}/followers`, { params: { current_user_id: currentUserId } })
export const getFollowing = (userId, currentUserId = null) => api.get(`/users/${userId}/following`, { params: { current_user_id: currentUserId } })
export const getFollowCounts = (userId) => api.get(`/users/${userId}/counts`)

// New APIs for delete and visibility
export const deletePost = (postId, userId) => api.delete(`/posts/${postId}`, { data: { user_id: userId } })
export const updatePostVisibility = (postId, userId, isPrivate) => api.put(`/posts/${postId}/visibility`, { user_id: userId, is_private: isPrivate })

// Message APIs
export const sendMessage = (senderId, receiverId, content) => api.post('/messages', { sender_id: senderId, receiver_id: receiverId, content })
export const getConversations = (userId) => api.get('/messages/conversations', { params: { user_id: userId } })
export const getConversation = (otherUserId, userId, limit = 50, offset = 0) => 
  api.get(`/messages/conversation/${otherUserId}`, { params: { user_id: userId, limit, offset } })
export const markMessagesRead = (userId, senderId) => api.put('/messages/read', { user_id: userId, sender_id: senderId })
export const getUnreadCount = (userId) => api.get('/messages/unread/count', { params: { user_id: userId } })

// Notification APIs
export const getNotifications = (userId) => api.get('/notifications', { params: { user_id: userId } })
export const markNotificationsRead = (userId) => api.put('/notifications/read', { user_id: userId })

// AI API
// export const aiPolish = (content) => api.post('/ai/polish', { content })
export const aiPolishStream = async (content, onChunk, onError) => {
  try {
    const response = await fetch('/api/ai/polish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      if (chunk.startsWith("Error:")) {
         if (onError) onError(chunk)
         break
      }
      if (onChunk) onChunk(chunk)
    }
  } catch (error) {
    if (onError) onError(error.message)
  }
}

export const getImageUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  // path might be absolute "assets/..." or just filename
  const filename = path.split(/[\\/]/).pop()
  return `/assets/${filename}`
}

// Admin APIs (后台)
// 后台凭证独立存放:只读 localStorage 的 admin_token,与前台 token 完全隔离,互不穿越。
const adminAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('admin_token') || ''}` })
export const getAdminUsers = () => api.get('/admin/users/', { headers: adminAuthHeader() })
export const updateUserRole = (userId, role) => api.patch(`/admin/users/${userId}/role/`, { role }, { headers: adminAuthHeader() })
export const getPendingDeliveries = (params = {}) => api.get('/admin/reviews/deliveries/', { headers: adminAuthHeader(), params })
export const reviewDelivery = (id, action, opinion) => api.post(`/admin/deliveries/${id}/review/`, { action, opinion }, { headers: adminAuthHeader() })

// 商单（T1.1）——列表返回 DRF 分页信封 {count, next, previous, results}，筛参 status/category/search(标题)
export const getAdminOrders = (params = {}) => api.get('/admin/orders/', { headers: adminAuthHeader(), params })
export const createAdminOrder = (data) => api.post('/admin/orders/', data, { headers: adminAuthHeader() })
export const getAdminOrderDetail = (id) => api.get(`/admin/orders/${id}/`, { headers: adminAuthHeader() })
export const updateAdminOrder = (id, data) => api.patch(`/admin/orders/${id}/`, data, { headers: adminAuthHeader() })
export const submitAdminOrder = (id) => api.post(`/admin/orders/${id}/submit/`, {}, { headers: adminAuthHeader() })
export const reviewAdminOrder = (id, action, opinion) => api.post(`/admin/orders/${id}/review/`, { action, opinion }, { headers: adminAuthHeader() })
export const completeAdminOrder = (id) => api.post(`/admin/orders/${id}/complete/`, {}, { headers: adminAuthHeader() })
export const closeAdminOrder = (id) => api.post(`/admin/orders/${id}/close/`, {}, { headers: adminAuthHeader() })

// 报名+指派（T1.2）
export const getAdminOrderApplications = (id, params = {}) => api.get(`/admin/orders/${id}/applications/`, { headers: adminAuthHeader(), params })
export const selectAdminOrderApplication = (id, aid) => api.post(`/admin/orders/${id}/applications/${aid}/select/`, { selected: true }, { headers: adminAuthHeader() })
export const assignAdminOrder = (id, creatorId) => api.post(`/admin/orders/${id}/assign/`, { creator_id: creatorId }, { headers: adminAuthHeader() })

// 创作者端（T1.4/T1.5，Bearer 前台 token，与后台凭证隔离）
const frontAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token') || ''}` })
export const getCreatorOrders = (params = {}) => api.get('/orders/', { headers: frontAuthHeader(), params })
export const getCreatorOrderDetail = (id) => api.get(`/orders/${id}/`, { headers: frontAuthHeader() })
export const applyCreatorOrder = (id, proposal) => api.post(`/orders/${id}/apply/`, { proposal }, { headers: frontAuthHeader() })
// 提交请求 delivery_type 用 "video"/"link" 字符串区分模式;响应 delivery_type 一律整数 0/1
export const submitCreatorDelivery = (id, { mode, file, url, note }, onProgress) => {
  if (mode === 'video') {
    const formData = new FormData()
    formData.append('delivery_type', 'video')
    formData.append('video_file', file)
    formData.append('note', note || '')
    return api.post(`/orders/${id}/deliver/`, formData, {
      headers: { ...frontAuthHeader(), 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    })
  }
  return api.post(`/orders/${id}/deliver/`, { delivery_type: 'link', video_url: url, note: note || '' }, { headers: frontAuthHeader() })
}

// 交付视频地址:后端返回绝对 URL 时归一到同源 /media/(dev 走 Vite 代理,支持 Range);其他绝对地址直接播放
export const getMediaUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('/media/')) return url
  if (/^https?:\/\//i.test(url)) {
    try {
      const u = new URL(url)
      if (u.pathname.startsWith('/media/')) return u.pathname + u.search
    } catch (e) {
      return url
    }
  }
  return url
}

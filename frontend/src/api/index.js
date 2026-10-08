import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
})

export const login = (username, password) => api.post('/login', { username, password })
export const register = (username, password, nickname, avatar) => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  if (nickname) formData.append('nickname', nickname)
  if (avatar) formData.append('avatar', avatar)
  
  return api.post('/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
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
    const response = await fetch('http://localhost:8000/api/ai/polish', {
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
  return `http://localhost:8000/assets/${filename}`
}

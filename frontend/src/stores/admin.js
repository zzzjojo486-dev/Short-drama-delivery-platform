import { defineStore } from 'pinia'
import { ref } from 'vue'

// 后台独立会话:凭证单独存在 admin_token / admin_user,
// 与前台 user store(token / user)完全隔离,互不穿越,互不覆盖。
export const useAdminStore = defineStore('admin', () => {
  const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))
  const token = ref(localStorage.getItem('admin_token') || '')

  function login(userData, token) {
    user.value = userData
    localStorage.setItem('admin_user', JSON.stringify(userData))
    if (token) {
      token.value = token
      localStorage.setItem('admin_token', token)
    }
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('admin_user')
    localStorage.removeItem('admin_token')
  }

  return { user, token, login, logout }
})
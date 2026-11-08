import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  function login(userData, token) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
    if (token) {
      token.value = token
      localStorage.setItem('token', token)
    }
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  return { user, login, logout }
})


















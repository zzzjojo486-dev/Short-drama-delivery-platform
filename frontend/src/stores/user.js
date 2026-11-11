import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  function login(userData, accessToken) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
    token.value = accessToken
    localStorage.setItem('token', accessToken)
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  return { user, token, login, logout }
})


















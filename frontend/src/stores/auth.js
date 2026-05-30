import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const cachedUser = localStorage.getItem('user_profile')
  const user = ref(null)
  const token = ref(localStorage.getItem('user_token') || null)
  const authReady = ref(false)
  const loginError = ref('')
  const signupError = ref('')
  const avatarError = ref('')
  const passwordError = ref('')
  const isAuthenticated = computed(() => !!token.value && token.value !== 'guest-token' && !!user.value)

  if (cachedUser) {
    try {
      user.value = JSON.parse(cachedUser)
    } catch {
      localStorage.removeItem('user_profile')
    }
  }

  function setUser(nextUser) {
    user.value = nextUser
    if (nextUser) {
      localStorage.setItem('user_profile', JSON.stringify(nextUser))
    } else {
      localStorage.removeItem('user_profile')
    }
  }

  async function login(phone, password) {
    loginError.value = ''
    try {
      const response = await authApi.login(phone, password)
      token.value = response.data.access_token
      localStorage.setItem('user_token', token.value)
      setUser(response.data.user || null)
      if (!user.value) {
        await fetchUser()
      }
      return true
    } catch (error) {
      console.error('Login failed:', error.response?.data || error)
      loginError.value = error.response?.data?.detail || '登录失败，请稍后重试'
      return false
    }
  }

  async function signup(phone, password, nickname, email) {
    signupError.value = ''
    try {
      await authApi.signup(phone, password, nickname, email)
      token.value = null
      setUser(null)
      localStorage.removeItem('user_token')
      return true
    } catch (error) {
      console.error('Signup failed:', error.response?.data || error)
      signupError.value = error.response?.data?.detail || '注册失败，请稍后重试'
      return false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = null
      setUser(null)
      localStorage.removeItem('user_token')
    }
  }

  async function fetchUser(force = false) {
    if (!token.value || token.value === 'guest-token') {
      token.value = null
      setUser(null)
      localStorage.removeItem('user_token')
      authReady.value = true
      return null
    }

    if (force || !user.value) {
      try {
        const response = await authApi.getMe()
        setUser(response.data)
      } catch {
        await logout()
      }
    }
    authReady.value = true
    return user.value
  }

  async function uploadAvatar(file) {
    avatarError.value = ''
    try {
      const response = await authApi.uploadAvatar(file)
      setUser({ ...user.value, avatar: response.data?.avatar || user.value?.avatar })
      return true
    } catch (error) {
      console.error('Upload avatar failed:', error.response?.data || error)
      avatarError.value = error.response?.data?.detail || '头像上传失败'
      return false
    }
  }

  async function changePassword(oldPassword, newPassword) {
    passwordError.value = ''
    try {
      await authApi.changePassword(oldPassword, newPassword)
      return true
    } catch (error) {
      console.error('Change password failed:', error.response?.data || error)
      passwordError.value = error.response?.data?.detail || '密码修改失败'
      return false
    }
  }

  return { user, token, authReady, loginError, signupError, avatarError, passwordError, isAuthenticated, login, signup, logout, fetchUser, uploadAvatar, changePassword }
})

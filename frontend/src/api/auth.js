import client from './client'

export const authApi = {
  login(phone, password) {
    return client.post('/auth/login', { phone, password })
  },
  signup(phone, password, nickname, email) {
    return client.post('/auth/signup', { phone, password, nickname, email: email || null })
  },
  logout() {
    return client.post('/auth/logout')
  },
  getMe() {
    return client.get('/auth/me')
  },
  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('avatar', file)
    return client.post('/auth/avatar-file', formData)
  }
}

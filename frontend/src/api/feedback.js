import client from './client'

export const feedbackApi = {
  submit(payload) {
    return client.post('/feedback', payload)
  }
}

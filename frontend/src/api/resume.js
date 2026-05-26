import client from './client'

export const resumeApi = {
  analyze(jdContent, experience) {
    return client.post('/resume/analyze', { jd_content: jdContent, experience })
  },
  analyzeUpload(formData) {
    return client.post('/resume/analyze-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getHistory() {
    return client.get('/resume/history')
  },
  getById(id) {
    return client.get(`/resume/${id}`)
  }
}

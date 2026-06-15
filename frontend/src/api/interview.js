import client from './client'

export const interviewApi = {
  start(jobType, context = null) {
    return client.post('/interview/start', { job_type: jobType, ...(context || {}) })
  },
  answer(interviewId, questionIndex, answer) {
    return client.post('/interview/answer', { interview_id: interviewId, question_index: questionIndex, answer })
  },
  complete(interviewId) {
    return client.post('/interview/complete', { interview_id: interviewId })
  },
  getHistory() {
    return client.get('/interview/history')
  },
  getById(id) {
    return client.get(`/interview/${id}`)
  }
}

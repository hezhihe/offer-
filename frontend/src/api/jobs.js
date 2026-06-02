import client from './client'

export const jobsApi = {
  getList(category = 'all', education = 'all', includeExpired = false) {
    return client.get('/jobs', { params: { category, education, include_expired: includeExpired } })
  },
  getById(id) {
    return client.get(`/jobs/${id}`)
  },
  getTodayTip() {
    return client.get('/tips/today')
  },
  getTips() {
    return client.get('/tips')
  },
  getStats() {
    return client.get('/stats/mine')
  },
  recordBrowse(jobId) {
    return client.post(`/jobs/${jobId}/browse`)
  },
  getBrowseHistory() {
    return client.get('/jobs/browse-history')
  }
}

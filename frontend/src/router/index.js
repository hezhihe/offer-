import { createRouter, createWebHashHistory } from 'vue-router'
import { normalizeToken } from '../api/client'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/resume', name: 'Resume', component: () => import('../views/Resume.vue') },
  { path: '/interview', name: 'Interview', component: () => import('../views/Interview.vue') },
  { path: '/calendar', name: 'Calendar', component: () => import('../views/Calendar.vue') },
  { path: '/profile', name: 'Profile', component: () => import('../views/Profile.vue') },
  { path: '/auth', name: 'Auth', component: () => import('../views/Auth.vue') }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = normalizeToken(localStorage.getItem('user_token'))
  if (token) localStorage.setItem('user_token', token)
  const isLoggedIn = !!token && token !== 'guest-token'
  if (to.name !== 'Auth' && !isLoggedIn) {
    next({ name: 'Auth' })
  } else {
    next()
  }
})

export default router

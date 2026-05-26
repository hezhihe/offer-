<template>
  <nav class="bottom-nav">
    <div class="nav-item" :class="{ active: currentPath === '/' }" @click="goTo('/')">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <span>首页</span>
    </div>
    <div class="nav-item" :class="{ active: currentPath === '/resume' }" @click="goTo('/resume')">
      <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM6 4h5v8l-2.5-1.5L6 12V4z"/></svg>
      <span>简历</span>
    </div>
    <div class="nav-item" :class="{ active: currentPath === '/interview' }" @click="goTo('/interview')">
      <svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM4 6h16v12H4V6z"/><circle cx="8" cy="14" r="1.5"/><circle cx="12" cy="14" r="1.5"/><circle cx="16" cy="14" r="1.5"/></svg>
      <span>面试</span>
    </div>
    <div class="nav-item" :class="{ active: currentPath === '/calendar' }" @click="goTo('/calendar')">
      <svg viewBox="0 0 24 24"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/><path d="M7 10h5v5H7z"/></svg>
      <span>日历</span>
    </div>
    <div class="nav-item" :class="{ active: currentPath === '/profile' }" @click="goTo('/profile')">
      <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
      <span>我的</span>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const currentPath = computed(() => route.path)

function goTo(path) {
  if (currentPath.value !== path) {
    router.push(path)
  }
}
</script>
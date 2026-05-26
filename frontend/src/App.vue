<template>
  <div class="app-container">
    <router-view v-if="authStore.authReady || route.name === 'Auth'" v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <BottomNav v-if="showBottomNav" />
  </div>
  <ModalDialog />
  <Toast />
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import BottomNav from './components/BottomNav.vue'
import ModalDialog from './components/ModalDialog.vue'
import Toast from './components/Toast.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const showBottomNav = computed(() => {
  return authStore.isAuthenticated && !['Auth'].includes(route.name)
})

function keepAuthRoute() {
  if (authStore.authReady && !authStore.isAuthenticated && route.name !== 'Auth') {
    router.replace({ name: 'Auth' })
  }
}

onMounted(async () => {
  await authStore.fetchUser(true)
  keepAuthRoute()
})

watch(() => [authStore.authReady, authStore.isAuthenticated, route.name], keepAuthRoute)
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>

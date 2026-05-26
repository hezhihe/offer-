<template>
  <div class="page active">
    <div class="profile-header">
      <div
        class="profile-avatar"
        :style="{ cursor: 'pointer' }"
        @click="isLoggedIn ? triggerUpload() : router.push('/auth')"
      >
        <img
          v-if="displayAvatar"
          class="avatar-img"
          :src="displayAvatar"
          alt=""
          @error="avatarLoadFailed = true"
        />
        <img v-else class="avatar-img" :src="defaultAvatar" alt="" />
        <input
          ref="avatarInput"
          type="file"
          accept="image/*"
          style="display:none"
          @change="handleAvatarChange"
        />
        <div v-if="isLoggedIn" class="avatar-hint">📷</div>
      </div>

      <div class="profile-name">{{ authStore.user?.nickname || '未登录' }}</div>
      <div class="profile-desc">{{ authStore.user?.phone || '点击头像登录' }}</div>

      <button
        v-if="!isLoggedIn"
        class="btn btn-primary"
        style="margin-top:12px;padding:10px 32px"
        @click="router.push('/auth')"
      >
        登录 / 注册
      </button>
    </div>

    <div v-if="isLoggedIn" class="stats-grid">
      <div class="stat-card">
        <div class="stat-num">{{ jobsStore.stats.resume }}</div>
        <div class="stat-label">简历分析</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ jobsStore.stats.interview }}</div>
        <div class="stat-label">模拟面试</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ jobsStore.stats.browse }}</div>
        <div class="stat-label">浏览岗位</div>
      </div>
    </div>

    <div v-if="isLoggedIn" class="card" style="margin-top:16px">
      <div class="menu-list">
        <div class="menu-item" @click="showUsageHistory">
          <div class="mi-left">
            <div class="mi-icon" style="background:#EFF6FF">📊</div>
            <span class="mi-text">使用记录</span>
          </div>
          <span class="mi-arrow">›</span>
        </div>
        <div class="menu-item" @click="showFeedbackForm">
          <div class="mi-left">
            <div class="mi-icon" style="background:#F5F3FF">💬</div>
            <span class="mi-text">意见反馈</span>
          </div>
          <span class="mi-arrow">›</span>
        </div>
        <div class="menu-item" @click="showCommunity">
          <div class="mi-left">
            <div class="mi-icon" style="background:#ECFDF5">👥</div>
            <span class="mi-text">加入社群</span>
          </div>
          <span class="mi-arrow">›</span>
        </div>
        <div class="menu-item" @click="showAbout">
          <div class="mi-left">
            <div class="mi-icon" style="background:#FEF3C7">ℹ️</div>
            <span class="mi-text">关于我们</span>
          </div>
          <span class="mi-arrow">›</span>
        </div>
      </div>
    </div>

    <button
      v-if="isLoggedIn"
      class="btn btn-secondary btn-block"
      style="margin-top:16px"
      @click="logout"
    >
      退出登录
    </button>

    <div class="modal-overlay" :class="{ show: showFeedback }" @click.self="closeFeedback">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeFeedback">×</button>
        <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">意见反馈</h3>
        <form class="feedback-form" @submit.prevent="submitFeedback">
          <div class="input-group">
            <label class="input-label">反馈内容</label>
            <textarea v-model="feedbackContent" placeholder="请输入您的意见或建议..." rows="6"></textarea>
          </div>
          <div class="input-group">
            <label class="input-label">联系方式（选填）</label>
            <input
              v-model="feedbackContact"
              type="text"
              placeholder="邮箱或手机号"
              style="width:100%;border:1.5px solid #E2E8F0;border-radius:var(--radius-sm);padding:12px;font-size:14px"
            />
          </div>
          <button class="btn btn-primary btn-block" :disabled="!feedbackContent.trim()">提交反馈</button>
        </form>
      </div>
    </div>

    <div class="modal-overlay" :class="{ show: showAboutModal }" @click.self="closeAbout">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeAbout">×</button>
        <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">关于 Offer罗盘</h3>
        <p style="font-size:14px;line-height:1.8;color:var(--medium)">
          Offer罗盘是一款面向大学生的 AI 求职助手，帮助用户管理求职申请、优化简历、准备面试和规划职业路径。
        </p>
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid #F1F5F9">
          <p style="font-size:13px;color:var(--medium)">版本: 1.0.0</p>
          <p style="font-size:13px;color:var(--medium);margin-top:4px">© 2026 Offer Compass</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useJobsStore } from '../stores/jobs'
import { useToast } from '../composables/useToast'
import defaultAvatar from '../assets/default-avatar.png'

const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const toast = useToast()

const isLoggedIn = computed(() => !!authStore.token && authStore.token !== 'guest-token')
const avatarInput = ref(null)
const avatarLoadFailed = ref(false)
const showFeedback = ref(false)
const showAboutModal = ref(false)
const feedbackContent = ref('')
const feedbackContact = ref('')
const displayAvatar = computed(() => {
  if (avatarLoadFailed.value) return null
  return authStore.user?.avatar || null
})

watch(() => authStore.user?.avatar, () => {
  avatarLoadFailed.value = false
})

onMounted(async () => {
  if (isLoggedIn.value) {
    await authStore.fetchUser(true)
    jobsStore.fetchStats()
  }
})

function triggerUpload() {
  avatarInput.value?.click()
}

function resizeAvatar(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const image = new Image()
      image.onload = () => {
        const size = 256
        const canvas = document.createElement('canvas')
        const context = canvas.getContext('2d')
        const sourceSize = Math.min(image.width, image.height)
        const sourceX = (image.width - sourceSize) / 2
        const sourceY = (image.height - sourceSize) / 2

        canvas.width = size
        canvas.height = size
        context.drawImage(image, sourceX, sourceY, sourceSize, sourceSize, 0, 0, size, size)
        canvas.toBlob((blob) => {
          if (!blob) {
            reject(new Error('Failed to compress avatar'))
            return
          }
          resolve(new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
        }, 'image/jpeg', 0.82)
      }
      image.onerror = reject
      image.src = reader.result
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    toast.show('请选择图片文件')
    e.target.value = ''
    return
  }

  try {
    const avatarFile = await resizeAvatar(file)
    const ok = await authStore.uploadAvatar(avatarFile)
    toast.show(ok ? '头像已更新' : authStore.avatarError || '头像上传失败')
  } catch {
    toast.show('图片读取失败')
  } finally {
    e.target.value = ''
  }
}

function showUsageHistory() {
  toast.show('使用记录功能开发中')
}

function showFeedbackForm() {
  showFeedback.value = true
}

function closeFeedback() {
  showFeedback.value = false
  feedbackContent.value = ''
  feedbackContact.value = ''
}

function submitFeedback() {
  localStorage.setItem('offer_compass_feedback', JSON.stringify({
    content: feedbackContent.value,
    contact: feedbackContact.value,
    timestamp: new Date().toISOString()
  }))
  toast.show('反馈已提交')
  closeFeedback()
}

function showCommunity() {
  toast.show('社群功能开发中')
}

function showAbout() {
  showAboutModal.value = true
}

function closeAbout() {
  showAboutModal.value = false
}

async function logout() {
  if (authStore.token && authStore.token !== 'guest-token') {
    await authStore.logout()
  } else {
    localStorage.removeItem('user_token')
    authStore.token = null
    authStore.user = null
  }
  toast.show('已退出登录')
  router.push('/auth')
}
</script>

<style scoped>
.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  margin: 0 auto 12px;
  color: var(--white);
  position: relative;
  background-size: cover;
  background-position: center;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-hint {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 24px;
  height: 24px;
  background: var(--white);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}
</style>

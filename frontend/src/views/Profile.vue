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

    <div v-if="isLoggedIn" class="card" style="margin-top:16px">
      <div class="menu-list">
        <div class="menu-item" @click="showUsageHistory('all')">
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
        <div class="menu-item" @click="showPasswordForm">
          <div class="mi-left">
            <div class="mi-icon" style="background:#EEF2FF">🔐</div>
            <span class="mi-text">修改密码</span>
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
        <form class="feedback-form" @submit.prevent="submitFeedbackToServer">
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

    <div class="modal-overlay" :class="{ show: showPasswordModal }" @click.self="closePasswordForm">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closePasswordForm">×</button>
        <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">修改密码</h3>
        <form class="feedback-form" @submit.prevent="submitPasswordChange">
          <div class="input-group">
            <label class="input-label">原密码</label>
            <div class="profile-password-field">
              <input
                v-model="passwordForm.oldPassword"
                :type="showOldPassword ? 'text' : 'password'"
                autocomplete="current-password"
                class="auth-like-input profile-password-input"
                placeholder="请输入当前密码"
              />
              <button type="button" class="profile-password-toggle" @click="showOldPassword = !showOldPassword">
                {{ showOldPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>
          <div class="input-group">
            <label class="input-label">新密码</label>
            <div class="profile-password-field">
              <input
                v-model="passwordForm.newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                autocomplete="new-password"
                class="auth-like-input profile-password-input"
                placeholder="至少 6 位"
              />
              <button type="button" class="profile-password-toggle" @click="showNewPassword = !showNewPassword">
                {{ showNewPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>
          <div class="input-group">
            <label class="input-label">确认新密码</label>
            <div class="profile-password-field">
              <input
                v-model="passwordForm.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password"
                class="auth-like-input profile-password-input"
                placeholder="请再次输入新密码"
              />
              <button type="button" class="profile-password-toggle" @click="showConfirmPassword = !showConfirmPassword">
                {{ showConfirmPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>
          <button class="btn btn-primary btn-block" :disabled="isPasswordSubmitting">
            {{ isPasswordSubmitting ? '修改中...' : '确认修改' }}
          </button>
        </form>
      </div>
    </div>

    <div class="modal-overlay" :class="{ show: showUsageModal }" @click.self="closeUsageHistory">
      <div class="modal-content usage-modal">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeUsageHistory">×</button>
        <h3 class="usage-title">{{ usageModalTitle }}</h3>

        <div v-if="!selectedUsageDetail" class="usage-tabs">
          <button
            v-for="tab in usageTabs"
            :key="tab.value"
            class="usage-tab"
            :class="{ active: usageFilter === tab.value }"
            @click="setUsageFilter(tab.value)"
          >
            <span>{{ tab.label }}</span>
            <strong>{{ tab.count }}</strong>
          </button>
        </div>

        <div v-if="isUsageLoading || isUsageDetailLoading" class="usage-empty">正在加载记录...</div>
        <div v-else-if="selectedUsageDetail?.category === 'interview'" class="usage-detail">
          <button class="usage-back" @click="backToUsageList">返回记录列表</button>
          <h4 class="usage-detail-title">{{ selectedUsageDetail.title }}</h4>
          <div class="usage-detail-time">{{ formatUsageTime(selectedUsageDetail.time) }}</div>

          <div class="usage-detail-section">
            <strong>面试总结</strong>
            <p>{{ interviewStore.historyDetail?.advice || '暂无面试总结' }}</p>
          </div>

          <div class="usage-detail-section">
            <strong>问答记录</strong>
            <div v-for="(item, index) in interviewHistoryDetails" :key="index" class="usage-qa">
              <div class="usage-question">{{ index + 1 }}. {{ item.question }}</div>
              <div class="usage-answer">{{ item.answer || '未作答' }}</div>
              <button
                class="qa-advice-toggle"
                type="button"
                @click="toggleQuestionAdvice(index)"
              >
                {{ expandedAdviceIndexes.has(index) ? '收起修改建议' : '查看修改建议' }}
              </button>
              <div v-if="expandedAdviceIndexes.has(index)" class="qa-advice-panel">
                <div v-if="!item.feedback" class="qa-advice-empty">
                  这条历史记录暂无当时保存的单题复盘。完成新的模拟面试后，这里会展示完整修改建议。
                </div>
                <template v-else>
                  <div
                    v-for="(section, sectionIndex) in feedbackSections(item.feedback)"
                    :key="section.title"
                    class="qa-advice-block"
                  >
                    <strong>{{ section.title }}</strong>
                    <ul>
                      <li v-for="(point, pointIndex) in section.points" :key="`${sectionIndex}-${pointIndex}`">
                        {{ point }}
                      </li>
                    </ul>
                  </div>
                  <div class="qa-advice-summary">
                    <strong>改进建议</strong>
                    <p>{{ item.feedback.suggestion || item.feedback.summary || '建议围绕问题补充具体场景、个人动作、量化结果和复盘结论。' }}</p>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="filteredUsageRecords.length === 0" class="usage-empty">
          暂无使用记录。完成一次简历分析、模拟面试或浏览岗位后，这里会自动更新。
        </div>
        <div v-else class="usage-list">
          <div
            v-for="record in filteredUsageRecords"
            :key="record.key"
            class="usage-item"
            :class="{ clickable: record.category === 'interview' }"
            @click="openUsageRecord(record)"
          >
            <div class="usage-type">{{ record.type }}</div>
            <div class="usage-main">{{ record.title }}</div>
            <div class="usage-sub">{{ record.subtitle }}</div>
            <div class="usage-time">{{ formatUsageTime(record.time) }}</div>
            <div v-if="record.category === 'interview'" class="usage-action">查看面试总结</div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-overlay" :class="{ show: showAboutModal }" @click.self="closeAbout">
      <div class="modal-content">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeAbout">×</button>
        <h3 style="font-size:18px;font-weight:700;margin-bottom:16px">关于 Offer罗盘</h3>
        <p style="font-size:14px;line-height:1.8;color:var(--medium)">
          Offer罗盘是一款面向大学生的 AI 求职助手，帮助用户管理求职申请、优化简历、准备面试和规划职业路径，一站式扫清求职路上的难关。
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
import { useResumeStore } from '../stores/resume'
import { useInterviewStore } from '../stores/interview'
import { useToast } from '../composables/useToast'
import { feedbackApi } from '../api/feedback'
import defaultAvatar from '../assets/default-avatar.png'

const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const resumeStore = useResumeStore()
const interviewStore = useInterviewStore()
const toast = useToast()

const isLoggedIn = computed(() => !!authStore.token && authStore.token !== 'guest-token')
const avatarInput = ref(null)
const avatarLoadFailed = ref(false)
const showFeedback = ref(false)
const showPasswordModal = ref(false)
const showAboutModal = ref(false)
const showUsageModal = ref(false)
const isUsageLoading = ref(false)
const isUsageDetailLoading = ref(false)
const selectedUsageDetail = ref(null)
const expandedAdviceIndexes = ref(new Set())
const usageFilter = ref('resume')
const feedbackContent = ref('')
const feedbackContact = ref('')
const isFeedbackSubmitting = ref(false)
const isPasswordSubmitting = ref(false)
const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const passwordForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const displayAvatar = computed(() => {
  if (avatarLoadFailed.value) return null
  return authStore.user?.avatar || null
})

const usageRecords = computed(() => {
  const resumeRecords = resumeStore.history.map(item => ({
    key: `resume-${item.id}`,
    id: item.id,
    category: 'resume',
    type: '简历分析',
    title: item.job_title || '简历分析记录',
    subtitle: item.match_score != null ? `匹配度 ${item.match_score}%` : '已生成简历分析结果',
    time: item.created_at
  }))

  const interviewRecords = interviewStore.history.map(item => ({
    key: `interview-${item.id}`,
    id: item.id,
    category: 'interview',
    type: '模拟面试',
    title: interviewStore.jobTypeNames[item.job_type] || item.job_type || '模拟面试记录',
    subtitle: '已完成一轮模拟面试',
    time: item.created_at
  }))

  const browseRecords = jobsStore.browseHistory.map((item, index) => ({
    key: `browse-${item.id}-${item.viewedAt || index}`,
    id: item.id,
    category: 'browse',
    type: '浏览岗位',
    title: item.title || '岗位记录',
    subtitle: [item.company, item.salary, item.date].filter(Boolean).join(' · '),
    time: item.viewedAt
  }))

  return [...resumeRecords, ...interviewRecords, ...browseRecords]
    .sort((a, b) => new Date(b.time || 0) - new Date(a.time || 0))
})

const filteredUsageRecords = computed(() => {
  return usageRecords.value.filter(record => record.category === usageFilter.value)
})

const usageRecordCounts = computed(() => ({
  resume: usageRecords.value.filter(record => record.category === 'resume').length,
  interview: usageRecords.value.filter(record => record.category === 'interview').length,
  browse: usageRecords.value.filter(record => record.category === 'browse').length
}))

const usageModalTitle = computed(() => {
  const titles = {
    usage: '使用记录',
    resume: '简历分析记录',
    interview: '模拟面试记录',
    browse: '浏览岗位记录'
  }
  return selectedUsageDetail.value ? titles[usageFilter.value] || titles.usage : titles.usage
})

const usageTabs = computed(() => [
  {
    value: 'resume',
    label: '简历分析',
    count: usageRecordCounts.value.resume
  },
  {
    value: 'interview',
    label: '模拟面试',
    count: usageRecordCounts.value.interview
  },
  {
    value: 'browse',
    label: '浏览岗位',
    count: usageRecordCounts.value.browse
  }
])

const interviewHistoryDetails = computed(() => {
  const detail = interviewStore.historyDetail
  if (!detail) return []
  if (Array.isArray(detail.details)) return detail.details
  const questions = Array.isArray(detail.questions) ? detail.questions : []
  const answers = Array.isArray(detail.answers) ? detail.answers : []
  const feedbacks = Array.isArray(detail.feedbacks) ? detail.feedbacks : []
  return questions.map((question, index) => ({
    question,
    answer: answers[index] || '',
    feedback: feedbacks[index] || null
  }))
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

async function showUsageHistory(type = 'resume') {
  usageFilter.value = type === 'all' ? 'resume' : type
  selectedUsageDetail.value = null
  expandedAdviceIndexes.value = new Set()
  showUsageModal.value = true
  isUsageLoading.value = true
  try {
    await Promise.all([
      resumeStore.fetchHistory(),
      interviewStore.fetchHistory(),
      jobsStore.fetchStats()
    ])
  } finally {
    isUsageLoading.value = false
  }
}

async function setUsageFilter(type) {
  usageFilter.value = type
  selectedUsageDetail.value = null
  expandedAdviceIndexes.value = new Set()
  interviewStore.clearHistoryDetail()

  if (type === 'resume' && resumeStore.history.length === 0) {
    isUsageLoading.value = true
    try {
      await resumeStore.fetchHistory()
    } finally {
      isUsageLoading.value = false
    }
  }

  if (type === 'interview' && interviewStore.history.length === 0) {
    isUsageLoading.value = true
    try {
      await interviewStore.fetchHistory()
    } finally {
      isUsageLoading.value = false
    }
  }
}

function closeUsageHistory() {
  showUsageModal.value = false
  selectedUsageDetail.value = null
  expandedAdviceIndexes.value = new Set()
  interviewStore.clearHistoryDetail()
}

function backToUsageList() {
  selectedUsageDetail.value = null
  expandedAdviceIndexes.value = new Set()
  interviewStore.clearHistoryDetail()
}

async function openUsageRecord(record) {
  if (record.category !== 'interview') return
  selectedUsageDetail.value = record
  expandedAdviceIndexes.value = new Set()
  isUsageDetailLoading.value = true
  try {
    await interviewStore.fetchHistoryDetail(record.id)
  } catch {
    toast.show('面试总结加载失败')
    selectedUsageDetail.value = null
  } finally {
    isUsageDetailLoading.value = false
  }
}

function toggleQuestionAdvice(index) {
  const next = new Set(expandedAdviceIndexes.value)
  if (next.has(index)) {
    next.delete(index)
  } else {
    next.add(index)
  }
  expandedAdviceIndexes.value = next
}

function feedbackSections(feedback) {
  if (!feedback) return []

  const dimensionSections = Array.isArray(feedback.dimensions)
    ? feedback.dimensions
        .map(item => ({
          title: item.label || '分析项',
          points: splitAdviceText(item.comment)
        }))
        .filter(section => section.points.length)
    : []

  if (dimensionSections.length) return dimensionSections

  return [
    {
      title: '回答亮点',
      points: Array.isArray(feedback.hit_points) && feedback.hit_points.length
        ? feedback.hit_points
        : ['本题暂无明确亮点记录。']
    },
    {
      title: '提升机会',
      points: Array.isArray(feedback.missed_points) && feedback.missed_points.length
        ? feedback.missed_points
        : ['建议补充更具体的岗位证据。']
    },
    {
      title: '行动建议',
      points: Array.isArray(feedback.rewrite_advice) && feedback.rewrite_advice.length
        ? feedback.rewrite_advice
        : ['建议围绕问题补充具体场景、个人动作、量化结果和复盘结论。']
    }
  ]
}

function splitAdviceText(value) {
  if (!value) return []
  return String(value)
    .split(/[；;。]\s*/)
    .map(item => item.trim())
    .filter(Boolean)
}

function formatUsageTime(value) {
  if (!value) return '时间未知'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间未知'
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
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

async function submitFeedbackToServer() {
  if (!feedbackContent.value.trim() || isFeedbackSubmitting.value) return

  isFeedbackSubmitting.value = true
  try {
    await feedbackApi.submit({
      content: feedbackContent.value,
      contact: feedbackContact.value || null,
      page_url: window.location.href
    })
    toast.show('反馈已提交')
    closeFeedback()
  } catch (error) {
    console.error('Submit feedback failed:', error.response?.data || error)
    toast.show(error.response?.data?.detail || '反馈提交失败')
  } finally {
    isFeedbackSubmitting.value = false
  }
}

function showPasswordForm() {
  showPasswordModal.value = true
}

function closePasswordForm() {
  showPasswordModal.value = false
  passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  showOldPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
}

function validatePasswordForm() {
  if (!passwordForm.value.oldPassword.trim()) {
    toast.show('请输入原密码')
    return false
  }
  if (passwordForm.value.newPassword.length < 6) {
    toast.show('新密码至少需要 6 位')
    return false
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    toast.show('两次输入的新密码不一致')
    return false
  }
  if (passwordForm.value.oldPassword === passwordForm.value.newPassword) {
    toast.show('新密码不能和旧密码相同')
    return false
  }
  return true
}

async function submitPasswordChange() {
  if (!validatePasswordForm() || isPasswordSubmitting.value) return

  isPasswordSubmitting.value = true
  try {
    const ok = await authStore.changePassword(
      passwordForm.value.oldPassword,
      passwordForm.value.newPassword
    )
    if (ok) {
      toast.show('密码已修改，请重新登录')
      closePasswordForm()
      await authStore.logout()
      router.push('/auth')
    } else {
      toast.show(authStore.passwordError || '密码修改失败')
    }
  } finally {
    isPasswordSubmitting.value = false
  }
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

.auth-like-input {
  border: 1.5px solid #e2e8f0;
  border-radius: var(--radius-sm);
  box-sizing: border-box;
  font-size: 14px;
  padding: 12px;
  width: 100%;
}

.profile-password-field {
  position: relative;
}

.profile-password-input {
  padding-right: 58px;
}

.profile-password-toggle {
  background: none;
  border: 0;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 4px;
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.usage-modal {
  max-height: 78vh;
  display: flex;
  flex-direction: column;
}

.usage-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

.usage-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 14px;
}

.usage-tab {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  color: var(--medium);
  min-height: 72px;
  padding: 10px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
}

.usage-tab span {
  max-width: 100%;
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usage-tab strong {
  color: var(--dark);
  font-size: 18px;
  line-height: 1;
}

.usage-tab.active {
  border-color: var(--blue);
  background: #eff6ff;
  color: var(--blue);
}

.usage-tab.active strong {
  color: var(--blue);
}

.usage-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  padding-right: 4px;
}

.usage-item {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.usage-item.clickable {
  cursor: pointer;
}

.usage-item.clickable:active {
  transform: scale(0.99);
}

.usage-type {
  display: inline-flex;
  width: fit-content;
  padding: 3px 8px;
  border-radius: 999px;
  background: #eff6ff;
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.usage-main {
  color: var(--dark);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
}

.usage-sub {
  color: var(--medium);
  font-size: 13px;
  line-height: 1.5;
  margin-top: 4px;
}

.usage-time {
  color: var(--medium);
  font-size: 12px;
  margin-top: 8px;
}

.usage-action {
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
  margin-top: 8px;
}

.usage-back {
  width: fit-content;
  border: 0;
  background: #eff6ff;
  color: var(--blue);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
}

.usage-detail-title {
  color: var(--dark);
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 4px;
}

.usage-detail-time {
  color: var(--medium);
  font-size: 13px;
  margin-bottom: 14px;
}

.usage-detail-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 14px;
  margin-top: 14px;
}

.usage-detail-section strong {
  display: block;
  color: var(--dark);
  font-size: 15px;
  margin-bottom: 8px;
}

.usage-detail-section p,
.usage-answer {
  color: var(--medium);
  font-size: 14px;
  line-height: 1.7;
}

.usage-qa {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px;
  margin-top: 10px;
}

.usage-question {
  color: var(--dark);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.6;
  margin-bottom: 6px;
}

.qa-advice-toggle {
  border: 0;
  border-radius: 999px;
  background: #eff6ff;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  margin-top: 10px;
  padding: 7px 12px;
}

.qa-advice-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  margin-top: 10px;
  padding: 12px;
}

.qa-advice-block + .qa-advice-block {
  border-top: 1px solid #e2e8f0;
  margin-top: 10px;
  padding-top: 10px;
}

.qa-advice-block strong {
  color: var(--dark);
  display: block;
  font-size: 13px;
  margin-bottom: 6px;
}

.qa-advice-block ul {
  color: var(--medium);
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
  padding-left: 18px;
}

.usage-empty {
  color: var(--medium);
  font-size: 14px;
  line-height: 1.7;
  padding: 18px 0;
}
</style>

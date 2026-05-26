<template>
  <div class="page auth-page">
    <div class="card auth-card">
      <div class="auth-brand">
        <div class="auth-logo">🧭</div>
        <h2 class="gradient-text">Offer罗盘</h2>
        <p>AI 驱动的求职助手</p>
      </div>

      <div v-if="!isSignup">
        <h3 class="auth-title">登录</h3>
        <form @submit.prevent="handleLogin">
          <div class="input-group">
            <label class="input-label">手机号</label>
            <input
              v-model.trim="loginForm.phone"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              placeholder="请输入 11 位手机号"
              class="auth-input"
            />
          </div>

          <div class="input-group">
            <label class="input-label">密码</label>
            <div class="password-field">
              <input
                v-model="loginForm.password"
                :type="showLoginPwd ? 'text' : 'password'"
                placeholder="请输入密码"
                class="auth-input password-input"
              />
              <button type="button" class="password-toggle" tabindex="-1" @click="showLoginPwd = !showLoginPwd">
                {{ showLoginPwd ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <button class="btn btn-primary btn-block" :disabled="isSubmitting">
            {{ isSubmitting ? '登录中...' : '登录' }}
          </button>
        </form>

        <p class="auth-switch">
          还没有账号？
          <a href="#" @click.prevent="toggleMode">立即注册</a>
        </p>
      </div>

      <div v-else>
        <h3 class="auth-title">注册</h3>
        <form @submit.prevent="handleSignup">
          <div class="input-group">
            <label class="input-label">昵称</label>
            <input
              v-model.trim="signupForm.nickname"
              type="text"
              placeholder="请输入昵称"
              class="auth-input"
            />
          </div>

          <div class="input-group">
            <label class="input-label">手机号</label>
            <input
              v-model.trim="signupForm.phone"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              placeholder="请输入 11 位手机号"
              class="auth-input"
            />
          </div>

          <div class="input-group">
            <label class="input-label">密码</label>
            <div class="password-field">
              <input
                v-model="signupForm.password"
                :type="showSignupPwd ? 'text' : 'password'"
                placeholder="请输入密码"
                class="auth-input password-input"
              />
              <button type="button" class="password-toggle" tabindex="-1" @click="showSignupPwd = !showSignupPwd">
                {{ showSignupPwd ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="input-group">
            <label class="input-label">确认密码</label>
            <div class="password-field">
              <input
                v-model="signupForm.confirmPassword"
                :type="showConfirmPwd ? 'text' : 'password'"
                placeholder="请再次输入密码"
                class="auth-input password-input"
              />
              <button type="button" class="password-toggle" tabindex="-1" @click="showConfirmPwd = !showConfirmPwd">
                {{ showConfirmPwd ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="input-group">
            <label class="input-label">
              邮箱
              <span class="optional-text">可选，用于接收简历投递通知</span>
            </label>
            <input
              v-model.trim="signupForm.email"
              type="email"
              placeholder="请输入邮箱"
              class="auth-input"
            />
          </div>

          <button class="btn btn-primary btn-block" :disabled="isSubmitting">
            {{ isSubmitting ? '注册中...' : '注册' }}
          </button>
        </form>

        <p class="auth-switch">
          已有账号？
          <a href="#" @click.prevent="toggleMode">立即登录</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const isSignup = ref(false)
const showLoginPwd = ref(false)
const showSignupPwd = ref(false)
const showConfirmPwd = ref(false)
const isSubmitting = ref(false)
const loginForm = ref({ phone: '', password: '' })
const signupForm = ref({ nickname: '', phone: '', password: '', confirmPassword: '', email: '' })

const isValidPhone = (phone) => /^1\d{10}$/.test(phone)
const isValidEmail = (email) => !email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

function toggleMode() {
  if (isSubmitting.value) return
  isSignup.value = !isSignup.value
}

function validateLogin() {
  if (!isValidPhone(loginForm.value.phone)) {
    toast.show('请输入正确的 11 位手机号')
    return false
  }
  if (!loginForm.value.password.trim()) {
    toast.show('请输入密码')
    return false
  }
  return true
}

function validateSignup() {
  if (!signupForm.value.nickname.trim()) {
    toast.show('请输入昵称')
    return false
  }
  if (!isValidPhone(signupForm.value.phone)) {
    toast.show('手机号必须是 11 位数字，例如 13890010004')
    return false
  }
  if (!signupForm.value.password.trim()) {
    toast.show('请输入密码')
    return false
  }
  if (signupForm.value.password !== signupForm.value.confirmPassword) {
    toast.show('两次输入的密码不一致')
    return false
  }
  if (!isValidEmail(signupForm.value.email)) {
    toast.show('请输入正确的邮箱格式')
    return false
  }
  return true
}

async function handleLogin() {
  if (!validateLogin() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const success = await authStore.login(loginForm.value.phone, loginForm.value.password)
    if (success) {
      toast.show('登录成功')
      router.push('/')
    } else {
      toast.show(authStore.loginError || '登录失败，请稍后重试')
    }
  } finally {
    isSubmitting.value = false
  }
}

async function handleSignup() {
  if (!validateSignup() || isSubmitting.value) return

  isSubmitting.value = true
  try {
    const success = await authStore.signup(
      signupForm.value.phone,
      signupForm.value.password,
      signupForm.value.nickname,
      signupForm.value.email
    )

    if (success) {
      toast.show('注册成功，请登录')
      loginForm.value.phone = signupForm.value.phone
      loginForm.value.password = ''
      signupForm.value = { nickname: '', phone: '', password: '', confirmPassword: '', email: '' }
      showSignupPwd.value = false
      showConfirmPwd.value = false
      isSignup.value = false
    } else {
      toast.show(authStore.signupError || '注册失败，请稍后重试')
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: calc(100vh - 100px);
}

.auth-card {
  max-width: 360px;
  margin: 0 auto;
}

.auth-brand {
  text-align: center;
  margin-bottom: 24px;
}

.auth-logo {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  font-size: 32px;
  color: var(--white);
}

.auth-brand h2 {
  font-size: 24px;
  font-weight: 800;
}

.auth-brand p {
  font-size: 14px;
  color: var(--medium);
  margin-top: 4px;
}

.auth-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 20px;
  text-align: center;
}

.auth-input {
  width: 100%;
  border: 1.5px solid #e2e8f0;
  border-radius: var(--radius-sm);
  padding: 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.password-field {
  position: relative;
}

.password-input {
  padding-right: 56px;
}

.password-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 4px;
}

.auth-switch {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: var(--medium);
}

.auth-switch a {
  color: var(--blue);
  font-weight: 600;
}

.optional-text {
  color: var(--medium);
  font-weight: 400;
  font-size: 12px;
}
</style>

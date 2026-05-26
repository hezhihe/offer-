<template>
  <div class="page active">
    <h1 class="section-title" style="margin-bottom:16px">
      <span class="icon" style="background:var(--blue-light)">📄</span>
      简历分析与重构
    </h1>

    <!-- JD 输入 -->
    <div class="input-group" style="margin-bottom:16px">
      <label class="input-label">📋 职位描述 (JD)</label>
      <textarea
        v-model="jdContent"
        placeholder="把招聘方发的职位描述粘贴到这里..."
        rows="6"
      ></textarea>
    </div>

    <!-- 简历输入 - 两种模式 -->
    <div class="input-group" style="margin-bottom:16px">
      <label class="input-label">📝 我的简历</label>

      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button 
          class="btn btn-sm" 
          :class="mode === 'upload' ? 'btn-primary' : 'btn-secondary'"
          @click="mode = 'upload'"
        >📁 上传文件</button>
        <button 
          class="btn btn-sm" 
          :class="mode === 'paste' ? 'btn-primary' : 'btn-secondary'"
          @click="mode = 'paste'"
        >📋 粘贴文本</button>
      </div>

      <!-- 上传模式 -->
      <div v-if="mode === 'upload'">
        <div 
          class="upload-zone" 
          @click="$refs.fileInput.click()"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <div style="font-size:36px;margin-bottom:8px">📤</div>
          <div v-if="!selectedFile" style="color:var(--medium)">
            点击选择文件 或 拖拽到此处<br>
            <span style="font-size:12px">支持 PDF、Word (.docx)</span>
          </div>
          <div v-else style="color:var(--green);font-weight:600">
            ✅ {{ selectedFile.name }}
          </div>
        </div>
        <input 
          ref="fileInput" 
          type="file" 
          accept=".pdf,.docx,.doc" 
          style="display:none" 
          @change="handleFileSelect"
        />
      </div>

      <!-- 粘贴模式 -->
      <div v-else>
        <textarea
          v-model="resumeText"
          placeholder="把你的完整简历粘贴到这里（教育背景、项目经验、技能等）..."
          rows="8"
        ></textarea>
      </div>
    </div>

    <button
      class="btn btn-primary btn-block"
      @click="analyze"
      :disabled="analyzing"
    >
      <span v-if="analyzing" class="loading-dots">
        <span></span><span></span><span></span>
      </span>
      <span v-else>🤖 AI分析与重构</span>
    </button>

    <!-- 分析结果 -->
    <div v-if="result" class="card" style="margin-top:20px">
      <div class="match-score">
        <div class="score-circle" :style="{ background: matchColor }">{{ result.match_score }}%</div>
        <div class="score-info">
          <h4>匹配度评估</h4>
          <p>与目标岗位的契合度分析</p>
          <div class="match-bar">
            <div class="match-bar-fill" :style="{ width: result.match_score + '%', background: matchColor }"></div>
          </div>
        </div>
      </div>

      <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">🔑 关键词匹配分析</h3>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">
        <span
          v-for="kw in result.keywords"
          :key="kw.word"
          class="badge"
          :class="kw.match === 'true' ? 'badge-green' : 'badge-amber'"
        >
          {{ kw.match === 'true' ? '✅' : '❌' }} {{ kw.word }}
        </span>
      </div>

      <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">✨ AI重构简历</h3>
      <div class="result-area">{{ result.refactored_resume }}</div>

      <button class="btn btn-secondary btn-sm btn-block" style="margin-top:12px" @click="copyResult">
        📋 一键复制
      </button>
    </div>

    <!-- 历史记录 -->
    <div v-if="resumeStore.history.length > 0" style="margin-top:24px">
      <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">📊 分析历史</h3>
      <div
        v-for="item in resumeStore.history"
        :key="item.id"
        class="card"
        style="margin-bottom:10px;padding:14px;cursor:pointer"
        @click="viewHistory(item)"
      >
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <div style="font-weight:600;font-size:14px">{{ item.job_title || '简历分析' }}</div>
            <div style="font-size:12px;color:var(--medium);margin-top:2px">{{ formatDate(item.created_at) }}</div>
          </div>
          <div style="font-size:24px;font-weight:800" :style="{ color: item.match_score >= 70 ? 'var(--green)' : 'var(--amber)' }">
            {{ item.match_score }}%
          </div>
        </div>
      </div>
    </div>

    <div
      class="modal-overlay"
      :class="{ show: resumeStore.historyDetail || resumeStore.isLoadingDetail }"
      @click.self="closeHistoryDetail"
    >
      <div class="modal-content history-detail-modal">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeHistoryDetail">×</button>

        <div v-if="resumeStore.isLoadingDetail" class="empty-state">
          <div class="es-icon">...</div>
          <p>正在加载历史详情</p>
        </div>

        <div v-else-if="resumeStore.historyDetail">
          <h3 class="detail-title">{{ resumeStore.historyDetail.job_title || '简历分析详情' }}</h3>
          <div class="detail-subtitle">{{ formatDate(resumeStore.historyDetail.created_at) }}</div>

          <div class="match-score" style="margin-top:16px">
            <div class="score-circle" :style="{ background: detailMatchColor }">{{ resumeStore.historyDetail.match_score }}%</div>
            <div class="score-info">
              <h4>匹配度评估</h4>
              <p>这次分析保存的完整结果</p>
              <div class="match-bar">
                <div class="match-bar-fill" :style="{ width: resumeStore.historyDetail.match_score + '%', background: detailMatchColor }"></div>
              </div>
            </div>
          </div>

          <h4 class="detail-section-title">关键词匹配</h4>
          <div class="keyword-list">
            <span
              v-for="kw in detailKeywords"
              :key="kw.word"
              class="badge"
              :class="isKeywordMatched(kw) ? 'badge-green' : 'badge-amber'"
            >
              {{ isKeywordMatched(kw) ? '✓' : '△' }} {{ kw.word }}
            </span>
          </div>

          <h4 class="detail-section-title">AI重构简历</h4>
          <div class="result-area">{{ resumeStore.historyDetail.reconstructed_resume }}</div>

          <details class="history-raw">
            <summary>查看原始输入</summary>
            <h4 class="detail-section-title">原始 JD</h4>
            <div class="result-area">{{ resumeStore.historyDetail.original_jd }}</div>
            <h4 class="detail-section-title">原始简历</h4>
            <div class="result-area">{{ resumeStore.historyDetail.original_resume }}</div>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useResumeStore } from '../stores/resume'
import { resumeApi } from '../api/resume'
import { useToast } from '../composables/useToast'

const resumeStore = useResumeStore()
const toast = useToast()

const mode = ref('upload')
const jdContent = ref('')
const resumeText = ref('')
const selectedFile = ref(null)
const analyzing = ref(false)
const result = ref(null)

onMounted(() => {
  resumeStore.fetchHistory()
})

const matchColor = computed(() => {
  if (!result.value) return '#666'
  const s = result.value.match_score
  if (s >= 80) return 'var(--green)'
  if (s >= 60) return 'var(--amber)'
  return 'var(--red)'
})

function handleFileSelect(e) {
  selectedFile.value = e.target.files[0] || null
}

function handleDrop(e) {
  selectedFile.value = e.dataTransfer.files[0] || null
}

async function analyze() {
  if (!jdContent.value.trim()) {
    toast.show('请先填写职位描述 JD')
    return
  }

  if (!selectedFile.value && !resumeText.value.trim()) {
    toast.show('请先上传简历或粘贴简历内容')
    return
  }

  analyzing.value = true
  result.value = null

  try {
    if (mode.value === 'upload' && selectedFile.value) {
      const formData = new FormData()
      formData.append('jd_content', jdContent.value)
      formData.append('resume_file', selectedFile.value)
      const response = await resumeApi.analyzeUpload(formData)
      result.value = response.data
    } else {
      const response = await resumeApi.analyze(jdContent.value, resumeText.value)
      result.value = response.data
    }
    resumeStore.fetchHistory()
  } catch (e) {
    toast.show('分析失败：' + (e.response?.data?.detail || e.message || '请稍后重试'))
  } finally {
    analyzing.value = false
  }
}

function copyResult() {
  if (result.value) {
    navigator.clipboard.writeText(result.value.refactored_resume)
    toast.show('已复制到剪贴板')
  }
}

function viewHistoryAlert(item) {
  alert(`查看历史：${item.job_title}，匹配度 ${item.match_score}%`)
}

const detailMatchColor = computed(() => {
  const s = resumeStore.historyDetail?.match_score || 0
  if (s >= 80) return 'var(--green)'
  if (s >= 60) return 'var(--amber)'
  return 'var(--red)'
})

const detailKeywords = computed(() => {
  const keywords = resumeStore.historyDetail?.keywords || []
  if (Array.isArray(keywords)) return keywords
  try {
    return JSON.parse(keywords)
  } catch {
    return []
  }
})

function isKeywordMatched(keyword) {
  return keyword.match === true || keyword.match === 'true'
}

async function viewHistory(item) {
  try {
    await resumeStore.fetchHistoryDetail(item.id)
  } catch (e) {
    toast.show('加载历史详情失败：' + (e.response?.data?.detail || e.message || '请稍后重试'))
  }
}

function closeHistoryDetail() {
  resumeStore.clearHistoryDetail()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-zone:hover {
  border-color: var(--blue);
  background: rgba(59,130,246,0.05);
}
.history-detail-modal {
  position: relative;
}
.detail-title {
  font-size: 18px;
  font-weight: 800;
  padding-right: 40px;
}
.detail-subtitle {
  font-size: 12px;
  color: var(--medium);
  margin-top: 4px;
}
.detail-section-title {
  font-size: 14px;
  font-weight: 700;
  margin: 16px 0 10px;
}
.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.history-raw {
  margin-top: 16px;
}
.history-raw summary {
  cursor: pointer;
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
}
</style>

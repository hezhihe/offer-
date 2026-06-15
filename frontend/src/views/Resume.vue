<!--
页面职责：简历分析页总控。
负责：JD/简历输入、上传文件、调用分析接口、保存岗位简历版本、加入投递跟进、进入模拟面试。
边界：分析结果展示已拆到 ResumeAnalysisResult.vue；不要继续把大块结果 UI 塞回本页面。
-->

<template>
  <div class="page active">
    <h1 class="section-title" style="margin-bottom:16px">
      <span class="icon" style="background:var(--blue-light)">📄</span>
      简历分析与重构
    </h1>


    <ResumeDiagnosisContextCard
      v-if="diagnosisContext && !showAnalysisResult"
      :diagnosis-context="diagnosisContext"
      @clear="clearDiagnosisContext"
    />
    <!-- JD 输入 -->
    <div v-if="!showAnalysisResult" class="input-group" style="margin-bottom:16px">
      <label class="input-label">📋 职位描述 (JD)</label>
      <textarea
        v-model="jdContent"
        placeholder="把招聘方发布的职位描述粘贴到这里..."
        rows="6"
      ></textarea>
    </div>

    <!-- 简历输入 - 两种模式 -->
    <div v-if="!showAnalysisResult" class="input-group" style="margin-bottom:16px">
      <label class="input-label">📄 我的简历</label>

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
            ✅{{ selectedFile.name }}
          </div>
        </div>
        <div v-if="selectedFile" class="selected-file-actions">
          <button type="button" class="preview-file-btn" @click="openSelectedFile">
            打开简历
          </button>
          <button type="button" class="remove-file-btn" @click="removeSelectedFile">
            删除已选文件
          </button>
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
          placeholder="把你的完整简历粘贴到这里（教育背景、项目经历、技能等）..."
          rows="8"
        ></textarea>
      </div>
    </div>

    <button
      v-if="!showAnalysisResult"
      class="btn btn-primary btn-block resume-analyze-btn"
      @click="analyze"
      :disabled="analyzing"
    >
      <LoadingDots v-if="analyzing" variant="primary" />
      <span v-else>🤖 AI分析与重构</span>
    </button>

    <!-- 分析结果 -->
    <ResumeAnalysisResult
      v-if="result && showAnalysisResult"
      :result="result"
      :match-color="matchColor"
      :readiness-reason="cleanDisplayText(result.readiness_reason)"
      :should-apply-now="shouldApplyNow"
      :should-revise-again="shouldReviseAgain"
      :should-prepare-interview="shouldPrepareInterview"
      :jd-requirements="jdRequirements"
      :matched-evidence="matchedEvidence"
      :cleaned-keywords="cleanedKeywords"
      :ability-gaps="abilityGaps"
      :rewrite-suggestions="rewriteSuggestions"
      :refactored-resume-text="refactoredResumeText"
      @back="backToAnalysisInput"
      @reanalyze="reanalyzeCurrentVersion"
      @start-interview="startInterviewFromCurrentResult"
      @save-version="saveCurrentJobVersion"
      @track-job="saveAndTrackCurrentJob"
      @copy="copyResult"
    />
    <!-- 历史记录 -->
    <div v-if="!showAnalysisResult && resumeStore.history.length > 0" style="margin-top:24px">
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
          <LoadingDots class="es-icon" variant="history" block />
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

          <div v-if="detailReadinessLabel" class="readiness-card" :class="`readiness-${detailReadinessLevel}`">
            <div class="readiness-header">
              <strong>投递准备度</strong>
              <span class="readiness-pill">{{ detailReadinessLabel }}</span>
            </div>
            <p>{{ detailReadinessReason }}</p>
          </div>

          <div class="next-action-card">
            <h3>下一步行动建议</h3>
            <div class="next-action-grid">
              <button class="next-action" :class="{ active: detailShouldApplyNow }" type="button">
                <strong>{{ detailShouldApplyNow ? '建议投递' : '暂不建议直接投递' }}</strong>
                <span>{{ detailShouldApplyNow ? '这版简历可以进入投递跟进。' : '先补齐关键证据再投，别浪费岗位机会。' }}</span>
              </button>
              <button class="next-action" :class="{ active: detailShouldReviseAgain }" type="button">
                <strong>{{ detailShouldReviseAgain ? '建议再次修改后分析' : '可继续微调' }}</strong>
                <span>回到当前 JD 和简历，按缺口补证据后再分析。</span>
              </button>
              <button class="next-action" :class="{ active: detailShouldPrepareInterview }" type="button">
                <strong>{{ detailShouldPrepareInterview ? '建议进入模拟面试' : '面试准备可稍后' }}</strong>
                <span>匹配度达标后，用岗位方向训练回答。</span>
              </button>
            </div>
          </div>

          <div v-if="detailJdRequirements.length" class="analysis-block">
            <h3>JD核心要求</h3>
            <div v-for="item in detailJdRequirements" :key="item" class="insight-item requirement-item">{{ item }}</div>
          </div>

          <div v-if="detailMatchedEvidence.length" class="analysis-block">
            <h3>简历已有证据</h3>
            <div v-for="item in detailMatchedEvidence" :key="item" class="insight-item evidence-item">{{ item }}</div>
          </div>

          <h4 class="detail-section-title">匹配关键词</h4>
          <div class="keyword-list">
            <span v-for="kw in detailKeywords" :key="kw.word" class="badge" :class="isKeywordMatched(kw) ? 'badge-green' : 'badge-amber'">
              {{ isKeywordMatched(kw) ? '✓' : '!' }} {{ cleanDisplayText(kw.word) }}
            </span>
          </div>

          <div v-if="detailAbilityGaps.length" class="analysis-block">
            <h3>能力缺口</h3>
            <div v-for="gap in detailAbilityGaps" :key="gap" class="gap-item">{{ gap }}</div>
          </div>

          <div v-if="detailRewriteSuggestions.length" class="analysis-block">
            <h3>改写建议</h3>
            <div v-for="item in detailRewriteSuggestions" :key="item" class="rewrite-template">{{ item }}</div>
          </div>

          <h4 class="detail-section-title">可参考表达片段</h4>
          <div class="result-area">{{ detailRefactoredResumeText }}</div>

          <details class="history-raw">
            <summary>查看原始输入</summary>
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
import { useRouter } from 'vue-router'
import { useResumeStore } from '../stores/resume'
import { useJobsStore } from '../stores/jobs'
import { resumeApi } from '../api/resume'
import { useToast } from '../composables/useToast'
import LoadingDots from '../components/LoadingDots.vue'
import ResumeAnalysisResult from '../components/ResumeAnalysisResult.vue'
import ResumeDiagnosisContextCard from '../components/ResumeDiagnosisContextCard.vue'

const resumeStore = useResumeStore()
const jobsStore = useJobsStore()
const toast = useToast()
const router = useRouter()

const mode = ref('upload')
const jdContent = ref('')
const resumeText = ref('')
const selectedFile = ref(null)
const selectedFileUrl = ref('')
const fileInput = ref(null)
const analyzing = ref(false)
const result = ref(null)
const showAnalysisResult = ref(false)
const diagnosisContext = ref(null)

onMounted(() => {
  resumeStore.fetchHistory()
  loadDiagnosisContext()
})

const matchColor = computed(() => {
  if (!result.value) return '#666'
  const s = result.value.match_score
  if (s >= 80) return 'var(--green)'
  if (s >= 60) return 'var(--amber)'
  return 'var(--red)'
})

const shouldApplyNow = computed(() => {
  if (!result.value) return false
  return result.value.readiness_level === 'ready' || result.value.match_score >= 80
})

const shouldReviseAgain = computed(() => {
  if (!result.value) return false
  return result.value.readiness_level !== 'ready' || result.value.match_score < 80
})

const shouldPrepareInterview = computed(() => {
  if (!result.value) return false
  return result.value.match_score >= 70 && result.value.readiness_level !== 'not_ready'
})

function cleanDisplayText(value) {
  const text = String(value || '')
    .replace(/\n/g, ' ')
    .replace(/\t/g, ' ')
    .replace(/\{\{.*?\}\}/g, '')
    .replace(/^\s*(?:[-*?]+|\d+[.?])\s*/gm, '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!text) return ''
  const questionCount = (text.match(/\?/g) || []).length
  const meaningfulCount = (text.match(/[一-龥A-Za-z0-9]/g) || []).length
  if (questionCount >= 4 && meaningfulCount === 0) return ''
  if (questionCount >= 8 && questionCount / Math.max(text.length, 1) > 0.5) return ''
  return text
}

function cleanDisplayList(items) {
  if (!Array.isArray(items)) return []
  return items
    .map(cleanDisplayText)
    .filter(item => item && !isBrokenPlaceholder(item))
}

const jdRequirements = computed(() => cleanDisplayList(result.value?.jd_requirements))
const matchedEvidence = computed(() => cleanDisplayList(result.value?.matched_evidence))
const rewriteSuggestions = computed(() => cleanDisplayList(result.value?.rewrite_templates))
const refactoredResumeText = computed(() => cleanDisplayText(result.value?.refactored_resume))
const cleanedKeywords = computed(() => {
  return (result.value?.keywords || [])
    .map(item => ({ ...item, word: cleanDisplayText(item.word), reason: cleanDisplayText(item.reason) }))
    .filter(item => item.word)
})

const abilityGaps = computed(() => {
  if (!result.value) return []
  const missing = cleanDisplayList(result.value.missing_requirements)
  if (missing.length) return missing
  return cleanedKeywords.value
    .filter(item => item.match !== true && item.match !== 'true')
    .map(item => item.reason || `${item.word} 还缺少对应证据`)
    .slice(0, 5)
})

function loadDiagnosisContext() {
  try {
    const raw = sessionStorage.getItem('offer_compass_resume_diagnosis_context')
    if (!raw) return
    const parsed = JSON.parse(raw)
    diagnosisContext.value = parsed
    const jd = parsed.latestInterviewContext?.jd_content || parsed.latestInterviewContext?.requirements || parsed.latestInterviewReview?.jd_content || ''
    if (jd && !jdContent.value.trim()) {
      jdContent.value = jd
    }
    const resume = parsed.latestInterviewContext?.resume_content || parsed.latestInterviewReview?.resume_context_summary || ''
    if (resume && !resumeText.value.trim()) {
      resumeText.value = resume
      mode.value = 'paste'
    }
  } catch {
    diagnosisContext.value = null
  }
}

function clearDiagnosisContext() {
  diagnosisContext.value = null
  sessionStorage.removeItem('offer_compass_resume_diagnosis_context')
}
function setSelectedFile(file) {
  if (selectedFileUrl.value) URL.revokeObjectURL(selectedFileUrl.value)
  selectedFile.value = file || null
  selectedFileUrl.value = file ? URL.createObjectURL(file) : ''
}

function handleFileSelect(e) { setSelectedFile(e.target.files[0] || null) }

function handleDrop(e) {
  setSelectedFile(e.dataTransfer.files[0] || null)
  if (fileInput.value) fileInput.value.value = ''
}

function removeSelectedFile() {
  setSelectedFile(null)
  if (fileInput.value) fileInput.value.value = ''
}

function openSelectedFile() {
  if (!selectedFile.value || !selectedFileUrl.value) return
  const fileName = selectedFile.value.name.toLowerCase()
  if (!fileName.endsWith('.pdf')) {
    toast.show('暂时只支持预览 PDF，Word 文件请下载或转为 PDF 后查看')
    return
  }
  window.open(selectedFileUrl.value, '_blank', 'noopener,noreferrer')
}

async function analyze() {
  if (!jdContent.value.trim()) { toast.show('请先填写 JD'); return }
  if (!selectedFile.value && !resumeText.value.trim()) { toast.show('请上传或粘贴简历内容'); return }
  analyzing.value = true
  result.value = null
  showAnalysisResult.value = false
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
    showAnalysisResult.value = true
    window.scrollTo?.({ top: 0, behavior: 'smooth' })
    resumeStore.fetchHistory()
  } catch (e) {
    toast.show('分析失败：' + (e.response?.data?.detail || e.message || '请稍后重试'))
  } finally {
    analyzing.value = false
  }
}

function extractJobTitleFromJd() {
  const firstMeaningfulLine = jdContent.value
    .split('\n')
    .map(line => line.trim())
    .find(line => line && !isBrokenPlaceholder(line.replace(/[:?：？]$/, '')))
  return cleanDisplayText(firstMeaningfulLine || result.value?.job_title || '目标岗位').slice(0, 60)
}

function saveCurrentJobVersion() {
  if (!result.value) return null
  const version = resumeStore.saveJobVersion({ jdContent: jdContent.value, resumeContent: resumeText.value || refactoredResumeText.value || '', result: result.value })
  toast.show('已保存为本岗位简历版本')
  return version
}

function saveAndTrackCurrentJob() {
  if (!result.value) return
  const version = saveCurrentJobVersion()
  const jobTitle = version?.jobTitle || extractJobTitleFromJd()
  const recordId = version?.id || `resume-jd-${Date.now()}`
  const virtualJob = {
    id: recordId,
    jobId: recordId,
    resumeVersionId: version?.id || '',
    interviewId: '',
    reviewId: '',
    company: '用户自定义 JD',
    title: jobTitle,
    salary: '待确认',
    date: '',
    deadline: '',
    category: inferJobTypeFromResumeFlow(),
    url: '',
    source: 'resume_analysis',
    status: '待投递',
    capital: '外部岗位/JD',
    education: '待确认',
    requirements: cleanDisplayText(jdContent.value).slice(0, 600),
    resumeContent: resumeText.value || refactoredResumeText.value || '',
    analysisResult: result.value,
    nextAction: shouldApplyNow.value ? '确认投递渠道并投递' : '先按改写建议补齐简历证据'
  }
  jobsStore.addApplicationRecord(virtualJob)
  toast.show('已加入投递跟进表，并绑定当前简历版本')
}

function backToAnalysisInput() {
  showAnalysisResult.value = false
  window.scrollTo?.({ top: 0, behavior: 'smooth' })
}

function reanalyzeCurrentVersion() { analyze() }

async function copyText(text) {
  if (!text) return false
  try {
    if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true }
  } catch {}
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  textarea.style.top = '0'
  document.body.appendChild(textarea)
  textarea.focus(); textarea.select()
  try { return document.execCommand('copy') } catch { return false } finally { document.body.removeChild(textarea) }
}

function inferJobTypeFromResumeFlow() {
  const text = `${jdContent.value}
${resumeText.value}
${refactoredResumeText.value || ''}`
  const rules = [
    ['ai', ['AI', 'Coze', 'OpenClaw', 'Trae', 'RAG', '大模型', '智能体', '提示词']],
    ['pm', ['产品', '运营', 'PRD', 'MVP', '用户调研', '需求分析', '竞品分析', '项目管理']],
    ['robot', ['机器人', 'ROS', 'SLAM', 'OpenCV', '视觉']],
    ['material', ['材料', '化工', '实验', '研发']],
    ['lowAltitude', ['低空', '无人机', 'eVTOL', '航空']]
  ]
  const scored = rules.map(([type, terms]) => [type, terms.filter(term => text.includes(term)).length])
  scored.sort((a, b) => b[1] - a[1])
  return scored[0]?.[1] > 0 ? scored[0][0] : 'pm'
}

function startInterviewFromCurrentResult() {
  if (!result.value) {
    toast.show('请先完成简历分析')
    return
  }
  const context = {
    source: 'resume_analysis',
    job_type: inferJobTypeFromResumeFlow(),
    jd_content: jdContent.value,
    resume_content: resumeText.value || refactoredResumeText.value || '',
    analysis_result: result.value
  }
  sessionStorage.setItem('resume_interview_context', JSON.stringify(context))
  router.push('/interview?from=resume')
}

async function copyResult() {
  const text = refactoredResumeText.value || ''
  const ok = await copyText(text)
  toast.show(ok ? '改写建议已复制' : '复制失败，请长按或手动选中文本复制')
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
  let parsed = []
  if (Array.isArray(keywords)) {
    parsed = keywords
  } else {
    try { parsed = JSON.parse(keywords) } catch { parsed = [] }
  }
  return parsed.map(item => ({ ...item, word: cleanDisplayText(item.word), reason: cleanDisplayText(item.reason) })).filter(item => item.word)
})

function splitDetailText(value) {
  return String(value || '')
    .replace(/\\n/g, '\n')
    .split('\n')
    .map(cleanDisplayText)
    .filter(Boolean)
}

const detailJdRequirements = computed(() => {
  const structured = cleanDisplayList(resumeStore.historyDetail?.jd_requirements)
  if (structured.length) return structured
  return detailKeywords.value
    .slice(0, 6)
    .map(item => `${item.word}?${item.reason || '请补充和该要求相关的项目证据'}`)
})

const detailMatchedEvidence = computed(() => {
  const structured = cleanDisplayList(resumeStore.historyDetail?.matched_evidence)
  if (structured.length) return structured
  return detailKeywords.value
    .filter(item => item.match === true || item.match === 'true')
    .map(item => item.reason || `简历已体现 ${item.word} 相关证据`)
    .slice(0, 6)
})

const detailRewriteSuggestions = computed(() => {
  const structured = cleanDisplayList(resumeStore.historyDetail?.rewrite_templates)
  if (structured.length) return structured
  return splitDetailText(resumeStore.historyDetail?.reconstructed_resume).slice(0, 5)
})

const detailRefactoredResumeText = computed(() => cleanDisplayText(resumeStore.historyDetail?.reconstructed_resume))
const detailReadinessLevel = computed(() => resumeStore.historyDetail?.readiness_level || '')
const detailReadinessLabel = computed(() => cleanDisplayText(resumeStore.historyDetail?.readiness_label) || ((resumeStore.historyDetail?.match_score || 0) >= 80 ? '建议投递' : '建议修改后投递'))
const detailReadinessReason = computed(() => cleanDisplayText(resumeStore.historyDetail?.readiness_reason) || ((resumeStore.historyDetail?.match_score || 0) >= 80 ? '当前匹配度较高，可以进入投递前检查和面试准备。' : '当前匹配度还不够稳定，建议先补齐关键证据后再投递。'))
const detailShouldApplyNow = computed(() => detailReadinessLevel.value === 'ready' || (resumeStore.historyDetail?.match_score || 0) >= 80)
const detailShouldReviseAgain = computed(() => detailReadinessLevel.value !== 'ready' || (resumeStore.historyDetail?.match_score || 0) < 80)
const detailShouldPrepareInterview = computed(() => (resumeStore.historyDetail?.match_score || 0) >= 70 && detailReadinessLevel.value !== 'not_ready')
const detailAbilityGaps = computed(() => {
  const missing = cleanDisplayList(resumeStore.historyDetail?.missing_requirements)
  if (missing.length) return missing
  return detailKeywords.value
    .filter(item => item.match !== true && item.match !== 'true')
    .map(item => item.reason || `${item.word} 还缺少对应证据`)
    .slice(0, 5)
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
.selected-file-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 10px;
}
.preview-file-btn {
  border: 1px solid rgba(37, 99, 235, 0.28);
  border-radius: 999px;
  background: #fff;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
}
.preview-file-btn:active {
  transform: scale(0.98);
}
.remove-file-btn {
  border: 1px solid rgba(239, 68, 68, 0.28);
  border-radius: 999px;
  background: #fff;
  color: var(--red);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
}
.remove-file-btn:active {
  transform: scale(0.98);
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
.readiness-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  margin: 16px 0;
  padding: 14px;
}
.readiness-header {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.readiness-pill {
  border-radius: 999px;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  padding: 4px 10px;
}
.readiness-card p {
  color: var(--medium);
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}
.readiness-ready .readiness-pill {
  background: var(--green);
}
.readiness-revise_first .readiness-pill {
  background: var(--amber);
}
.readiness-not_ready .readiness-pill {
  background: var(--red);
}
.analysis-block {
  background: rgba(15, 23, 42, 0.03);
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 14px;
}
.analysis-block h3 {
  font-size: 14px;
  font-weight: 800;
  margin: 0 0 10px;
}
.analysis-block ul {
  margin: 0;
  padding-left: 18px;
}
.analysis-block li {
  color: var(--dark);
  font-size: 13px;
  line-height: 1.7;
}
.rewrite-template {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--dark);
  font-size: 13px;
  line-height: 1.7;
  margin-top: 8px;
  padding: 10px;
}

.next-action-card {
  margin: 14px 0 16px;
  padding: 14px;
  border: 1px solid #e5edf8;
  border-radius: 14px;
  background: #f8fbff;
}

.next-action-card h3 {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 800;
}

.next-action-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.next-action {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  text-align: left;
}

.next-action strong {
  display: block;
  color: var(--dark);
  font-size: 13px;
}

.next-action span {
  display: block;
  margin-top: 3px;
  color: var(--medium);
  font-size: 12px;
  line-height: 1.45;
}

.next-action.active {
  border-color: rgba(37, 99, 235, .35);
  background: var(--blue-light);
}

.compact-match-score {
  margin-top: 14px;
}

.gap-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 13px;
  line-height: 1.55;
  margin-bottom: 8px;
}

.result-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 12px;
}

.result-actions .btn {
  margin-top: 0 !important;
}

.insight-item {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  margin-bottom: 8px;
}

.requirement-item {
  background: #eff6ff;
  color: #1d4ed8;
}

.evidence-item {
  background: #ecfdf5;
  color: #047857;
}

.analysis-result-page {
  border: 1px solid rgba(37, 99, 235, .16);
  box-shadow: 0 18px 42px rgba(37, 99, 235, .08);
}
.result-page-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}
.back-analysis-btn {
  flex-shrink: 0;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #fff;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 800;
  padding: 9px 12px;
}
.result-page-eyebrow {
  color: var(--blue);
  font-size: 12px;
  font-weight: 900;
  margin: 0 0 4px;
}
.result-page-head h2 {
  color: var(--dark);
  font-size: 20px;
  line-height: 1.3;
  margin: 0;
}
@media (max-width: 520px) {
  .result-page-head {
    flex-direction: column;
  }
}



</style>





























<template>
  <div class="page active">
    <div v-if="!interviewStore.questions.length" class="interview-start">
      <h2>🎯 面试模拟</h2>
      <p>选择您的目标岗位，开始AI面试练习</p>
      <div v-if="interviewStore.isStarting" class="starting-hint">
        <span class="loading-dots"><span></span><span></span><span></span></span>
        正在准备高参考价值题组
      </div>
      <div class="job-grid">
        <div class="job-card" @click="startInterview('robot')">
          <div class="jc-icon">🤖</div>
          <div class="jc-name">机器人工程师</div>
        </div>
        <div class="job-card" @click="startInterview('ai')">
          <div class="jc-icon">🧠</div>
          <div class="jc-name">AI算法工程师</div>
        </div>
        <div class="job-card" @click="startInterview('lowAltitude')">
          <div class="jc-icon">🛸</div>
          <div class="jc-name">低空经济运营</div>
        </div>
        <div class="job-card" @click="startInterview('material')">
          <div class="jc-icon">🔬</div>
          <div class="jc-name">新材料研发</div>
        </div>
        <div class="job-card" @click="startInterview('pm')">
          <div class="jc-icon">💼</div>
          <div class="jc-name">产品经理</div>
        </div>
      </div>

      <!-- 历史记录 -->
      <div v-if="interviewStore.history.length > 0" class="interview-history-section">
        <h3 class="interview-history-title">📊 面试历史</h3>
        <div class="interview-history-grid">
        <div
          v-for="item in interviewStore.history"
          :key="item.id"
          class="card interview-history-card"
          @click="viewHistory(item)"
        >
          <div class="interview-history-card-inner">
            <div>
              <div class="interview-history-name">{{ interviewStore.jobTypeNames[item.job_type] || item.job_type }}</div>
              <div class="interview-history-time">{{ formatDate(item.created_at) }}</div>
            </div>
            <div class="interview-history-arrow">›</div>
          </div>
        </div>
          </div>
      </div>
    </div>

    <div v-else-if="interviewStore.isCompleted" class="report-card interview-summary">
      <div class="summary-kicker">Interview Review</div>
      <h2 class="summary-title">面试总结</h2>
      <div class="summary-job">{{ interviewStore.jobTypeNames[interviewStore.jobType] || '目标岗位' }}</div>

      <div class="summary-advice-card">
        <div class="summary-section-head">
          <div>
            <h3>具体优化建议</h3>
            <p>按岗位能力、回答结构和证据缺口逐条调整</p>
          </div>
        </div>
        <div class="advice-list">
          <div
            v-for="(item, index) in reportAdviceItems"
            :key="index"
            class="advice-item"
          >
            <div class="advice-index">{{ index === 0 ? '总' : index }}</div>
            <div>{{ item }}</div>
          </div>
        </div>
      </div>
      <div style="margin-bottom:20px">
        <h4 class="summary-detail-title">面试详情</h4>
        <div class="report-item" v-for="(detail, index) in interviewStore.report.details" :key="index">
          <div class="ri-q">{{ index + 1 }}. {{ detail.question }}</div>
          <div class="ri-a">{{ detail.answer || '未作答' }}</div>
          <button
            class="qa-advice-toggle"
            type="button"
            @click="toggleReportAnalysis(index)"
          >
            {{ expandedReportAnalysisIndexes.has(index) ? '收起问题分析' : '查看问题分析' }}
          </button>
          <div v-if="expandedReportAnalysisIndexes.has(index)" class="qa-advice-panel">
            <div v-if="!detail.feedback" class="qa-advice-empty">
              这道题暂无可展开的问题分析。后端返回完整单题反馈后，这里会展示回答亮点、提升方向和行动建议。
            </div>
            <template v-else>
              <div
                v-for="(section, sectionIndex) in feedbackSections(detail.feedback)"
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
                <p>{{ detail.feedback.suggestion || detail.feedback.summary || '建议围绕问题补充具体场景、个人动作、量化结果和下一步修改方案。' }}</p>
              </div>
            </template>
          </div>
        </div>
      </div>
      <button class="btn btn-primary btn-block" @click="resetInterview">
        🔄 重新开始
      </button>
    </div>

    <div v-else>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <div>
          <h3 style="font-size:15px;font-weight:700">{{ interviewStore.jobTypeNames[interviewStore.jobType] }}</h3>
          <p style="font-size:12px;color:var(--medium)">第 {{ interviewStore.currentQuestionIndex + 1 }} / 5 轮动态追问</p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="interviewStore.reset()">退出</button>
      </div>
      <div class="progress-bar">
        <div class="progress-bar-fill" :style="{ width: (interviewStore.currentQuestionIndex / 5 * 100) + '%' }"></div>
      </div>

      <div class="chat-area">
        <div ref="chatMessagesRef" class="chat-messages">
          <template v-for="(turn, index) in answeredTurns" :key="index">
            <div class="chat-bubble chat-ai">
              {{ turn.question }}
            </div>
            <div class="chat-bubble chat-user">
              {{ turn.answer }}
            </div>
            <div v-if="turn.feedback" class="micro-feedback">
              <div class="mf-item" v-for="(dim, idx) in turn.feedback.dimensions" :key="idx">
                <div class="mf-title">
                  {{ normalizeFeedbackTitle(dim.label) }}
                </div>
                <ul class="mf-list">
                  <li v-for="(point, pointIndex) in splitFeedbackComment(dim.comment)" :key="pointIndex">
                    {{ point }}
                  </li>
                </ul>
              </div>
              <div class="mf-summary">
                <strong>改进建议</strong>
                <p>{{ turn.feedback.suggestion }}</p>
              </div>
            </div>
          </template>

          <div v-if="currentQuestion && !interviewStore.isAnswering" class="chat-bubble chat-ai current-question">
            {{ currentQuestion }}
          </div>

          <div v-if="interviewStore.isAnswering" class="chat-bubble chat-ai">
            <span class="loading-dots">
              <span></span><span></span><span></span>
            </span>
          </div>
        </div>

        <div v-if="interviewStore.answerError" class="interview-error">
          {{ interviewStore.answerError }}
        </div>

        <div class="chat-input-area">
          <textarea
            v-model="answerText"
            placeholder="输入您的回答..."
            rows="2"
            @keydown.enter.exact.prevent="submitAnswer"
          ></textarea>
          <button
            class="btn btn-primary"
            @click="submitAnswer"
            :disabled="!answerText.trim() || interviewStore.isAnswering"
          >
            发送
          </button>
        </div>
      </div>
    </div>

    <div
      class="modal-overlay"
      :class="{ show: interviewStore.historyDetail || interviewStore.isLoadingDetail }"
      @click.self="closeHistoryDetail"
    >
      <div class="modal-content history-detail-modal">
        <div class="modal-handle"></div>
        <button class="modal-close" @click="closeHistoryDetail">×</button>

        <div v-if="interviewStore.isLoadingDetail" class="empty-state">
          <div class="es-icon">...</div>
          <p>正在加载面试详情</p>
        </div>

        <div v-else-if="interviewStore.historyDetail">
          <h3 class="detail-title">{{ interviewStore.jobTypeNames[interviewStore.historyDetail.job_type] || interviewStore.historyDetail.job_type || '面试详情' }}</h3>
          <div class="detail-subtitle">{{ formatDate(interviewStore.historyDetail.created_at) }}</div>

          <h4 class="detail-section-title">综合建议</h4>
          <div class="result-area">{{ interviewStore.historyDetail.advice || '暂无建议' }}</div>

          <h4 class="detail-section-title">问答详情</h4>
          <div
            v-for="(detail, index) in historyDetails"
            :key="index"
            class="report-item"
          >
            <div class="ri-q">{{ index + 1 }}. {{ detail.question }}</div>
            <div class="ri-a">{{ detail.answer || '未作答' }}</div>
            <button
              class="qa-advice-toggle"
              type="button"
              @click="toggleHistoryAdvice(index)"
            >
              {{ expandedHistoryAdviceIndexes.has(index) ? '收起修改建议' : '查看修改建议' }}
            </button>
            <div v-if="expandedHistoryAdviceIndexes.has(index)" class="qa-advice-panel">
              <div v-if="!detail.feedback" class="qa-advice-empty">
                这条历史记录暂无当时保存的单题修改建议。完成新的模拟面试后，这里会展示完整修改建议。
              </div>
              <template v-else>
                <div
                  v-for="(section, sectionIndex) in feedbackSections(detail.feedback)"
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
                  <p>{{ detail.feedback.suggestion || detail.feedback.summary || '建议围绕问题补充具体场景、个人动作、量化结果和下一步修改方案。' }}</p>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useInterviewStore } from '../stores/interview'

const interviewStore = useInterviewStore()
const answerText = ref('')
const chatMessagesRef = ref(null)
const expandedReportAnalysisIndexes = ref(new Set())
const expandedHistoryAdviceIndexes = ref(new Set())

onMounted(() => {
  interviewStore.fetchHistory()
})

const answeredTurns = computed(() => {
  return interviewStore.answers.map((answer, index) => ({
    question: interviewStore.questions[index] || '',
    answer,
    feedback: interviewStore.feedbacks[index] || null
  }))
})

const currentQuestion = computed(() => {
  return interviewStore.questions[interviewStore.currentQuestionIndex] || ''
})

const reportAdviceItems = computed(() => {
  const advice = interviewStore.report?.advice || ''
  return advice
    .split(/\n+/)
    .map(item => item.replace(/^建议\d+[:：]\s*/, '').replace(/^总结[:：]\s*/, '').trim())
    .filter(item => !isInternalReviewNote(item))
    .filter(Boolean)
})

function scrollChatToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

watch(
  () => [
    interviewStore.questions.length,
    interviewStore.answers.length,
    interviewStore.feedbacks.length,
    interviewStore.isAnswering
  ],
  scrollChatToBottom
)

const historyDetails = computed(() => {
  const detail = interviewStore.historyDetail
  if (!detail) return []
  if (Array.isArray(detail.details)) return detail.details
  const questions = Array.isArray(detail.questions) ? detail.questions : []
  const answers = Array.isArray(detail.answers) ? detail.answers : []
  const scores = Array.isArray(detail.scores) ? detail.scores : []
  const feedbacks = Array.isArray(detail.feedbacks) ? detail.feedbacks : []
  return questions.map((question, index) => ({
    question,
    answer: answers[index] || '',
    score: scores[index] || 0,
    feedback: feedbacks[index] || null
  }))
})

function feedbackSections(feedback) {
  if (!feedback) return []

  const dimensionSections = Array.isArray(feedback.dimensions)
    ? feedback.dimensions
        .map(item => ({
          title: normalizeFeedbackTitle(item.label),
          points: splitFeedbackComment(item.comment)
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
      title: '提升方向',
      points: Array.isArray(feedback.missed_points) && feedback.missed_points.length
        ? feedback.missed_points
        : ['建议补充更具体的岗位证据。']
    },
    {
      title: '行动建议',
      points: Array.isArray(feedback.rewrite_advice) && feedback.rewrite_advice.length
        ? feedback.rewrite_advice
        : ['建议围绕问题补充具体场景、个人动作、量化结果和下一步修改方案。']
    }
  ]
}

function normalizeFeedbackTitle(label) {
  if (label === '提升机会') return '提升方向'
  return label || '分析项'
}

function feedbackList(feedback, type) {
  if (!feedback) return []
  if (type === 'hit') {
    return Array.isArray(feedback.hit_points) && feedback.hit_points.length
      ? feedback.hit_points
      : feedback.dimensions?.filter(item => item.label?.includes('相关') || item.label?.includes('匹配')).map(item => item.comment).filter(Boolean).slice(0, 2) || ['暂未识别到明确切中点。']
  }
  if (type === 'missed') {
    return Array.isArray(feedback.missed_points) && feedback.missed_points.length
      ? feedback.missed_points
      : feedback.dimensions?.map(item => item.comment).filter(Boolean).slice(0, 3) || ['还需要补充更具体的岗位证据。']
  }
  return Array.isArray(feedback.rewrite_advice) && feedback.rewrite_advice.length
    ? feedback.rewrite_advice
    : [feedback.suggestion || '建议补充具体项目、个人动作、结果和下一步修改方案。']
}

function splitFeedbackComment(comment) {
  if (!comment) return []
  return String(comment)
    .split(/[；;。]\s*/)
    .map(item => item.trim())
    .filter(Boolean)
}

function isInternalReviewNote(text) {
  return /不展示分数|反馈方式|定性反馈|目标岗位是/.test(text)
}

async function startInterview(jobType) {
  if (interviewStore.isStarting) return
  await interviewStore.start(jobType)
  scrollChatToBottom()
}

async function submitAnswer() {
  if (!answerText.value.trim()) return
  const answer = answerText.value
  answerText.value = ''
  
  try {
    await interviewStore.answer(answer)
  } catch {
    answerText.value = answer
    scrollChatToBottom()
    return
  }
  
  if (interviewStore.currentQuestionIndex >= 5) {
    await interviewStore.complete()
  } else {
    scrollChatToBottom()
  }
}

function resetInterview() {
  expandedReportAnalysisIndexes.value = new Set()
  interviewStore.reset()
  interviewStore.fetchHistory()
}

function toggleReportAnalysis(index) {
  const next = new Set(expandedReportAnalysisIndexes.value)
  if (next.has(index)) {
    next.delete(index)
  } else {
    next.add(index)
  }
  expandedReportAnalysisIndexes.value = next
}

async function viewHistory(item) {
  try {
    expandedHistoryAdviceIndexes.value = new Set()
    await interviewStore.fetchHistoryDetail(item.id)
  } catch (e) {
    alert('加载面试详情失败: ' + (e.response?.data?.detail || e.message || '请稍后重试'))
  }
}

function closeHistoryDetail() {
  expandedHistoryAdviceIndexes.value = new Set()
  interviewStore.clearHistoryDetail()
}

function toggleHistoryAdvice(index) {
  const next = new Set(expandedHistoryAdviceIndexes.value)
  if (next.has(index)) {
    next.delete(index)
  } else {
    next.add(index)
  }
  expandedHistoryAdviceIndexes.value = next
}

function displayScore(value) {
  const score = Number(value || 0)
  return Number.isFinite(score) ? score.toFixed(1) : '0.0'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.interview-history-section {
  margin-top: 28px;
  width: 100%;
}
.interview-history-title {
  font-size: 17px;
  font-weight: 800;
  margin: 0 0 14px;
  text-align: left;
}
.interview-history-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  width: 100%;
}
.interview-history-card {
  cursor: pointer;
  min-height: 92px;
  padding: 18px 20px;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.interview-history-card:hover {
  border-color: rgba(67, 97, 238, .35);
  box-shadow: 0 16px 34px rgba(67, 97, 238, .12);
  transform: translateY(-2px);
}
.interview-history-card-inner {
  align-items: center;
  display: flex;
  gap: 16px;
  height: 100%;
  justify-content: space-between;
}
.interview-history-name {
  color: var(--dark);
  font-size: 16px;
  font-weight: 800;
  line-height: 1.35;
}
.interview-history-time {
  color: var(--medium);
  font-size: 13px;
  margin-top: 6px;
}
.interview-history-arrow {
  color: var(--medium);
  flex: 0 0 auto;
  font-size: 28px;
  line-height: 1;
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
.score-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 16px;
}
.score-summary > div {
  background: var(--blue-light);
  border-radius: var(--radius-sm);
  padding: 14px;
  text-align: center;
}
.score-summary-num {
  font-size: 30px;
  font-weight: 800;
  color: var(--blue);
  font-family: var(--font-display);
}
.score-summary-num.small {
  color: var(--purple);
}
.score-summary-label {
  font-size: 12px;
  color: var(--medium);
  margin-top: 2px;
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
.qa-advice-block + .qa-advice-block,
.qa-advice-summary {
  border-top: 1px solid #e2e8f0;
  margin-top: 10px;
  padding-top: 10px;
}
.qa-advice-block strong,
.qa-advice-summary strong {
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
.qa-advice-summary p,
.qa-advice-empty {
  color: var(--medium);
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
}
.micro-feedback {
  margin: 12px 0 16px;
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(67, 97, 238, .08), rgba(114, 9, 183, .08));
}
.interview-error {
  margin: 0 0 12px;
  padding: 10px 12px;
  border: 1px solid #fecaca;
  border-radius: 12px;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 13px;
  line-height: 1.5;
}
.mf-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(15, 23, 42, .08);
}
.mf-item:first-child {
  padding-top: 0;
}
.mf-title {
  display: block;
  margin-bottom: 8px;
  color: var(--dark);
  font-size: 15px;
  font-weight: 800;
  line-height: 1.4;
  letter-spacing: 0;
}
.mf-list {
  display: grid;
  gap: 6px;
  margin: 0;
  padding-left: 18px;
  color: var(--medium);
  font-size: 14px;
  line-height: 1.65;
}
.mf-list li::marker {
  color: var(--blue);
}
.mf-summary {
  padding-top: 12px;
  color: var(--dark);
  font-size: 14px;
  line-height: 1.65;
}
.mf-summary strong {
  display: block;
  margin-bottom: 4px;
}
.mf-summary p {
  margin: 0;
  color: var(--medium);
}
.qf-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--dark);
  margin-bottom: 6px;
}
.qf-list {
  margin: 0;
  padding-left: 18px;
  color: var(--medium);
  font-size: 12px;
  line-height: 1.7;
}
.qf-summary {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0,0,0,.1);
  color: var(--dark);
  font-size: 13px;
  line-height: 1.6;
}
.starting-hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: -8px 0 16px;
  padding: 8px 12px;
  border-radius: 999px;
  background: var(--blue-light);
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
}
.interview-summary {
  text-align: left;
  padding-top: 28px;
}
.summary-kicker {
  width: max-content;
  margin: 0 auto 8px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(67, 97, 238, .08);
  color: var(--blue);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}
.summary-title {
  margin: 0;
  text-align: center;
  font-size: 34px;
  line-height: 1.15;
  font-weight: 900;
  color: var(--dark);
}
.summary-job {
  margin: 8px 0 20px;
  text-align: center;
  font-size: 14px;
  color: var(--medium);
}
.summary-advice-card {
  margin-bottom: 22px;
  padding: 18px 0;
  border: 1px solid rgba(67, 97, 238, .12);
  border-radius: var(--radius);
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, .06);
}
.summary-section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  padding: 0 18px;
}
.summary-section-head h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 850;
  color: var(--dark);
}
.summary-section-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--medium);
}
.advice-list {
  display: grid;
  gap: 10px;
}
.advice-item {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 0;
  background: var(--blue-light);
  color: var(--dark);
  font-size: 14px;
  line-height: 1.65;
}
.advice-item + .advice-item {
  border-top: 1px solid rgba(67, 97, 238, .1);
}
.advice-index {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #fff;
  color: var(--blue);
  font-size: 13px;
  font-weight: 900;
}
.summary-detail-title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 850;
  color: var(--dark);
}
@media (max-width: 640px) {
  .interview-history-grid {
    grid-template-columns: 1fr;
  }
  .interview-history-card {
    min-height: 86px;
  }
  .summary-section-head {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

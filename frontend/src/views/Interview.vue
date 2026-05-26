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
      <div v-if="interviewStore.history.length > 0" style="margin-top:24px">
        <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">📊 面试历史</h3>
        <div
          v-for="item in interviewStore.history"
          :key="item.id"
          class="card"
          style="margin-bottom:10px;padding:14px;cursor:pointer"
          @click="viewHistory(item)"
        >
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:600;font-size:14px">{{ interviewStore.jobTypeNames[item.job_type] || item.job_type }}</div>
              <div style="font-size:12px;color:var(--medium);margin-top:2px">{{ formatDate(item.created_at) }}</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:20px;font-weight:800" :style="{ color: item.avg_score >= 7 ? 'var(--green)' : 'var(--amber)' }">
                {{ displayScore(item.avg_score) }}
              </div>
              <div style="font-size:11px;color:var(--medium)">平均分</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="interviewStore.isCompleted" class="report-card interview-summary">
      <div class="summary-kicker">Interview Review</div>
      <h2 class="summary-title">面试总结</h2>
      <div class="summary-job">{{ interviewStore.jobTypeNames[interviewStore.jobType] || '目标岗位' }}</div>

      <div class="summary-score-panel">
        <div>
          <div class="report-total">{{ Math.round(interviewStore.report.avg_score * 10) / 10 }}</div>
          <div class="report-total-label">平均分（满分10分）</div>
        </div>
        <div class="summary-score-copy">
          <strong>{{ summaryLevel }}</strong>
          <span>{{ summaryOneLine }}</span>
        </div>
      </div>

      <div class="summary-advice-card">
        <div class="summary-section-head">
          <div>
            <h3>具体优化建议</h3>
            <p>按岗位能力、回答结构和低分题逐条调整</p>
          </div>
          <button class="btn btn-secondary btn-sm" @click="copyInterviewAdvice">一键复制</button>
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
          <div class="ri-score">得分：{{ detail.score }}/10</div>
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
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
                  <span style="font-weight:600;font-size:13px">{{ dim.label }}</span>
                  <span style="font-weight:800;font-size:14px" :style="{ color: dim.score >= 7 ? 'var(--green)' : dim.score >= 5 ? 'var(--amber)' : 'var(--red)' }">{{ dim.score }}/10</span>
                </div>
                <div style="font-size:12px;color:var(--medium);line-height:1.5">{{ dim.comment }}</div>
              </div>
              <div style="margin-top:10px;padding-top:10px;border-top:1px dashed rgba(0,0,0,.1)">
                💡 <strong>改进建议：</strong>{{ turn.feedback.suggestion }}
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

          <div class="score-summary">
            <div>
              <div class="score-summary-num">{{ displayScore(interviewStore.historyDetail.avg_score) }}</div>
              <div class="score-summary-label">平均分</div>
            </div>
            <div>
              <div class="score-summary-num small">{{ interviewStore.historyDetail.total_score || 0 }}</div>
              <div class="score-summary-label">总分</div>
            </div>
          </div>

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
            <div class="ri-score">得分：{{ detail.score || 0 }}/10</div>
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
    .filter(Boolean)
})

const summaryLevel = computed(() => {
  const score = Number(interviewStore.report?.avg_score || 0)
  if (score >= 8) return '竞争力较强'
  if (score >= 6) return '具备基础竞争力'
  return '需要重点补强'
})

const summaryOneLine = computed(() => {
  return reportAdviceItems.value[0] || '建议结合岗位要求继续完善项目案例、量化指标和表达结构。'
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
  return questions.map((question, index) => ({
    question,
    answer: answers[index] || '',
    score: scores[index] || 0
  }))
})

async function startInterview(jobType) {
  if (interviewStore.isStarting) return
  await interviewStore.start(jobType)
  scrollChatToBottom()
}

async function submitAnswer() {
  if (!answerText.value.trim()) return
  const answer = answerText.value
  answerText.value = ''
  
  await interviewStore.answer(answer)
  
  if (interviewStore.currentQuestionIndex >= 5) {
    await interviewStore.complete()
  } else {
    scrollChatToBottom()
  }
}

async function copyInterviewAdvice() {
  const text = [
    '面试总结',
    `岗位：${interviewStore.jobTypeNames[interviewStore.jobType] || interviewStore.jobType || '目标岗位'}`,
    `平均分：${displayScore(interviewStore.report?.avg_score)}/10`,
    '',
    ...(reportAdviceItems.value.map((item, index) => `${index === 0 ? '总结' : `建议${index}`}：${item}`))
  ].join('\n')

  try {
    await navigator.clipboard.writeText(text)
    alert('已复制面试总结和优化建议')
  } catch {
    alert('复制失败，请手动选择文本复制')
  }
}

function resetInterview() {
  interviewStore.reset()
  interviewStore.fetchHistory()
}

async function viewHistory(item) {
  try {
    await interviewStore.fetchHistoryDetail(item.id)
  } catch (e) {
    alert('加载面试详情失败: ' + (e.response?.data?.detail || e.message || '请稍后重试'))
  }
}

function closeHistoryDetail() {
  interviewStore.clearHistoryDetail()
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
.summary-score-panel {
  display: grid;
  grid-template-columns: minmax(100px, 150px) 1fr;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
  padding: 18px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(67, 97, 238, .08), rgba(76, 201, 240, .08));
}
.summary-score-panel .report-total,
.summary-score-panel .report-total-label {
  text-align: center;
}
.summary-score-copy strong {
  display: block;
  margin-bottom: 6px;
  font-size: 18px;
  color: var(--dark);
}
.summary-score-copy span {
  display: block;
  color: var(--medium);
  font-size: 14px;
  line-height: 1.6;
}
.summary-advice-card {
  margin-bottom: 22px;
  padding: 18px;
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
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--blue-light);
  color: var(--dark);
  font-size: 14px;
  line-height: 1.65;
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
  .summary-score-panel {
    grid-template-columns: 1fr;
  }
  .summary-section-head {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>

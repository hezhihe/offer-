<!--
组件职责：展示当前简历分析结果。
边界：只接收 props、emit 用户动作；不调用接口、不写 store、不写本地缓存、不跳路由。
-->

<template>
  <div class="card analysis-result-page" style="margin-top:20px">
    <div class="result-page-head">
      <button class="back-analysis-btn" type="button" @click="emit('back')">← 返回分析界面</button>
      <div>
        <p class="result-page-eyebrow">AI 分析结果</p>
        <h2>这份简历当前是否适合投递</h2>
      </div>
    </div>

    <div v-if="result.readiness_label" class="readiness-card" :class="`readiness-${result.readiness_level}`">
      <div class="readiness-header">
        <strong>投递准备度</strong>
        <span class="readiness-pill">{{ result.readiness_label }}</span>
      </div>
      <p>{{ readinessReason }}</p>
    </div>

    <div class="next-action-card">
      <h3>下一步行动建议</h3>
      <div class="next-action-grid">
        <button class="next-action" :class="{ active: shouldApplyNow }" type="button">
          <strong>{{ shouldApplyNow ? '建议投递' : '暂不建议直接投递' }}</strong>
          <span>{{ shouldApplyNow ? '这版简历可以进入投递跟进。' : '先补齐关键证据再投，别浪费岗位机会。' }}</span>
        </button>
        <button class="next-action" :class="{ active: shouldReviseAgain }" type="button" @click="emit('reanalyze')">
          <strong>{{ shouldReviseAgain ? '建议再次修改后分析' : '可继续微调' }}</strong>
          <span>用当前 JD 和简历再跑一轮，检查是否进步。</span>
        </button>
        <button class="next-action" :class="{ active: shouldPrepareInterview }" type="button" @click="emit('start-interview')">
          <strong>{{ shouldPrepareInterview ? '建议进入模拟面试' : '面试准备可稍后' }}</strong>
          <span>匹配度达标后，用岗位方向训练回答。</span>
        </button>
      </div>
    </div>

    <div class="match-score compact-match-score">
      <div class="score-circle" :style="{ background: matchColor }">{{ result.match_score }}%</div>
      <div class="score-info">
        <h4>匹配证据</h4>
        <p>与目标岗位的关键词和能力契合度</p>
        <div class="match-bar">
          <div class="match-bar-fill" :style="{ width: result.match_score + '%', background: matchColor }"></div>
        </div>
      </div>
    </div>

    <div v-if="jdRequirements.length" class="analysis-block">
      <h3>JD核心要求</h3>
      <div v-for="item in jdRequirements" :key="item" class="insight-item requirement-item">{{ item }}</div>
    </div>

    <div v-if="matchedEvidence.length" class="analysis-block">
      <h3>简历已有证据</h3>
      <div v-for="item in matchedEvidence" :key="item" class="insight-item evidence-item">{{ item }}</div>
    </div>

    <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">匹配关键词</h3>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">
      <span
        v-for="kw in cleanedKeywords"
        :key="kw.word"
        class="badge"
        :class="isKeywordMatched(kw) ? 'badge-green' : 'badge-amber'"
      >
        {{ isKeywordMatched(kw) ? '✓' : '!' }} {{ kw.word }}
      </span>
    </div>

    <div v-if="abilityGaps.length" class="analysis-block">
      <h3>能力缺口</h3>
      <div v-for="gap in abilityGaps" :key="gap" class="gap-item">{{ gap }}</div>
    </div>

    <div v-if="rewriteSuggestions.length" class="analysis-block">
      <h3>改写建议</h3>
      <div
        v-for="item in rewriteSuggestions"
        :key="item"
        class="rewrite-template"
      >
        {{ item }}
      </div>
    </div>

    <h3 style="font-size:15px;font-weight:700;margin-bottom:12px">可参考表达片段</h3>
    <div class="result-area">{{ refactoredResumeText }}</div>

    <div class="result-actions">
      <button class="btn btn-primary btn-sm btn-block" @click="emit('save-version')">
        保存为本岗位简历版本
      </button>
      <button class="btn btn-secondary btn-sm btn-block" @click="emit('track-job')">
        加入投递跟进
      </button>
      <button class="btn btn-secondary btn-sm btn-block" @click="emit('copy')">
        一键复制
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  result: {
    type: Object,
    required: true
  },
  matchColor: {
    type: String,
    required: true
  },
  readinessReason: {
    type: String,
    default: ''
  },
  shouldApplyNow: {
    type: Boolean,
    default: false
  },
  shouldReviseAgain: {
    type: Boolean,
    default: false
  },
  shouldPrepareInterview: {
    type: Boolean,
    default: false
  },
  jdRequirements: {
    type: Array,
    default: () => []
  },
  matchedEvidence: {
    type: Array,
    default: () => []
  },
  cleanedKeywords: {
    type: Array,
    default: () => []
  },
  abilityGaps: {
    type: Array,
    default: () => []
  },
  rewriteSuggestions: {
    type: Array,
    default: () => []
  },
  refactoredResumeText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['back', 'reanalyze', 'start-interview', 'save-version', 'track-job', 'copy'])

function isKeywordMatched(keyword) {
  return keyword?.match === true || keyword?.match === 'true'
}
</script>

<style scoped>
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
.readiness-ready .readiness-pill { background: var(--green); }
.readiness-revise_first .readiness-pill { background: var(--amber); }
.readiness-not_ready .readiness-pill { background: var(--red); }
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
.compact-match-score { margin-top: 14px; }
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
.gap-item,
.insight-item {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  margin-bottom: 8px;
}
.gap-item {
  background: #fff7ed;
  color: #9a3412;
}
.requirement-item {
  background: #eff6ff;
  color: #1d4ed8;
}
.evidence-item {
  background: #ecfdf5;
  color: #047857;
}
.result-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 12px;
}
.result-actions .btn { margin-top: 0 !important; }
@media (max-width: 520px) {
  .result-page-head { flex-direction: column; }
}
</style>

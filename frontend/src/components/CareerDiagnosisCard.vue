<!--
组件职责：展示求职诊断档案。
边界：只展示短板、线索、行动和统计；不写 sessionStorage，不做路由跳转。
-->

<template>
  <section class="career-assets-card diagnosis-card">
    <div class="career-assets-head">
      <div>
        <p class="career-eyebrow">求职诊断档案</p>
        <h2>下一轮求职该补什么</h2>
      </div>
    </div>

    <div class="career-stats-grid">
      <button class="career-stat" type="button" @click="emit('open-stat', 'resume')">
        <span>简历版本</span>
        <strong>{{ stats.resumeVersions }}</strong>
      </button>
      <button class="career-stat" type="button" @click="emit('open-stat', 'application')">
        <span>投递记录</span>
        <strong>{{ stats.applications }}</strong>
      </button>
      <button class="career-stat" type="button" @click="emit('open-stat', 'interview')">
        <span>面试复盘</span>
        <strong>{{ stats.interviewReviews }}</strong>
      </button>
    </div>

    <div v-if="hasData" class="diagnosis-content">
      <div class="diagnosis-block">
        <div class="diagnosis-label">能力短板</div>
        <div class="diagnosis-tags">
          <span v-for="tag in weaknessTags" :key="tag">{{ tag }}</span>
        </div>
      </div>

      <div class="diagnosis-block">
        <div class="diagnosis-label">简历补强线索</div>
        <ul class="diagnosis-list">
          <li v-for="clue in resumeClues" :key="clue">{{ clue }}</li>
        </ul>
      </div>

      <div class="diagnosis-block">
        <div class="diagnosis-label">下一步行动</div>
        <ul class="diagnosis-list">
          <li v-for="action in nextActions" :key="action">{{ action }}</li>
        </ul>
      </div>
    </div>

    <div v-else class="career-empty">
      还没有形成诊断档案。先完成一次 JD 简历分析，或基于具体 JD 做一轮模拟面试，系统会把短板、补强线索和下一步动作沉淀到这里。
    </div>

    <div class="diagnosis-actions">
      <button type="button" @click="emit('optimize-resume')">继续简历分析</button>
      <button type="button" @click="emit('view-progress')">查看投递进展</button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  stats: {
    type: Object,
    default: () => ({ resumeVersions: 0, applications: 0, interviewReviews: 0 })
  },
  hasData: {
    type: Boolean,
    default: false
  },
  weaknessTags: {
    type: Array,
    default: () => []
  },
  resumeClues: {
    type: Array,
    default: () => []
  },
  nextActions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['open-stat', 'optimize-resume', 'view-progress'])
</script>

<style scoped>
.career-assets-card {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid rgba(37, 99, 235, .14);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(16, 185, 129, .14), transparent 32%),
    linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 16px 38px rgba(37, 99, 235, .08);
}

.career-assets-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.career-eyebrow {
  margin: 0 0 4px;
  color: var(--blue);
  font-size: 12px;
  font-weight: 800;
}

.career-assets-head h2 {
  margin: 0;
  color: var(--dark);
  font-size: 17px;
  line-height: 1.35;
}

.career-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.career-stat {
  width: 100%;
  padding: 10px;
  border: 1px solid #e8eef7;
  border-radius: 14px;
  background: rgba(255,255,255,.86);
  cursor: pointer;
  text-align: left;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}

.career-stat:hover {
  border-color: rgba(37, 99, 235, .35);
  box-shadow: 0 10px 22px rgba(37, 99, 235, .08);
  transform: translateY(-1px);
}

.career-stat span {
  display: block;
  color: var(--medium);
  font-size: 11px;
  font-weight: 700;
}

.career-stat strong {
  display: block;
  margin-top: 4px;
  color: var(--dark);
  font-size: 21px;
  font-weight: 900;
}

.diagnosis-card {
  border-color: rgba(16, 185, 129, .18);
}

.diagnosis-content {
  display: grid;
  gap: 10px;
}

.diagnosis-block {
  padding: 11px;
  border: 1px solid #e8eef7;
  border-radius: 14px;
  background: #fff;
}

.diagnosis-label {
  color: var(--medium);
  font-size: 11px;
  font-weight: 800;
  margin-bottom: 8px;
}

.diagnosis-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.diagnosis-tags span {
  padding: 6px 9px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #047857;
  font-size: 12px;
  font-weight: 800;
}

.diagnosis-list {
  display: grid;
  gap: 7px;
  margin: 0;
  padding-left: 18px;
  color: var(--dark);
  font-size: 13px;
  line-height: 1.55;
}

.diagnosis-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 12px;
}

.diagnosis-actions button {
  min-height: 38px;
  border: 1px solid #dbe3ef;
  border-radius: 12px;
  background: #fff;
  color: var(--blue);
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.career-empty {
  padding: 12px;
  border-radius: 14px;
  background: #fff;
  color: var(--medium);
  font-size: 13px;
  line-height: 1.6;
}
</style>

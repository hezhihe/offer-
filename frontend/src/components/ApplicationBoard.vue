<!--
组件职责：展示投递进展表。
边界：只展示投递记录和阶段；更新阶段、进入模拟面试交给 Calendar.vue 处理。
-->

<template>
  <section class="application-board">
    <div class="board-head">
      <div>
        <p class="board-eyebrow">投递进展表</p>
        <h2>把岗位从“看到”推进到“拿 Offer”</h2>
      </div>
      <span class="board-count">{{ records.length }} 个岗位</span>
    </div>

    <div v-if="records.length" class="stage-grid">
      <div v-for="stage in stages" :key="stage.key" class="stage-card">
        <div class="stage-title">{{ stage.label }}</div>
        <div class="stage-num">{{ countByStage(stage.key) }}</div>
      </div>
    </div>

    <div v-if="records.length" class="application-list">
      <div v-for="record in records.slice(0, 5)" :key="record.id" class="application-item">
        <div class="application-main">
          <strong>{{ record.company }}｜{{ record.title }}</strong>
          <span>{{ record.salary || '薪资待确认' }} / 截止 {{ record.deadline || record.date || '待确认' }}</span>
          <span class="application-next">下一步：{{ record.nextAction || '确认下一步动作' }}</span>
          <span class="application-source">最近更新：{{ formatUpdatedAt(record.updatedAt) }}</span>
        </div>
        <div class="application-actions">
          <select :value="record.stage" @change="emit('update-stage', record, $event.target.value)">
            <option v-for="stage in stages" :key="stage.key" :value="stage.key">{{ stage.label }}</option>
          </select>
          <button class="interview-link-btn" type="button" @click="emit('start-interview', record)">模拟面试</button>
        </div>
      </div>
    </div>

    <div v-else class="board-empty">先从下方岗位详情里点击“加入投递跟进”，这里会自动形成你的求职进度表。</div>
  </section>
</template>

<script setup>
const props = defineProps({
  records: {
    type: Array,
    default: () => []
  },
  stages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update-stage', 'start-interview'])

function countByStage(stage) {
  return props.records.filter(item => item.stage === stage).length
}

function formatUpdatedAt(value) {
  if (!value) return '待确认'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '待确认'
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.application-board {
  margin: 16px 0 18px;
  padding: 16px;
  border: 1px solid rgba(37, 99, 235, .14);
  border-radius: 22px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 18px 42px rgba(37, 99, 235, .08);
}

.board-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.board-eyebrow {
  margin: 0 0 4px;
  color: var(--blue);
  font-size: 12px;
  font-weight: 800;
}

.board-head h2 {
  margin: 0;
  font-size: 17px;
  line-height: 1.35;
}

.board-count {
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--blue-light);
  color: var(--blue);
  font-size: 12px;
  font-weight: 800;
}

.stage-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.stage-card {
  padding: 10px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e8eef7;
}

.stage-title {
  color: var(--medium);
  font-size: 11px;
  font-weight: 700;
}

.stage-num {
  margin-top: 3px;
  color: var(--dark);
  font-size: 20px;
  font-weight: 900;
}

.application-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.application-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px;
  border-radius: 14px;
  background: rgba(255,255,255,.86);
  border: 1px solid #e8eef7;
}

.application-main {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.application-main strong {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.application-main span {
  color: var(--medium);
  font-size: 11px;
}

.application-next {
  color: #1d4ed8 !important;
  font-weight: 700;
}

.application-source {
  color: #64748b !important;
}

.application-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.application-item select {
  min-width: 88px;
  height: 32px;
  border: 1px solid #dbe3ef;
  border-radius: 999px;
  padding: 0 8px;
  background: #fff;
  color: var(--dark);
  font-weight: 700;
}

.interview-link-btn {
  height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.board-empty {
  padding: 12px;
  border-radius: 14px;
  background: #fff;
  color: var(--medium);
  font-size: 13px;
  line-height: 1.55;
}
</style>

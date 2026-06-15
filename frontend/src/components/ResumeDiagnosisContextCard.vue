<!--
组件职责：展示“求职诊断档案”回流到简历分析页的补强线索。
负责：展示能力短板、简历补强线索、下一步动作，以及触发清除事件。
边界：不读取或写入 sessionStorage；不修改 JD/简历输入；不调用接口；不做路由跳转。
-->

<template>
  <div class="diagnosis-resume-card">
    <div class="diagnosis-resume-head">
      <strong>来自求职诊断档案的补强线索</strong>
      <button type="button" @click="$emit('clear')">清除</button>
    </div>
    <p>把这些短板和面试复盘线索补进本轮 JD 简历分析，避免下一次投递继续踩同样的问题。</p>

    <div v-if="diagnosisContext.weaknessTags?.length" class="diagnosis-mini-block">
      <span>能力短板</span>
      <div class="diagnosis-mini-tags">
        <em v-for="tag in diagnosisContext.weaknessTags" :key="tag">{{ tag }}</em>
      </div>
    </div>

    <div v-if="diagnosisContext.resumeRewriteClues?.length" class="diagnosis-mini-block">
      <span>简历补强线索</span>
      <ul>
        <li v-for="clue in diagnosisContext.resumeRewriteClues" :key="clue">{{ clue }}</li>
      </ul>
    </div>

    <div v-if="diagnosisContext.nextActions?.length" class="diagnosis-mini-block">
      <span>下一步动作</span>
      <ul>
        <li v-for="action in diagnosisContext.nextActions" :key="action">{{ action }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
defineProps({
  diagnosisContext: {
    type: Object,
    required: true,
  },
})

defineEmits(['clear'])
</script>

<style scoped>
.diagnosis-resume-card {
  margin-bottom: 16px;
  padding: 14px;
  border: 1px solid rgba(37, 99, 235, .18);
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
  box-shadow: 0 12px 28px rgba(37, 99, 235, .07);
}

.diagnosis-resume-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.diagnosis-resume-head strong {
  color: var(--dark);
  font-size: 15px;
}

.diagnosis-resume-head button {
  border: 0;
  border-radius: 999px;
  background: #eff6ff;
  color: var(--blue);
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  padding: 6px 10px;
}

.diagnosis-resume-card p {
  color: var(--medium);
  font-size: 13px;
  line-height: 1.55;
  margin: 0 0 10px;
}

.diagnosis-mini-block {
  margin-top: 10px;
}

.diagnosis-mini-block span {
  display: block;
  color: var(--dark);
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 6px;
}

.diagnosis-mini-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.diagnosis-mini-tags em {
  border-radius: 999px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
  padding: 5px 9px;
}

.diagnosis-mini-block ul {
  margin: 0;
  padding-left: 18px;
  color: var(--medium);
  font-size: 13px;
  line-height: 1.65;
}
</style>

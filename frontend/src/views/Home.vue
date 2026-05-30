<template>
  <div class="page active">
    <div class="hero-gradient">
      <h1 class="gradient-text">Offer罗盘</h1>
      <p>AI驱动的毕业生求职助手</p>
    </div>

    <div class="feature-grid">
      <div class="feature-card" @click="$router.push('/resume')">
        <div class="fc-icon" style="background:linear-gradient(135deg,#3B82F6,#1D4ED8)">📄</div>
        <div class="fc-title">简历重构</div>
        <div class="fc-desc">AI分析JD，智能匹配关键词</div>
        <span class="fc-arrow">→</span>
      </div>
      <div class="feature-card" @click="$router.push('/interview')">
        <div class="fc-icon" style="background:linear-gradient(135deg,#8B5CF6,#7C3AED)">🎯</div>
        <div class="fc-title">面试模拟</div>
        <div class="fc-desc">AI动态出题，逐题复盘优化</div>
        <span class="fc-arrow">→</span>
      </div>
      <div class="feature-card" @click="$router.push('/calendar')">
        <div class="fc-icon" style="background:linear-gradient(135deg,#10B981,#059669)">📅</div>
        <div class="fc-title">招聘日历</div>
        <div class="fc-desc">新质生产力岗位精准推送</div>
        <span class="fc-arrow">→</span>
      </div>
    </div>

    <div class="tip-card">
      <div class="tip-head">
        <div class="tip-label">🌟 面试小Tips</div>
        <button class="tip-switch" type="button" @click="changeTip">换一个</button>
      </div>
      <div class="tip-text">{{ jobsStore.todayTip }}</div>
    </div>

    <div class="community-card" @click="showCommunity">
      <div class="cc-icon">👥</div>
      <div class="cc-text">
        <h3>加入求职社群</h3>
        <p>与求职同学交流，获取内推机会</p>
      </div>
      <span style="font-size:18px">→</span>
    </div>
  </div>
</template>

<script setup>import { onMounted, onUnmounted } from 'vue';
import { useJobsStore } from '../stores/jobs';
const jobsStore = useJobsStore();
let tipTimer = null;
onMounted(() => {
 jobsStore.fetchTodayTip();
 tipTimer = window.setInterval(() => {
  jobsStore.switchTip();
 }, 5 * 60 * 1000);
});
onUnmounted(() => {
 if (tipTimer) {
  window.clearInterval(tipTimer);
 }
});
function changeTip() {
 jobsStore.switchTip();
}
function showCommunity() {
 alert('社群功能开发中，敬请期待！');
}
</script>

<style scoped>
.tip-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.tip-card .tip-label {
  letter-spacing: 0;
  text-transform: none;
}

.tip-switch {
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #b45309;
  cursor: pointer;
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  padding: 8px 12px;
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.12);
}

.tip-switch:active {
  transform: scale(0.98);
}
</style>

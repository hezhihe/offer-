<template>
  <div class="page active">
    <div class="hero-gradient">
      <h1 class="gradient-text">Offer罗盘</h1>
      <p>AI驱动的2026届毕业生求职助手</p>
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
        <div class="fc-desc">AI动态出题，5维智能评分</div>
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
      <div class="tip-label">💡 求职攻略</div>
      <div class="tip-text">{{ jobsStore.todayTip }}</div>
    </div>

    <div class="community-card" @click="showCommunity">
      <div class="cc-icon">👥</div>
      <div class="cc-text">
        <h3>加入求职社群</h3>
        <p>与2026届同学交流，获取内推机会</p>
      </div>
      <span style="font-size:18px">→</span>
    </div>
  </div>
</template>

<script setup>import { onMounted } from 'vue';
import { useJobsStore } from '../stores/jobs';
const jobsStore = useJobsStore();
onMounted(() => {
 jobsStore.fetchTodayTip();
});
function showCommunity() {
 alert('社群功能开发中，敬请期待！');
}
</script>
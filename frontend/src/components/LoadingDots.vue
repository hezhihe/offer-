<!--
组件职责：统一加载点动画。
边界：纯 UI 组件，不包含任何业务逻辑。
-->

<template>
  <span
    class="loading-dots-component"
    :class="[`loading-dots-${variant}`, { 'loading-dots-block': block }]"
    aria-hidden="true"
  >
    <span></span>
    <span></span>
    <span></span>
  </span>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default'
  },
  block: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.loading-dots-component {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  line-height: 1;
  vertical-align: middle;
}

.loading-dots-component span {
  display: block;
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 999px;
  background: #5b7da8;
  opacity: .45;
  animation: loadingDotWave 0.9s ease-in-out infinite;
}

.loading-dots-component span:nth-child(2) {
  animation-delay: 0.14s;
}

.loading-dots-component span:nth-child(3) {
  animation-delay: 0.28s;
}

.loading-dots-primary span {
  background: #fff;
  box-shadow: 0 0 0 1px rgba(255,255,255,.28);
}

.loading-dots-history {
  gap: 8px;
  min-width: 64px;
  height: 44px;
  margin: 0 auto 10px;
}

.loading-dots-history span {
  width: 9px;
  height: 9px;
  flex-basis: 9px;
}

.loading-dots-block {
  display: flex;
}

@keyframes loadingDotWave {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: .45;
  }
  40% {
    transform: translateY(-8px);
    opacity: 1;
  }
}
</style>

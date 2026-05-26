<template>
  <div class="modal-overlay" :class="{ show: visible }" @click.self="close">
    <div class="modal-content">
      <div class="modal-handle"></div>
      <button class="modal-close" @click="close">×</button>
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const visible = ref(false)

function open() {
  visible.value = true
}

function close() {
  visible.value = false
}

defineExpose({ open, close })
</script>
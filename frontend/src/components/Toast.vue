<template>
  <div class="toast" :class="{ show: toastVisible }">{{ toastMessage }}</div>
</template>

<script setup>
import { useToast } from '../composables/useToast'

const { toastMessage, toastVisible } = useToast()
</script>
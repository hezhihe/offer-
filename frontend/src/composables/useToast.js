import { ref } from 'vue'

const toastMessage = ref('')
const toastVisible = ref(false)

export function useToast() {
  function show(message) {
    toastMessage.value = message
    toastVisible.value = true
    setTimeout(() => {
      toastVisible.value = false
    }, 2500)
  }

  return {
    toastMessage,
    toastVisible,
    show
  }
}
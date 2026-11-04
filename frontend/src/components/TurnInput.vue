<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['submit'])

const MAX_CHARS = 4000
const text = ref('')

function submit() {
  const value = text.value.trim()
  if (!value || props.disabled) return
  emit('submit', value)
  text.value = ''
}

// Enter envia; Shift+Enter quebra a linha.
function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <form class="turn-input" @submit.prevent="submit">
    <label for="turn-text" class="sr-only">O que você faz?</label>
    <textarea
      id="turn-text"
      v-model="text"
      class="textarea"
      rows="3"
      :maxlength="MAX_CHARS"
      :disabled="disabled"
      placeholder="O que você faz ou diz? (Enter envia · Shift+Enter quebra a linha)"
      @keydown="onKeydown"
    ></textarea>
    <button type="submit" class="btn btn-primary" :disabled="disabled || !text.trim()">Agir</button>
  </form>
</template>

<style scoped>
.turn-input {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
}

.turn-input .textarea {
  flex: 1;
}

@media (max-width: 640px) {
  .turn-input {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

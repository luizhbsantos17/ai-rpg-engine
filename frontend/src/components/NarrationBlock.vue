<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  streaming: { type: Boolean, default: false },
})

// Texto da IA é sempre exibido como texto puro (nunca como HTML), por segurança.
const paragraphs = computed(() =>
  props.text
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean),
)
</script>

<template>
  <article class="narration" :class="{ streaming }" :aria-busy="streaming">
    <p v-for="(paragraph, index) in paragraphs" :key="index">{{ paragraph }}</p>
    <span v-if="streaming" class="caret" aria-hidden="true"></span>
  </article>
</template>

<style scoped>
.narration {
  font-family: var(--font-narration);
  font-size: 1.08rem;
  line-height: 1.75;
  color: var(--text);
  padding: var(--space-2) 0;
}

.narration p {
  margin: 0 0 0.9em;
  white-space: pre-wrap;
}

.narration p:last-of-type {
  display: inline;
}

.caret {
  display: inline-block;
  width: 0.55em;
  height: 1.1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent-glow);
  animation: blink 1s steps(2, start) infinite;
}

@keyframes blink {
  to {
    visibility: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  .caret {
    animation: none;
  }
}
</style>

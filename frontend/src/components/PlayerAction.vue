<script setup>
defineProps({
  text: { type: String, required: true },
  failed: { type: Boolean, default: false }, // jogada que não chegou a ser narrada
})
</script>

<template>
  <div class="player-action" :class="{ failed }">
    <span class="label">Você<template v-if="failed"> · não concluída</template></span>
    <p>{{ text }}</p>
  </div>
</template>

<style scoped>
.player-action {
  margin: var(--space-4) 0;
  padding: var(--space-2) var(--space-4);
  border-left: 2px solid var(--gold);
  background: linear-gradient(90deg, rgba(224, 184, 102, 0.08), transparent 70%);
}

.label {
  display: block;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--gold);
}

.failed {
  opacity: 0.55;
  border-left-style: dashed;
}

p {
  margin: var(--space-1) 0 0;
  white-space: pre-wrap;
  color: var(--text);
}
</style>

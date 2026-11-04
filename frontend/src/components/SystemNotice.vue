<script setup>
// Mensagem no estilo "janela de sistema" (interface diegética, SPEC 12.2).
defineProps({
  tag: { type: String, default: 'SISTEMA' },
  tone: { type: String, default: 'info' }, // info | alert | error
})
</script>

<template>
  <div class="notice" :class="`tone-${tone}`" role="status">
    <span class="tag">[{{ tag }}]</span>
    <div class="body"><slot /></div>
  </div>
</template>

<style scoped>
.notice {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  margin: var(--space-4) 0;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  background: rgba(12, 22, 40, 0.85);
  box-shadow: inset 0 0 18px rgba(108, 199, 255, 0.07);
  font-size: 0.95rem;
}

.tag {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--accent);
  white-space: nowrap;
  padding-top: 2px;
}

.body {
  flex: 1;
}

.tone-alert .tag {
  color: var(--gold);
}

.tone-error {
  border-color: rgba(255, 122, 122, 0.45);
  background: var(--danger-bg);
}

.tone-error .tag {
  color: var(--danger);
}
</style>

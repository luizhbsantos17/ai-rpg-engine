<script setup>
// Saída dos comandos /admin e /debug. Fica fora da história e não é salva como narração.
defineProps({
  log: { type: Array, required: true },
})
defineEmits(['clear'])
</script>

<template>
  <section v-if="log.length" class="console" aria-label="Console do administrador">
    <header>
      <span class="tag">CONSOLE ADMIN</span>
      <button type="button" class="clear" @click="$emit('clear')">limpar</button>
    </header>
    <div v-for="(entry, index) in log" :key="index" class="entry" :class="{ failed: !entry.ok }">
      <div class="command">&gt; {{ entry.command }}</div>
      <pre>{{ entry.lines.join('\n') }}</pre>
    </div>
  </section>
</template>

<style scoped>
.console {
  margin: var(--space-4) 0;
  border: 1px dashed rgba(224, 184, 102, 0.6);
  border-radius: var(--radius);
  background: rgba(10, 8, 4, 0.85);
  font-family: var(--font-mono);
  font-size: 0.82rem;
}

header {
  display: flex;
  justify-content: space-between;
  padding: var(--space-1) var(--space-3);
  border-bottom: 1px dashed rgba(224, 184, 102, 0.4);
}

.tag {
  color: var(--gold);
  letter-spacing: 0.2em;
  font-size: 0.72rem;
}

.clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font: inherit;
}

.entry {
  padding: var(--space-2) var(--space-3);
}

.command {
  color: var(--gold);
}

.failed .command {
  color: var(--danger);
}

pre {
  margin: var(--space-1) 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: var(--text);
  font: inherit;
}
</style>

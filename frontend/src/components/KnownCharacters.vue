<script setup>
// Personagens conhecidos: só o que o protagonista sabe (SPEC 6.1). Ninguém aqui mostra o status verdadeiro.
defineProps({
  characters: { type: Array, default: () => [] },
})

const LEVELS = {
  confirmed: { label: 'confirmado', cls: 'confirmed' },
  partial: { label: 'parcial', cls: 'partial' },
  estimated: { label: 'estimado', cls: 'estimated' },
  unknown: { label: 'desconhecido', cls: 'unknown' },
}
const FIELD_NAMES = { identity: 'identidade', skills: 'habilidades' }
</script>

<template>
  <section class="known" aria-label="Personagens conhecidos">
    <header class="known-header"><span class="tag">CONHECIDOS</span></header>
    <p v-if="!characters.length" class="muted small">Você ainda não sabe nada de especial sobre ninguém.</p>
    <article v-for="person in characters" :key="person.id" class="person">
      <h3>{{ person.name }}</h3>
      <ul class="facts">
        <li v-for="fact in person.facts" :key="fact.field">
          <span class="field">{{ FIELD_NAMES[fact.field] ?? fact.field }}</span>
          <span class="value">{{ fact.value ?? '???' }}</span>
          <span class="level" :class="LEVELS[fact.level]?.cls">{{ LEVELS[fact.level]?.label ?? fact.level }}</span>
        </li>
      </ul>
    </article>
  </section>
</template>

<style scoped>
.known {
  margin-top: var(--space-4);
  background: var(--panel);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-4);
  font-size: 0.88rem;
}

.known-header {
  margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-3);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--line);
  background: linear-gradient(90deg, rgba(108, 199, 255, 0.1), transparent);
}

.tag {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  color: var(--accent);
}

.person + .person {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--line);
}

.person h3 {
  font-size: 0.95rem;
  margin: 0 0 var(--space-1);
  color: var(--text);
}

.facts {
  list-style: none;
  margin: 0;
  padding: 0;
}

.facts li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-2);
  padding: 2px 0;
}

.field {
  color: var(--text-muted);
}

.value {
  font-family: var(--font-mono);
  color: var(--text);
  overflow-wrap: anywhere;
}

.level {
  font-size: 0.7rem;
  padding: 0 var(--space-1);
  border-radius: 4px;
  border: 1px solid var(--line);
  color: var(--text-muted);
  white-space: nowrap;
}

.level.confirmed {
  border-color: rgba(127, 224, 168, 0.5);
  color: var(--success);
}

.level.partial,
.level.estimated {
  border-color: rgba(224, 184, 102, 0.5);
  color: var(--gold);
}

.small {
  font-size: 0.85rem;
  margin: 0;
}
</style>

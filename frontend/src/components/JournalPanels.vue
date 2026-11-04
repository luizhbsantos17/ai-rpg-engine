<script setup>
// Mapa, diário e laços do protagonista (uma aba de cada, escolhida por `view`).
defineProps({
  view: { type: String, required: true }, // 'map' | 'diary' | 'bonds'
  journal: { type: Object, required: true },
})
</script>

<template>
  <section class="journal-panel">
    <template v-if="view === 'map'">
      <div v-if="journal.map.current" class="here">
        <h3>Você está em: {{ journal.map.current.name }}</h3>
        <p v-if="journal.map.current.present.length" class="small">
          À vista: {{ journal.map.current.present.map((p) => p.name + (p.status ? ` (${p.status})` : '')).join(', ') }}
        </p>
        <p v-if="journal.map.current.items.length" class="small">
          No chão: {{ journal.map.current.items.map((i) => `${i.name} ×${i.quantity}`).join(', ') }}
        </p>
      </div>
      <h4>Lugares visitados</h4>
      <ul class="list">
        <li v-for="place in journal.map.places" :key="place.id" :class="{ current: place.current }" :title="place.description">
          {{ place.current ? '◆' : '◇' }} {{ place.name }}
        </li>
        <li v-if="!journal.map.places.length" class="muted small">Nenhum ainda.</li>
      </ul>
    </template>

    <template v-else-if="view === 'diary'">
      <ol class="diary">
        <li v-for="(entry, index) in journal.diary" :key="index" :class="entry.kind">
          <span class="turn">{{ entry.kind === 'summary' ? `Turnos ${entry.from_turn}–${entry.turn}` : `Turno ${entry.turn}` }}</span>
          <p>{{ entry.text }}</p>
        </li>
        <li v-if="!journal.diary.length" class="muted small">O diário se enche conforme a história avança.</li>
      </ol>
    </template>

    <template v-else>
      <ul class="list">
        <li v-for="bond in journal.bonds" :key="bond.name" class="bond">
          <strong>{{ bond.name }}</strong>
          <span v-if="bond.labels.length" class="labels">{{ bond.labels.join(' · ') }}</span>
          <span v-if="Object.keys(bond.dimensions).length" class="small muted">
            {{ Object.entries(bond.dimensions).map(([k, v]) => `${k} ${v}`).join(', ') }}
          </span>
        </li>
        <li v-if="!journal.bonds.length" class="muted small">Seus laços aparecem aqui.</li>
      </ul>
      <p class="muted small">O que os outros sentem por você, só a história revela.</p>
    </template>
  </section>
</template>

<style scoped>
.journal-panel {
  font-size: 0.88rem;
}

h3 {
  font-size: 0.95rem;
  color: var(--gold);
  margin: 0 0 var(--space-1);
}

h4 {
  font-family: var(--font-ui);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: var(--space-3) 0 var(--space-1);
}

.here {
  padding-bottom: var(--space-2);
  border-bottom: 1px dashed var(--line);
}

.list,
.diary {
  list-style: none;
  margin: 0;
  padding: 0;
}

.list li {
  padding: 3px 0;
}

.current {
  color: var(--accent);
}

.diary li {
  padding: var(--space-2) 0;
  border-bottom: 1px dashed var(--line);
}

.diary p {
  margin: 2px 0 0;
  white-space: pre-wrap;
}

.diary .summary p {
  font-family: var(--font-narration);
}

.turn {
  font-size: 0.72rem;
  color: var(--text-faint);
}

.bond {
  display: flex;
  flex-direction: column;
  border-bottom: 1px dashed var(--line);
}

.labels {
  color: var(--gold);
  font-size: 0.82rem;
}

.small {
  font-size: 0.82rem;
  margin: var(--space-1) 0 0;
}
</style>

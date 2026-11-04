<script setup>
// Diário de missões: só as que o jogador conhece (as ocultas chegam quando forem reveladas).
import { computed } from 'vue'

const props = defineProps({
  quests: { type: Array, default: () => [] },
})

const STATUS = { active: 'Em andamento', completed: 'Concluída', failed: 'Falhou', abandoned: 'Abandonada' }
const KIND = { main: 'Principal', side: 'Secundária', optional: 'Opcional', dynamic: 'Dinâmica' }

const active = computed(() => props.quests.filter((q) => q.status === 'active'))
const finished = computed(() => props.quests.filter((q) => q.status !== 'active'))
</script>

<template>
  <section class="quest-log" aria-label="Missões">
    <header class="quest-header"><span class="tag">MISSÕES</span></header>
    <p v-if="!quests.length" class="muted small">Nenhuma missão ainda.</p>
    <article v-for="quest in [...active, ...finished]" :key="quest.key" class="quest" :class="quest.status">
      <div class="quest-title">
        <span>{{ quest.title }}</span>
        <span class="kind">{{ KIND[quest.kind] ?? quest.kind }}</span>
      </div>
      <p v-if="quest.status !== 'active'" class="status">{{ STATUS[quest.status] ?? quest.status }}</p>
      <ul v-if="quest.objectives.length" class="objectives">
        <li v-for="(objective, index) in quest.objectives" :key="index" :class="{ done: objective.done }">
          {{ objective.done ? '✓' : '○' }} {{ objective.text }}
        </li>
      </ul>
    </article>
  </section>
</template>

<style scoped>
.quest-log {
  margin-top: var(--space-4);
  background: var(--panel);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-4);
  font-size: 0.9rem;
}

.quest-header {
  margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-3);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--line);
  background: linear-gradient(90deg, rgba(224, 184, 102, 0.14), transparent);
}

.tag {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  color: var(--gold);
}

.quest {
  padding: var(--space-2) 0;
  border-bottom: 1px dashed var(--line);
}

.quest:last-child {
  border-bottom: none;
}

.quest-title {
  display: flex;
  justify-content: space-between;
  gap: var(--space-2);
  color: var(--text);
}

.kind {
  font-size: 0.72rem;
  color: var(--text-faint);
  white-space: nowrap;
}

.status {
  margin: 2px 0 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.completed .quest-title {
  color: var(--success);
}

.failed .quest-title,
.abandoned .quest-title {
  color: var(--text-faint);
  text-decoration: line-through;
}

.objectives {
  list-style: none;
  margin: var(--space-1) 0 0;
  padding: 0;
  color: var(--text-muted);
}

.objectives .done {
  color: var(--text-faint);
  text-decoration: line-through;
}

.small {
  font-size: 0.85rem;
  margin: 0;
}
</style>

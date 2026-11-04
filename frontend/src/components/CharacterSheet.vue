<script setup>
// "Janela de status" do protagonista (SPEC 12). Mostra só o próprio personagem (SPEC 6.1).
import { computed } from 'vue'

const props = defineProps({
  character: { type: Object, default: null },
  worldTime: { type: String, default: null },
})

const resources = computed(() => (props.character?.attributes ?? []).filter((a) => a.resource))
const attributes = computed(() => (props.character?.attributes ?? []).filter((a) => !a.resource))

function percent(attribute) {
  const value = Number(attribute.value)
  const max = Number(attribute.max)
  if (!Number.isFinite(value) || !Number.isFinite(max) || max <= 0) return 0
  return Math.max(0, Math.min(100, (value / max) * 100))
}

const statusLabel = { active: 'Ativo', dead: 'Morto' }
</script>

<template>
  <aside class="sheet" aria-label="Ficha do personagem">
    <header class="sheet-header">
      <span class="sheet-tag">STATUS</span>
      <span v-if="worldTime" class="world-time" title="Tempo do mundo">{{ worldTime }}</span>
    </header>

    <p v-if="!character" class="muted empty">A ficha aparece quando a história começar.</p>

    <template v-else>
      <h2 class="name">{{ character.name }}</h2>
      <p class="meta">
        <span :class="{ dead: character.status === 'dead' }">{{ statusLabel[character.status] ?? character.status }}</span>
        <template v-if="character.location"> · {{ character.location }}</template>
      </p>

      <section v-if="resources.length" class="block">
        <div v-for="resource in resources" :key="resource.key" class="resource" :title="resource.description">
          <div class="resource-label">
            <span>{{ resource.name }}</span>
            <span class="numbers">{{ resource.value }} / {{ resource.max }}</span>
          </div>
          <div class="bar" role="meter" :aria-valuenow="Number(resource.value)" aria-valuemin="0" :aria-valuemax="Number(resource.max)" :aria-label="resource.name">
            <div class="fill" :style="{ width: percent(resource) + '%' }"></div>
          </div>
        </div>
      </section>

      <section v-if="character.effects?.length" class="block">
        <h3>Efeitos</h3>
        <ul class="list">
          <li v-for="effect in character.effects" :key="effect.key" :title="effect.description">
            <span class="effect">{{ effect.name }}</span>
            <span v-if="effect.ends" class="level">até {{ effect.ends }}</span>
          </li>
        </ul>
      </section>

      <section v-if="attributes.length" class="block">
        <h3>Atributos</h3>
        <dl class="attributes">
          <template v-for="attribute in attributes" :key="attribute.key">
            <dt :title="attribute.description">{{ attribute.name }}</dt>
            <dd>{{ attribute.value }}</dd>
          </template>
        </dl>
      </section>

      <section class="block">
        <h3>Habilidades</h3>
        <ul v-if="character.skills.length" class="list">
          <li v-for="skill in character.skills" :key="skill.key" :title="skill.description">
            <span>{{ skill.name }}<small v-if="skill.ready_at" class="cooldown"> · recarga até {{ skill.ready_at }}</small></span>
            <span class="level">Nv. {{ skill.level }}<template v-if="skill.max_level"> / {{ skill.max_level }}</template></span>
          </li>
        </ul>
        <p v-else class="muted small">Nenhuma ainda.</p>
      </section>

      <section class="block">
        <h3>Inventário</h3>
        <ul v-if="character.items.length" class="list">
          <li v-for="item in character.items" :key="item.id" :title="item.description">
            <span>{{ item.name }}</span>
            <span class="level">×{{ item.quantity }}</span>
          </li>
        </ul>
        <p v-else class="muted small">Vazio.</p>
      </section>
    </template>
  </aside>
</template>

<style scoped>
.sheet {
  background: var(--panel);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow-panel), inset 0 0 24px rgba(108, 199, 255, 0.06);
  padding: var(--space-4);
  font-size: 0.92rem;
}

.sheet-header {
  border-bottom: 1px solid var(--line);
  margin: calc(-1 * var(--space-4)) calc(-1 * var(--space-4)) var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: linear-gradient(90deg, rgba(108, 199, 255, 0.14), transparent);
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.world-time {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--gold);
}

.effect {
  color: var(--gold);
}

.cooldown {
  color: var(--text-faint);
  font-size: 0.75rem;
}

.sheet-tag {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  color: var(--accent);
}

.name {
  color: var(--gold);
  margin: 0;
  font-size: 1.25rem;
}

.meta {
  margin: var(--space-1) 0 var(--space-3);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.dead {
  color: var(--danger);
}

.block {
  margin-top: var(--space-4);
}

.block h3 {
  font-family: var(--font-ui);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: var(--space-2);
}

.resource {
  margin-bottom: var(--space-3);
}

.resource-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 3px;
}

.numbers {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--line);
  overflow: hidden;
}

.fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #9fe0ff);
  box-shadow: 0 0 10px var(--accent-glow);
  transition: width 0.4s ease;
}

.attributes {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-1) var(--space-3);
  margin: 0;
}

.attributes dt {
  color: var(--text);
}

.attributes dd {
  margin: 0;
  font-family: var(--font-mono);
  color: var(--accent);
  text-align: right;
  overflow-wrap: anywhere;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.list li {
  display: flex;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 3px 0;
  border-bottom: 1px dashed var(--line);
}

.level {
  font-family: var(--font-mono);
  color: var(--text-muted);
  white-space: nowrap;
}

.small,
.empty {
  font-size: 0.85rem;
  margin: 0;
}
</style>

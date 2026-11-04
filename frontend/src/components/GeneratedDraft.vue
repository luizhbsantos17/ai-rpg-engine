<script setup>
// Rascunho de campanha gerada: o jogador vê só a introdução; os segredos ficam com o mestre.
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  draft: { type: Object, required: true },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['regenerate', 'save', 'start'])

const keep = reactive({ title: false, premise: false, genre_tags: false })
const editing = ref(false)
const form = reactive({ title: '', premise: '', tags: '' })

watch(
  () => props.draft,
  (draft) => {
    form.title = draft.title
    form.premise = draft.premise ?? ''
    form.tags = draft.genre_tags.join(', ')
  },
  { immediate: true },
)

function regenerate() {
  emit('regenerate', Object.keys(keep).filter((field) => keep[field]))
}

function save() {
  emit('save', {
    title: form.title,
    premise: form.premise,
    genre_tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
  })
  editing.value = false
}
</script>

<template>
  <article class="draft panel">
    <template v-if="!editing">
      <div class="row">
        <h2>{{ draft.title }}</h2>
        <label class="keep"><input v-model="keep.title" type="checkbox" /> manter</label>
      </div>
      <div class="row">
        <p class="tags">
          <span v-for="tag in draft.genre_tags" :key="tag" class="tag">{{ tag }}</span>
        </p>
        <label class="keep"><input v-model="keep.genre_tags" type="checkbox" /> manter</label>
      </div>
      <div class="row">
        <p class="premise">{{ draft.premise }}</p>
        <label class="keep"><input v-model="keep.premise" type="checkbox" /> manter</label>
      </div>
      <p v-if="draft.secrets_count" class="secrets">
        🔒 O mestre guardou {{ draft.secrets_count }} segredo(s) que você vai descobrir jogando.
      </p>
    </template>

    <form v-else @submit.prevent="save">
      <div class="field">
        <label for="draft-title">Título</label>
        <input id="draft-title" v-model="form.title" class="input" maxlength="200" required />
      </div>
      <div class="field">
        <label for="draft-tags">Gêneros e temas (separados por vírgula)</label>
        <input id="draft-tags" v-model="form.tags" class="input" />
      </div>
      <div class="field">
        <label for="draft-premise">Premissa</label>
        <textarea id="draft-premise" v-model="form.premise" class="textarea" rows="5" maxlength="4000" required></textarea>
      </div>
      <div class="actions">
        <button type="button" class="btn" @click="editing = false">Cancelar</button>
        <button type="submit" class="btn btn-primary" :disabled="busy || !form.title.trim()">Salvar ajustes</button>
      </div>
    </form>

    <div v-if="!editing" class="actions">
      <button type="button" class="btn" :disabled="busy" @click="regenerate">Gerar de novo</button>
      <button type="button" class="btn" :disabled="busy" @click="editing = true">Editar</button>
      <button type="button" class="btn btn-primary" :disabled="busy" @click="emit('start')">Começar</button>
    </div>
  </article>
</template>

<style scoped>
.draft h2 {
  color: var(--gold);
  margin: 0;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.keep {
  font-size: 0.8rem;
  color: var(--text-muted);
  white-space: nowrap;
  display: inline-flex;
  gap: var(--space-1);
  align-items: center;
}

.premise {
  margin: 0;
  font-family: var(--font-narration);
  line-height: 1.7;
  white-space: pre-wrap;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin: 0;
}

.tag {
  font-size: 0.75rem;
  padding: 1px var(--space-2);
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--text-muted);
}

.secrets {
  font-size: 0.85rem;
  color: var(--text-muted);
  border-top: 1px dashed var(--line);
  padding-top: var(--space-3);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}
</style>

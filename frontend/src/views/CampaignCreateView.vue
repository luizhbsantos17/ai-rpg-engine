<script setup>
// Criação de campanha: aleatória pela IA (padrão, SPEC 3.1) ou escrita pelo jogador.
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import * as api from '../api/campaigns.js'
import GeneratedDraft from '../components/GeneratedDraft.vue'
import SystemNotice from '../components/SystemNotice.vue'
import { useCampaignsStore } from '../stores/campaigns.js'

const router = useRouter()
const route = useRoute()
const store = useCampaignsStore()

const mode = ref('random') // 'random' | 'manual'
const error = ref(null)
const busy = ref(false)

// --- aleatória ---
const genres = ref('')
const themes = ref('')
const draft = ref(null)

// --- manual ---
const title = ref('')
const premise = ref('')
const tags = ref('')

const splitTags = (text) => text.split(',').map((t) => t.trim()).filter(Boolean)

onMounted(async () => {
  // Continuar a criação de um rascunho (vindo da lista de campanhas).
  if (route.query.draft) {
    try {
      draft.value = await api.getCampaign(String(route.query.draft))
    } catch (err) {
      error.value = err.message
    }
  }
})

async function run(task) {
  busy.value = true
  error.value = null
  try {
    await task()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

const generate = () =>
  run(async () => {
    draft.value = await api.generateCampaign({ genres: splitTags(genres.value), themes: themes.value })
  })

const regenerate = (keep) =>
  run(async () => {
    draft.value = await api.generateCampaign({
      genres: splitTags(genres.value),
      themes: themes.value,
      draft_id: draft.value.id,
      keep,
    })
  })

const saveDraft = (changes) =>
  run(async () => {
    draft.value = { ...draft.value, ...(await api.updateDraft(draft.value.id, changes)) }
  })

const start = () =>
  run(async () => {
    const campaign = await api.startCampaign(draft.value.id)
    router.push(`/campanha/${campaign.id}`)
  })

const createManual = () =>
  run(async () => {
    const campaign = await store.create({ title: title.value, premise: premise.value || null, genre_tags: splitTags(tags.value) })
    router.push(`/campanha/${campaign.id}`)
  })
</script>

<template>
  <section class="create">
    <h1>Nova campanha</h1>

    <div class="tabs" role="tablist">
      <button type="button" role="tab" class="tab" :class="{ active: mode === 'random' }" :aria-selected="mode === 'random'"
              @click="mode = 'random'">Gerar aleatória</button>
      <button type="button" role="tab" class="tab" :class="{ active: mode === 'manual' }" :aria-selected="mode === 'manual'"
              @click="mode = 'manual'">Escrever a minha</button>
    </div>

    <SystemNotice v-if="error" tone="error" tag="ERRO">{{ error }}</SystemNotice>

    <template v-if="mode === 'random'">
      <form v-if="!draft" class="panel" @submit.prevent="generate">
        <p class="muted">
          A IA inventa um mundo, uma premissa e segredos que só o mestre conhece. Tudo é opcional:
          deixe em branco para uma surpresa completa.
        </p>
        <div class="field">
          <label for="genres">Gêneros que você gostaria (opcional, separados por vírgula)</label>
          <input id="genres" v-model="genres" class="input" placeholder="isekai, horror, ficção científica..." />
        </div>
        <div class="field">
          <label for="themes">Preferências (opcional)</label>
          <textarea id="themes" v-model="themes" class="textarea" rows="3" maxlength="1000"
                    placeholder="Ex.: quero começar fraco; sem dragões; um mistério político..."></textarea>
        </div>
        <div class="actions">
          <RouterLink to="/" class="btn">Cancelar</RouterLink>
          <button type="submit" class="btn btn-primary" :disabled="busy">
            {{ busy ? 'Criando o mundo… (pode levar um minuto)' : 'Gerar campanha' }}
          </button>
        </div>
      </form>

      <template v-else>
        <p v-if="busy" class="muted waiting">A IA está trabalhando… (pode levar um minuto)</p>
        <GeneratedDraft :draft="draft" :busy="busy" @regenerate="regenerate" @save="saveDraft" @start="start" />
      </template>
    </template>

    <form v-else class="panel" @submit.prevent="createManual">
      <div class="field">
        <label for="title">Título</label>
        <input id="title" v-model="title" class="input" maxlength="200" required />
      </div>
      <div class="field">
        <label for="premise">Premissa (o ponto de partida da história)</label>
        <textarea id="premise" v-model="premise" class="textarea" rows="5" maxlength="4000"
                  placeholder="Ex.: Você acorda num templo em ruínas, sem lembrar como chegou ali..."></textarea>
      </div>
      <div class="field">
        <label for="tags">Gêneros e temas (separados por vírgula, opcional)</label>
        <input id="tags" v-model="tags" class="input" placeholder="fantasia sombria, mistério" />
      </div>
      <div class="actions">
        <RouterLink to="/" class="btn">Cancelar</RouterLink>
        <button type="submit" class="btn btn-primary" :disabled="busy || !title.trim()">
          {{ busy ? 'Criando…' : 'Criar e começar' }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.create {
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.tab {
  flex: 1;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  cursor: pointer;
}

.tab.active {
  border-color: var(--accent);
  color: var(--text);
  background: rgba(108, 199, 255, 0.12);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.waiting {
  font-style: italic;
}
</style>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import SystemNotice from '../components/SystemNotice.vue'
import { useCampaignsStore } from '../stores/campaigns.js'

const router = useRouter()
const store = useCampaignsStore()

const title = ref('')
const premise = ref('')
const tags = ref('')
const saving = ref(false)
const error = ref(null)

async function submit() {
  saving.value = true
  error.value = null
  try {
    const campaign = await store.create({
      title: title.value,
      premise: premise.value || null,
      genre_tags: tags.value
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    })
    router.push(`/campanha/${campaign.id}`)
  } catch (err) {
    error.value = err.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="panel create">
    <h1>Nova campanha</h1>
    <p class="muted">
      Nesta primeira versão você escreve a premissa. A geração aleatória de universos chega na Etapa 3.
    </p>

    <form @submit.prevent="submit">
      <div class="field">
        <label for="title">Título</label>
        <input id="title" v-model="title" class="input" maxlength="200" required />
      </div>
      <div class="field">
        <label for="premise">Premissa (o ponto de partida da história)</label>
        <textarea
          id="premise"
          v-model="premise"
          class="textarea"
          rows="5"
          maxlength="4000"
          placeholder="Ex.: Você acorda num templo em ruínas, sem lembrar como chegou ali..."
        ></textarea>
      </div>
      <div class="field">
        <label for="tags">Gêneros e temas (separados por vírgula, opcional)</label>
        <input id="tags" v-model="tags" class="input" placeholder="fantasia sombria, mistério" />
      </div>

      <SystemNotice v-if="error" tone="error" tag="ERRO">{{ error }}</SystemNotice>

      <div class="actions">
        <RouterLink to="/" class="btn">Cancelar</RouterLink>
        <button type="submit" class="btn btn-primary" :disabled="saving || !title.trim()">
          {{ saving ? 'Criando…' : 'Criar e começar' }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.create {
  max-width: 680px;
  width: 100%;
  margin: 0 auto;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>

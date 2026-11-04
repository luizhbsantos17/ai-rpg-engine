<script setup>
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import SystemNotice from '../components/SystemNotice.vue'
import { useCampaignsStore } from '../stores/campaigns.js'

const store = useCampaignsStore()
onMounted(() => store.fetch())

const formatDate = (iso) =>
  new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

async function remove(campaign) {
  const typed = window.prompt(
    `Excluir "${campaign.title}" apaga a campanha e todo o histórico, sem volta.\n` +
      'Para confirmar, digite o título exato:',
  )
  if (typed === null) return
  try {
    await store.remove(campaign.id, typed)
  } catch (err) {
    window.alert(err.message)
  }
}
</script>

<template>
  <section>
    <div class="heading">
      <h1>Suas campanhas</h1>
      <RouterLink to="/nova" class="btn btn-primary">+ Nova campanha</RouterLink>
    </div>

    <p v-if="store.loading" class="muted">Carregando…</p>
    <SystemNotice v-else-if="store.error" tone="error" tag="ERRO">{{ store.error }}</SystemNotice>

    <div v-else-if="store.items.length === 0" class="panel empty">
      <p>Nenhuma campanha ainda.</p>
      <RouterLink to="/nova" class="btn btn-primary">Criar a primeira</RouterLink>
    </div>

    <ul v-else class="campaign-list">
      <li v-for="campaign in store.items" :key="campaign.id" class="panel campaign-card">
        <div class="card-main">
          <h2>{{ campaign.title }} <span v-if="campaign.status === 'draft'" class="draft-badge">Rascunho</span></h2>
          <p v-if="campaign.genre_tags.length" class="tags">
            <span v-for="tag in campaign.genre_tags" :key="tag" class="tag">{{ tag }}</span>
          </p>
          <p v-if="campaign.premise" class="premise">{{ campaign.premise }}</p>
          <p class="muted small">Última atividade: {{ formatDate(campaign.updated_at) }}</p>
        </div>
        <div class="card-actions">
          <RouterLink v-if="campaign.status === 'draft'" :to="`/nova?draft=${campaign.id}`" class="btn btn-primary">
            Continuar criação
          </RouterLink>
          <RouterLink v-else :to="`/campanha/${campaign.id}`" class="btn btn-primary">Continuar</RouterLink>
          <button type="button" class="btn btn-danger" @click="remove(campaign)">Excluir</button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}

.heading h1 {
  margin: 0;
}

.empty {
  text-align: center;
}

.campaign-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-4);
}

.campaign-card {
  display: flex;
  gap: var(--space-4);
  justify-content: space-between;
  align-items: flex-start;
}

.card-main h2 {
  color: var(--gold);
  margin-bottom: var(--space-2);
}

.draft-badge {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 1px var(--space-2);
  border: 1px dashed var(--line-strong);
  border-radius: 999px;
  color: var(--text-muted);
  vertical-align: middle;
}

.premise {
  margin: var(--space-2) 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

.small {
  font-size: 0.8rem;
  margin: 0;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .campaign-card {
    flex-direction: column;
  }
  .card-actions {
    flex-direction: row;
  }
}
</style>

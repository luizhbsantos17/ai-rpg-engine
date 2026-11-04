<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import CharacterSheet from '../components/CharacterSheet.vue'
import KnownCharacters from '../components/KnownCharacters.vue'
import QuestLog from '../components/QuestLog.vue'
import NarrationBlock from '../components/NarrationBlock.vue'
import PlayerAction from '../components/PlayerAction.vue'
import SystemNotice from '../components/SystemNotice.vue'
import TurnInput from '../components/TurnInput.vue'
import { usePlayStore } from '../stores/play.js'
import { parseNotice } from '../utils/notices.js'

const props = defineProps({ id: { type: String, required: true } })
const play = usePlayStore()
const bottom = ref(null)
const sheetOpen = ref(false) // em telas pequenas a ficha abre por botão

const START_PROMPT = 'Comece a história.'

onMounted(() => play.load(props.id))
watch(
  () => props.id,
  (id) => play.load(id),
)

// Acompanha o texto novo, rolando a página até o fim.
watch(
  () => [play.messages.length, play.streamingText.length, play.failure],
  async () => {
    await nextTick()
    bottom.value?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  },
)
</script>

<template>
  <section class="play">
    <p v-if="play.loading" class="muted">Abrindo campanha…</p>

    <template v-else-if="play.loadError">
      <SystemNotice tone="error" tag="ERRO">{{ play.loadError }}</SystemNotice>
      <RouterLink to="/" class="btn">Voltar às campanhas</RouterLink>
    </template>

    <template v-else-if="play.campaign">
      <header class="campaign-header">
        <div>
          <h1>{{ play.campaign.title }}</h1>
          <p v-if="play.campaign.premise" class="premise">{{ play.campaign.premise }}</p>
        </div>
        <div class="header-actions">
          <RouterLink :to="`/campanha/${id}/configuracoes`" class="btn">Configurações</RouterLink>
          <button type="button" class="btn sheet-toggle" :aria-expanded="sheetOpen" @click="sheetOpen = !sheetOpen">
            {{ sheetOpen ? 'Fechar ficha' : 'Ficha' }}
          </button>
        </div>
      </header>

      <div class="layout">
      <div class="story" aria-live="polite">
        <SystemNotice v-if="play.isEmpty && !play.streaming">
          A história ainda não começou. Escreva a primeira ação do seu personagem ou peça ao narrador para começar.
          <div class="start">
            <button type="button" class="btn btn-primary" @click="play.send(START_PROMPT)">Começar a história</button>
          </div>
        </SystemNotice>

        <template v-for="message in play.messages" :key="message.id">
          <PlayerAction
            v-if="message.role === 'player'"
            :text="message.content"
            :failed="play.turns[message.turn_id]?.status === 'failed'"
          />
          <NarrationBlock v-else-if="message.role === 'narration'" :text="message.content" />
          <SystemNotice
            v-else
            :tag="parseNotice(message.content).tag"
            :tone="parseNotice(message.content).tone"
            class="compact"
          >{{ parseNotice(message.content).text }}</SystemNotice>
        </template>

        <NarrationBlock v-if="play.streaming" :text="play.streamingText" streaming />
        <p v-if="play.streaming && !play.streamingText" class="muted waiting">O narrador está pensando…</p>

        <SystemNotice v-if="play.failure" tone="error" tag="FALHA">
          {{ play.failure.message }}
          <div v-if="play.failure.retryable" class="start">
            <button type="button" class="btn" :disabled="play.streaming" @click="play.retry()">Tentar de novo</button>
          </div>
        </SystemNotice>
        <SystemNotice v-if="play.notice" tone="alert" tag="AVISO">{{ play.notice }}</SystemNotice>
        <div ref="bottom"></div>
      </div>
      <div class="sheet-panel" :class="{ open: sheetOpen }">
        <CharacterSheet :character="play.character" :world-time="play.worldTime" />
        <QuestLog :quests="play.quests" />
        <KnownCharacters :characters="play.known" />
      </div>
      </div>

      <div class="input-bar">
        <TurnInput :disabled="play.streaming" @submit="play.send" />
      </div>
    </template>
  </section>
</template>

<style scoped>
.play {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.campaign-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--line);
}

.header-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: var(--space-5);
  align-items: start;
  flex: 1;
}

.sheet-panel {
  position: sticky;
  top: var(--space-4);
}

.sheet-toggle {
  display: none;
}

.compact {
  margin: var(--space-2) 0;
  padding: var(--space-2) var(--space-3);
  font-size: 0.88rem;
}

@media (max-width: 860px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .sheet-toggle {
    display: inline-flex;
  }
  .sheet-panel {
    display: none;
    position: static;
    order: -1;
  }
  .sheet-panel.open {
    display: block;
  }
}

.campaign-header h1 {
  color: var(--gold);
  margin-bottom: var(--space-2);
}

.premise {
  margin: 0;
  color: var(--text-muted);
  font-style: italic;
}

.story {
  flex: 1;
  padding-bottom: var(--space-5);
}

.start {
  margin-top: var(--space-3);
}

.waiting {
  font-style: italic;
}

.input-bar {
  position: sticky;
  bottom: 0;
  padding: var(--space-3) 0 var(--space-4);
  background: linear-gradient(0deg, var(--bg) 70%, transparent);
}
</style>

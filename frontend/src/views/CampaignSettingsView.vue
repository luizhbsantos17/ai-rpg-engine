<script setup>
// Configurações da campanha (SPEC 19): experiência × conteúdo; regras só listadas (mudam pelo motor).
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import * as api from '../api/campaigns.js'
import SystemNotice from '../components/SystemNotice.vue'

const props = defineProps({ id: { type: String, required: true } })

const view = ref(null)
const error = ref(null)
const warnings = ref([])
const saved = ref(false)
const busy = ref(false)
const experience = reactive({})
const content = reactive({ intensity: 2, categories: {} })

const LEVELS = [
  { value: 0, label: 'Evitar' },
  { value: 1, label: 'Leve' },
  { value: 2, label: 'Moderado' },
  { value: 3, label: 'Intenso' },
]
const SIMULATION = [
  { value: null, label: 'Padrão do programa' },
  { value: 'off', label: 'Desligada' },
  { value: 'low', label: 'Baixa (só em passagens de 1 dia ou mais)' },
  { value: 'normal', label: 'Normal (6 horas ou mais)' },
  { value: 'high', label: 'Alta (2 horas ou mais)' },
]

function fill(data) {
  view.value = data
  Object.assign(experience, data.experience)
  content.intensity = data.content.intensity
  content.categories = { ...data.content.categories }
}

onMounted(async () => {
  try {
    fill(await api.getSettings(props.id))
  } catch (err) {
    error.value = err.message
  }
})

function categoryValue(key) {
  return content.categories[key] ?? ''
}

function setCategory(key, value) {
  if (value === '') delete content.categories[key]
  else content.categories[key] = Number(value)
}

async function save() {
  busy.value = true
  error.value = null
  saved.value = false
  try {
    const payload = {
      experience: { ...experience, ai_model: experience.ai_model || null },
      content: { intensity: Number(content.intensity), categories: content.categories },
    }
    const result = await api.saveSettings(props.id, payload)
    fill(result)
    warnings.value = result.warnings ?? []
    saved.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="settings">
    <div class="heading">
      <h1>Configurações da campanha</h1>
      <RouterLink :to="`/campanha/${id}`" class="btn">Voltar ao jogo</RouterLink>
    </div>

    <SystemNotice v-if="error" tone="error" tag="ERRO">{{ error }}</SystemNotice>
    <p v-if="!view && !error" class="muted">Carregando…</p>

    <form v-if="view" @submit.prevent="save">
      <fieldset class="panel">
        <legend>Experiência <span class="muted small">(muda como o jogo é apresentado; não altera o mundo)</span></legend>
        <div class="field">
          <label for="model">Modelo de IA (vazio = padrão: {{ view.defaults.ai_model || 'primeiro instalado' }})</label>
          <input id="model" v-model="experience.ai_model" class="input" maxlength="200" placeholder="ex.: qwen2.5:3b" />
        </div>
        <div class="field">
          <label for="creativity">
            Criatividade: {{ experience.creativity ?? `padrão (${view.defaults.creativity})` }}
          </label>
          <input id="creativity" v-model.number="experience.creativity" type="range" min="0" max="2" step="0.1" />
        </div>
        <div class="field">
          <label for="mechanics">Motor de regras (ficha, testes, missões)</label>
          <select id="mechanics" v-model="experience.mechanics" class="input">
            <option :value="null">Padrão do programa</option>
            <option :value="true">Ligado</option>
            <option :value="false">Desligado (só narração, mais rápido)</option>
          </select>
        </div>
        <div class="field">
          <label for="simulation">Mundo vivo (personagens agem longe de você quando o tempo passa)</label>
          <select id="simulation" v-model="experience.simulation" class="input">
            <option v-for="option in SIMULATION" :key="String(option.value)" :value="option.value">{{ option.label }}</option>
          </select>
        </div>
        <label class="check"><input v-model="experience.show_dice" type="checkbox" /> Mostrar os avisos de testes com os números dos dados</label>
        <label class="check"><input v-model="experience.system_window" type="checkbox" /> Mostrar avisos de "sistema" (desligue em universos sem janela de status)</label>
      </fieldset>

      <fieldset class="panel">
        <legend>Conteúdo e maturidade</legend>
        <p class="muted small">
          Sempre valem: conteúdo sexual só entre adultos; violência sexual pode ser tema, nunca erotizada.
          <template v-if="view.provider.content_note"><br />{{ view.provider.content_note }}</template>
        </p>
        <div class="field">
          <label for="intensity">Intensidade geral</label>
          <select id="intensity" v-model.number="content.intensity" class="input">
            <option v-for="level in LEVELS" :key="level.value" :value="level.value">{{ level.label }}</option>
          </select>
        </div>
        <div class="categories">
          <div v-for="(name, key) in view.content_categories" :key="key" class="field">
            <label :for="`cat-${key}`">{{ name }}</label>
            <select :id="`cat-${key}`" class="input" :value="categoryValue(key)" @change="setCategory(key, $event.target.value)">
              <option value="">Usar a geral</option>
              <option v-for="level in LEVELS" :key="level.value" :value="level.value">{{ level.label }}</option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset class="panel">
        <legend>Regras do universo</legend>
        <p class="muted small">
          Regras mudam o funcionamento do mundo e por isso só mudam dentro da história (com motivo e nova versão),
          ou pelo modo administrador. Regras atuais:
        </p>
        <ul class="rules">
          <li v-for="rule in view.rules" :key="`${rule.kind}-${rule.key}`">
            <span>{{ rule.name }}</span><span class="muted small">{{ rule.kind }} · versão {{ rule.version }}</span>
          </li>
          <li v-if="!view.rules.length" class="muted small">Ainda não há regras (são criadas no primeiro turno).</li>
        </ul>
      </fieldset>

      <SystemNotice v-for="warning in warnings" :key="warning" tone="alert" tag="AVISO">{{ warning }}</SystemNotice>
      <SystemNotice v-if="saved && !warnings.length">Configurações salvas.</SystemNotice>

      <div class="actions">
        <button type="submit" class="btn btn-primary" :disabled="busy">{{ busy ? 'Salvando…' : 'Salvar' }}</button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.settings {
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
}

.heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
}

.heading h1 {
  margin: 0;
}

fieldset {
  margin: 0 0 var(--space-4);
}

legend {
  font-family: var(--font-display);
  color: var(--gold);
  padding: 0 var(--space-2);
}

.check {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  margin-bottom: var(--space-2);
  font-size: 0.92rem;
}

.categories {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0 var(--space-4);
}

.rules {
  list-style: none;
  margin: 0;
  padding: 0;
}

.rules li {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px dashed var(--line);
}

.small {
  font-size: 0.82rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

input[type='range'] {
  width: 100%;
}
</style>

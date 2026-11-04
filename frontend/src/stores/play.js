// Estado da partida aberta: histórico, texto chegando aos poucos e falhas a repetir.
import { defineStore } from 'pinia'

import * as api from '../api/campaigns.js'

export const STREAM_CUT_MESSAGE = 'A conexão caiu antes do fim da narração. Tente de novo.'

function newTurnId() {
  return crypto.randomUUID()
}

export const usePlayStore = defineStore('play', {
  state: () => ({
    campaign: null,
    character: null, // ficha do protagonista (null até a campanha ser preparada)
    worldTime: null, // "dia 1, 08:00"
    quests: [], // missões visíveis ao jogador
    known: [], // personagens conhecidos (só o que o protagonista sabe)
    journal: { map: { current: null, places: [] }, diary: [], bonds: [] },
    messages: [],
    turns: {},
    loading: false,
    loadError: null,
    streaming: false,
    streamingText: '',
    failure: null, // { turnId, input, message, retryable }
    notice: null, // aviso que não é falha de turno (ex.: pedido recusado)
    replacingId: null, // narração sendo reescrita ("gerar outra versão"): some enquanto a nova chega
  }),
  getters: {
    isEmpty: (state) => state.messages.length === 0,
    // Só a narração da última jogada concluída pode ganhar outra versão.
    regenerableId: (state) => {
      if (state.streaming || state.failure) return null
      const last = state.messages.at(-1)
      if (!last || last.role !== 'narration') return null
      return state.turns[last.turn_id]?.status === 'completed' ? last.id : null
    },
  },
  actions: {
    async load(campaignId) {
      this.$reset()
      this.loading = true
      try {
        const [history, sheet] = await Promise.all([api.getHistory(campaignId), api.getSheet(campaignId)])
        this.campaign = history.campaign
        this.character = sheet.character
        this.worldTime = sheet.world_time ?? null
        this.quests = sheet.quests ?? []
        this.messages = history.messages
        this.turns = Object.fromEntries(history.turns.map((t) => [t.id, t]))
        // Ao reabrir, se a última jogada falhou, oferece repetir (D-012).
        const last = history.turns.at(-1)
        if (last && last.status === 'failed') {
          this.failure = { turnId: last.id, input: last.player_input, message: last.error, retryable: true }
        }
      } catch (err) {
        this.loadError = err.message
      } finally {
        this.loading = false
      }
      await this.refreshKnown()
    },

    async refreshKnown() {
      if (!this.campaign) return
      try {
        const [known, journal] = await Promise.all([api.getKnown(this.campaign.id), api.getJournal(this.campaign.id)])
        this.known = known
        this.journal = journal
      } catch {
        // painéis complementares: se falharem, a história continua
      }
    },

    send(input) {
      return this.runTurn(newTurnId(), input)
    },

    retry() {
      if (!this.failure) return Promise.resolve()
      return this.runTurn(this.failure.turnId, this.failure.input)
    },

    async refreshSheet() {
      if (!this.campaign) return
      try {
        const sheet = await api.getSheet(this.campaign.id)
        this.character = sheet.character
        this.worldTime = sheet.world_time ?? null
        this.quests = sheet.quests ?? []
      } catch {
        // a ficha é complementar: se falhar, a história continua
      }
      await this.refreshKnown()
    },

    addMessage(message) {
      if (message && !this.messages.some((m) => m.id === message.id)) {
        this.messages.push(message)
        this.messages.sort((a, b) => a.seq - b.seq)
      }
    },

    // Outra versão da narração da última jogada (mesmos dados). Se falhar, a anterior fica.
    async regenerate() {
      const old = this.messages.find((m) => m.id === this.regenerableId)
      if (!old || !this.campaign) return
      this.streaming = true
      this.streamingText = ''
      this.notice = null
      this.replacingId = old.id
      let finished = false
      try {
        await api.regenerateTurn(this.campaign.id, old.turn_id, {
          onDelta: (data) => {
            this.streamingText += data.text
          },
          onDone: (data) => {
            finished = true
            this.turns[data.turn.id] = data.turn
            this.messages = this.messages.filter((m) => m.id !== old.id)
            this.addMessage(data.narration_message)
          },
          onError: (data) => {
            finished = true
            this.turns[data.turn.id] = data.turn
            this.notice = `Não foi possível gerar outra versão (a anterior foi mantida): ${data.message}`
          },
        })
        if (!finished) this.notice = `${STREAM_CUT_MESSAGE} A versão anterior foi mantida.`
      } catch (err) {
        this.notice = err.message
      } finally {
        this.streaming = false
        this.streamingText = ''
        this.replacingId = null
      }
    },

    async runTurn(turnId, input) {
      if (this.streaming || !this.campaign) return
      this.streaming = true
      this.streamingText = ''
      this.failure = null
      this.notice = null
      let finished = false
      try {
        await api.playTurn(this.campaign.id, turnId, input, {
          onTurn: (data) => {
            this.turns[data.turn.id] = data.turn
            this.addMessage(data.player_message)
          },
          onMechanics: (data) => {
            for (const message of data.messages) this.addMessage(message)
            this.refreshSheet()
          },
          onDelta: (data) => {
            this.streamingText += data.text
          },
          onDone: (data) => {
            finished = true
            this.turns[data.turn.id] = data.turn
            this.addMessage(data.narration_message)
            this.streamingText = ''
          },
          onError: (data) => {
            finished = true
            this.turns[data.turn.id] = data.turn
            this.failure = { turnId, input, message: data.message, retryable: data.retryable }
            this.streamingText = ''
          },
        })
        if (!finished) {
          this.failure = { turnId, input, message: STREAM_CUT_MESSAGE, retryable: true }
        }
      } catch (err) {
        if (err.status === 0) {
          this.failure = { turnId, input, message: err.message, retryable: true }
        } else {
          this.notice = err.message
        }
      } finally {
        this.streaming = false
        this.streamingText = ''
      }
    },
  },
})

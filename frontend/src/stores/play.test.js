import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api/campaigns.js'
import { ApiError } from '../api/client.js'
import { STREAM_CUT_MESSAGE, usePlayStore } from './play.js'

vi.mock('../api/campaigns.js', () => ({
  getHistory: vi.fn(),
  getSheet: vi.fn(),
  getKnown: vi.fn().mockResolvedValue([]),
  getJournal: vi.fn().mockResolvedValue({ map: { current: null, places: [] }, diary: [], bonds: [] }),
  playTurn: vi.fn(),
}))

const campaign = { id: 'c1', title: 'Teste', premise: null }
const turn = (id, status, extra = {}) => ({ id, number: 1, status, error: null, player_input: 'Ajo.', ...extra })
const msg = (id, seq, role, content, turnId = 't1') => ({ id, seq, role, content, turn_id: turnId })

async function loadedStore(history = {}, character = null) {
  api.getHistory.mockResolvedValue({ campaign, turns: [], messages: [], ...history })
  api.getSheet.mockResolvedValue({ character })
  const store = usePlayStore()
  await store.load('c1')
  return store
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('usePlayStore', () => {
  it('carrega o histórico em ordem', async () => {
    const store = await loadedStore({
      turns: [turn('t1', 'completed')],
      messages: [msg('m1', 1, 'player', 'Ajo.'), msg('m2', 2, 'narration', 'Algo acontece.')],
    })
    expect(store.campaign.title).toBe('Teste')
    expect(store.messages.map((m) => m.content)).toEqual(['Ajo.', 'Algo acontece.'])
    expect(store.failure).toBeNull()
  })

  it('ao reabrir com a última jogada falhada, oferece repetir', async () => {
    const store = await loadedStore({
      turns: [turn('t1', 'failed', { error: 'Ollama desligado.' })],
      messages: [msg('m1', 1, 'player', 'Ajo.')],
    })
    expect(store.failure).toEqual({ turnId: 't1', input: 'Ajo.', message: 'Ollama desligado.', retryable: true })
  })

  it('jogada com sucesso: texto chega aos poucos e a narração é adicionada', async () => {
    const store = await loadedStore()
    const seen = []
    api.playTurn.mockImplementation(async (campaignId, turnId, input, h) => {
      h.onTurn({ turn: turn(turnId, 'processing'), player_message: msg('m1', 1, 'player', input, turnId) })
      h.onDelta({ text: 'A porta ' })
      seen.push(store.streamingText)
      h.onDelta({ text: 'range.' })
      seen.push(store.streamingText)
      h.onDone({ turn: turn(turnId, 'completed'), narration_message: msg('m2', 2, 'narration', 'A porta range.', turnId) })
    })

    await store.send('Abro a porta.')

    expect(seen).toEqual(['A porta ', 'A porta range.'])
    expect(store.messages.map((m) => m.role)).toEqual(['player', 'narration'])
    expect(store.streaming).toBe(false)
    expect(store.streamingText).toBe('')
  })

  it('falha da IA vira failure e repetir usa o MESMO turn_id', async () => {
    const store = await loadedStore()
    api.playTurn.mockImplementationOnce(async (cid, turnId, input, h) => {
      h.onTurn({ turn: turn(turnId, 'processing'), player_message: msg('m1', 1, 'player', input, turnId) })
      h.onError({ turn: turn(turnId, 'failed'), message: 'Ollama desligado.', retryable: true })
    })
    await store.send('Corro.')
    const failedTurnId = store.failure.turnId
    expect(store.failure.message).toBe('Ollama desligado.')

    api.playTurn.mockImplementationOnce(async (cid, turnId, input, h) => {
      h.onTurn({ turn: turn(turnId, 'processing'), player_message: msg('m1', 1, 'player', input, turnId) })
      h.onDone({ turn: turn(turnId, 'completed'), narration_message: msg('m2', 2, 'narration', 'Ok.', turnId) })
    })
    await store.retry()

    expect(api.playTurn.mock.calls[1][1]).toBe(failedTurnId)
    expect(api.playTurn.mock.calls[1][2]).toBe('Corro.')
    expect(store.failure).toBeNull()
    expect(store.messages).toHaveLength(2) // a mensagem do jogador não duplica
  })

  it('stream que termina sem "done" nem "error" vira falha repetível', async () => {
    const store = await loadedStore()
    api.playTurn.mockImplementation(async (cid, turnId, input, h) => {
      h.onDelta({ text: 'meio' })
    })
    await store.send('Algo.')
    expect(store.failure.message).toBe(STREAM_CUT_MESSAGE)
    expect(store.failure.retryable).toBe(true)
  })

  it('pedido recusado pelo servidor (409) vira aviso, não falha de jogada', async () => {
    const store = await loadedStore()
    api.playTurn.mockRejectedValue(new ApiError('Já existe uma jogada em andamento.', 409))
    await store.send('Algo.')
    expect(store.notice).toBe('Já existe uma jogada em andamento.')
    expect(store.failure).toBeNull()
  })

  it('avisos do motor entram no chat em ordem e a ficha é atualizada', async () => {
    const store = await loadedStore()
    const sheet = { name: 'Kael', attributes: [], skills: [], items: [] }
    api.getSheet.mockResolvedValue({ character: sheet, world_time: 'dia 1, 08:00' })
    api.playTurn.mockImplementation(async (cid, turnId, input, h) => {
      h.onTurn({ turn: turn(turnId, 'processing'), player_message: msg('m1', 1, 'player', input, turnId) })
      h.onMechanics({ messages: [msg('m2', 2, 'system', '[SISTEMA] Personagem criado: Kael.', turnId)] })
      h.onDone({ turn: turn(turnId, 'completed'), narration_message: msg('m3', 3, 'narration', 'Era uma vez.', turnId) })
    })
    await store.send('Começo.')
    await Promise.resolve()
    expect(store.messages.map((m) => m.role)).toEqual(['player', 'system', 'narration'])
    expect(store.character).toEqual(sheet)
  })

  it('não inicia duas jogadas ao mesmo tempo', async () => {
    const store = await loadedStore()
    let release
    api.playTurn.mockImplementation(() => new Promise((resolve) => (release = resolve)))
    const first = store.send('Um.')
    await store.send('Dois.')
    release()
    await first
    expect(api.playTurn).toHaveBeenCalledTimes(1)
  })
})

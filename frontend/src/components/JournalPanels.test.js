import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import JournalPanels from './JournalPanels.vue'

const journal = {
  map: {
    current: { id: 't', name: 'Torre', present: [{ name: 'Mira', kind: 'character', status: '' }],
               items: [{ key: 'pedra', name: 'Pedra', quantity: 2 }] },
    places: [{ id: 'v', name: 'Vila', current: false, description: '' }, { id: 't', name: 'Torre', current: true, description: '' }],
  },
  diary: [{ kind: 'summary', turn: 3, from_turn: 1, text: 'Kael subiu à torre.' }],
  bonds: [{ name: 'Mira', labels: ['aliada'], dimensions: { confianca: 10 } }],
}

describe('JournalPanels', () => {
  it('mapa mostra o local atual, quem está lá e os lugares visitados', () => {
    const text = mount(JournalPanels, { props: { view: 'map', journal } }).text()
    expect(text).toContain('Você está em: Torre')
    expect(text).toContain('À vista: Mira')
    expect(text).toContain('Pedra ×2')
    expect(text).toContain('Vila')
  })

  it('diário mostra os resumos com o intervalo de turnos', () => {
    const text = mount(JournalPanels, { props: { view: 'diary', journal } }).text()
    expect(text).toContain('Turnos 1–3')
    expect(text).toContain('Kael subiu à torre.')
  })

  it('laços mostram só as relações do protagonista', () => {
    const text = mount(JournalPanels, { props: { view: 'bonds', journal } }).text()
    expect(text).toContain('Mira')
    expect(text).toContain('aliada')
    expect(text).toContain('confianca 10')
  })
})

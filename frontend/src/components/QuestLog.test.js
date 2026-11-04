import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import QuestLog from './QuestLog.vue'

describe('QuestLog', () => {
  it('lista missões ativas primeiro, com objetivos marcados', () => {
    const wrapper = mount(QuestLog, {
      props: {
        quests: [
          { key: 'a', title: 'Antiga', kind: 'side', status: 'completed', objectives: [] },
          { key: 'b', title: 'Mapas perdidos', kind: 'main', status: 'active',
            objectives: [{ text: 'Falar com o pescador', done: true }, { text: 'Achar o farol', done: false }] },
        ],
      },
    })
    const titles = wrapper.findAll('.quest-title span:first-child').map((s) => s.text())
    expect(titles).toEqual(['Mapas perdidos', 'Antiga'])
    expect(wrapper.find('.objectives .done').text()).toContain('Falar com o pescador')
    expect(wrapper.text()).toContain('Concluída')
  })

  it('sem missões mostra aviso', () => {
    expect(mount(QuestLog).text()).toContain('Nenhuma missão ainda.')
  })
})

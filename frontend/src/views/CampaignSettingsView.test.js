import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api/campaigns.js'
import CampaignSettingsView from './CampaignSettingsView.vue'

vi.mock('../api/campaigns.js', () => ({ getSettings: vi.fn(), saveSettings: vi.fn() }))

const VIEW = {
  experience: { ai_model: null, creativity: null, mechanics: null, simulation: null, summary_every: null,
                show_dice: true, system_window: true },
  content: { intensity: 2, categories: {} },
  defaults: { ai_model: 'qwen2.5:1.5b', creativity: 0.8, mechanics: true, summary_every: 8 },
  content_categories: { violencia: 'Violência', horror: 'Horror' },
  provider: { name: 'ollama', content_note: 'Depende do modelo.' },
  rules: [{ kind: 'attribute', key: 'vida', name: 'Vida', version: 1 }],
  versions: { experience: 0, content: 0 },
}

const stubs = { RouterLink: { template: '<a><slot /></a>' } }

beforeEach(() => vi.clearAllMocks())

describe('CampaignSettingsView', () => {
  it('mostra padrões, categorias e regras atuais', async () => {
    api.getSettings.mockResolvedValue(VIEW)
    const wrapper = mount(CampaignSettingsView, { props: { id: 'c1' }, global: { stubs } })
    await flushPromises()
    expect(wrapper.text()).toContain('qwen2.5:1.5b')
    expect(wrapper.text()).toContain('Horror')
    expect(wrapper.text()).toContain('Vida')
    expect(wrapper.text()).toContain('Depende do modelo.')
  })

  it('salva experiência e conteúdo e mostra os avisos de impacto', async () => {
    api.getSettings.mockResolvedValue(VIEW)
    api.saveSettings.mockResolvedValue({ ...VIEW, warnings: ['Sem o motor de regras...'] })
    const wrapper = mount(CampaignSettingsView, { props: { id: 'c1' }, global: { stubs } })
    await flushPromises()
    await wrapper.find('#mechanics').setValue('false')
    await wrapper.find('#cat-horror').setValue('3')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const [id, payload] = api.saveSettings.mock.calls[0]
    expect(id).toBe('c1')
    expect(payload.content.categories).toEqual({ horror: 3 })
    expect(wrapper.text()).toContain('Sem o motor de regras...')
  })
})

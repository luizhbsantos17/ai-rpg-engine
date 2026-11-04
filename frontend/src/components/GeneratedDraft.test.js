import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import GeneratedDraft from './GeneratedDraft.vue'

const draft = { id: 'd1', title: 'A Cidade de Vidro', genre_tags: ['mistério'], premise: 'Você acorda...', secrets_count: 3 }

describe('GeneratedDraft', () => {
  it('mostra a introdução e só a QUANTIDADE de segredos', () => {
    const wrapper = mount(GeneratedDraft, { props: { draft } })
    expect(wrapper.text()).toContain('A Cidade de Vidro')
    expect(wrapper.text()).toContain('Você acorda...')
    expect(wrapper.text()).toContain('3 segredo(s)')
  })

  it('gerar de novo envia os campos marcados para manter', async () => {
    const wrapper = mount(GeneratedDraft, { props: { draft } })
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(true) // título
    await checkboxes[2].setValue(true) // premissa
    await wrapper.findAll('button').find((b) => b.text() === 'Gerar de novo').trigger('click')
    expect(wrapper.emitted('regenerate')[0]).toEqual([['title', 'premise']])
  })

  it('editar e salvar envia os ajustes', async () => {
    const wrapper = mount(GeneratedDraft, { props: { draft } })
    await wrapper.findAll('button').find((b) => b.text() === 'Editar').trigger('click')
    await wrapper.find('#draft-title').setValue('Meu Título')
    await wrapper.find('#draft-tags').setValue('horror, mistério')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('save')[0][0]).toEqual({
      title: 'Meu Título', premise: 'Você acorda...', genre_tags: ['horror', 'mistério'],
    })
  })
})

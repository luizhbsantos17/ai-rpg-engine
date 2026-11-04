import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import NarrationBlock from './NarrationBlock.vue'

describe('NarrationBlock', () => {
  it('divide o texto em parágrafos', () => {
    const wrapper = mount(NarrationBlock, { props: { text: 'Primeiro.\n\nSegundo.' } })
    expect(wrapper.findAll('p').map((p) => p.text())).toEqual(['Primeiro.', 'Segundo.'])
  })

  it('nunca interpreta o texto da IA como HTML', () => {
    const wrapper = mount(NarrationBlock, { props: { text: '<img src=x onerror="alert(1)"> olá' } })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('<img src=x onerror="alert(1)"> olá')
  })

  it('mostra o cursor enquanto o texto está chegando', () => {
    const wrapper = mount(NarrationBlock, { props: { text: 'Era', streaming: true } })
    expect(wrapper.find('.caret').exists()).toBe(true)
  })
})

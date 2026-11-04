import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import CharacterSheet from './CharacterSheet.vue'

const character = {
  name: 'Kael',
  status: 'active',
  location: 'Vila Costeira',
  attributes: [
    { key: 'vida', name: 'Vida', resource: true, value: '15', max: '20', description: '' },
    { key: 'forca', name: 'Força', resource: false, value: '5', max: null, description: '' },
  ],
  skills: [{ key: 'ventos', name: 'Leitura de Ventos', level: 2, max_level: null, description: '' }],
  items: [{ id: 'i1', key: 'bussola', name: 'Bússola', quantity: 1, description: '' }],
}

describe('CharacterSheet', () => {
  it('sem personagem mostra aviso', () => {
    expect(mount(CharacterSheet).text()).toContain('A ficha aparece quando a história começar.')
  })

  it('mostra recursos como barra proporcional, atributos, habilidades e itens', () => {
    const wrapper = mount(CharacterSheet, { props: { character } })
    expect(wrapper.text()).toContain('Kael')
    expect(wrapper.text()).toContain('15 / 20')
    expect(wrapper.find('.fill').attributes('style')).toContain('width: 75%')
    expect(wrapper.find('dl').text()).toContain('Força')
    expect(wrapper.text()).toContain('Leitura de Ventos')
    expect(wrapper.text()).toContain('Bússola')
  })

  it('separa o equipamento do inventário e mostra classe e raça', () => {
    const equippedCharacter = {
      ...character,
      class: 'guerreiro',
      race: 'anão',
      items: [
        ...character.items,
        { id: 'i2', key: 'cota', name: 'Cota de malha', quantity: 1, description: '', equipped_slot: 'corpo',
          bonus: { defesa: 2, estilo: 'pesado' } },
      ],
    }
    const wrapper = mount(CharacterSheet, { props: { character: equippedCharacter } })
    expect(wrapper.find('.identity').text()).toBe('anão · guerreiro')
    const blocks = wrapper.findAll('section.block')
    const titled = (title) => blocks.find((b) => b.find('h3').exists() && b.find('h3').text() === title)
    const equipment = titled('Equipamento')
    const inventory = titled('Inventário')
    expect(equipment.text()).toContain('Cota de malha')
    expect(equipment.text()).toContain('+2 defesa, estilo pesado')
    expect(equipment.text()).toContain('corpo')
    expect(inventory.text()).toContain('Bússola')
    expect(inventory.text()).not.toContain('Cota de malha')
  })

  it('sem nada equipado, não mostra a seção de equipamento', () => {
    const wrapper = mount(CharacterSheet, { props: { character } })
    expect(wrapper.findAll('h3').map((h) => h.text())).not.toContain('Equipamento')
    expect(wrapper.find('.identity').exists()).toBe(false)
  })

  it('mostra o tempo do mundo e os efeitos ativos', () => {
    const withEffect = { ...character, effects: [{ key: 'veneno', name: 'Envenenado', ends: 'dia 1, 10:00', description: '' }] }
    const wrapper = mount(CharacterSheet, { props: { character: withEffect, worldTime: 'dia 1, 08:00' } })
    expect(wrapper.find('.world-time').text()).toBe('dia 1, 08:00')
    expect(wrapper.text()).toContain('Envenenado')
    expect(wrapper.text()).toContain('até dia 1, 10:00')
  })

  it('números enormes não quebram a barra', () => {
    const big = { ...character, attributes: [{ ...character.attributes[0], value: '1E+40', max: 'abc' }] }
    const wrapper = mount(CharacterSheet, { props: { character: big } })
    expect(wrapper.find('.fill').attributes('style')).toContain('width: 0%')
  })
})

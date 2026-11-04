import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import KnownCharacters from './KnownCharacters.vue'

describe('KnownCharacters', () => {
  it('mostra só o que o protagonista sabe, com o nível de cada informação', () => {
    const wrapper = mount(KnownCharacters, {
      props: {
        characters: [{ id: 'v', name: 'Viajante', kind: 'character', facts: [
          { field: 'identity', value: 'um mercador comum', level: 'confirmed' },
          { field: 'forca', value: '≈10', level: 'estimated' },
          { field: 'ouro', value: null, level: 'unknown' },
        ] }],
      },
    })
    const text = wrapper.text()
    expect(text).toContain('Viajante')
    expect(text).toContain('identidade')
    expect(text).toContain('um mercador comum')
    expect(text).toContain('estimado')
    expect(text).toContain('???')
  })

  it('sem conhecimento mostra aviso', () => {
    expect(mount(KnownCharacters).text()).toContain('Você ainda não sabe nada')
  })
})

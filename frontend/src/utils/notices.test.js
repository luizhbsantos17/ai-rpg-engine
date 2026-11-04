import { describe, expect, it } from 'vitest'

import { parseNotice } from './notices.js'

describe('parseNotice', () => {
  it('separa a etiqueta do texto', () => {
    expect(parseNotice('[TESTE] Saltar: 12 + 3 = 15 → sucesso.')).toEqual({
      tag: 'TESTE',
      text: 'Saltar: 12 + 3 = 15 → sucesso.',
      tone: 'info',
    })
  })

  it('alertas têm tom de alerta', () => {
    expect(parseNotice('[ALERTA] Você morreu.').tone).toBe('alert')
  })

  it('texto sem etiqueta vira [SISTEMA]', () => {
    expect(parseNotice('Aviso solto')).toEqual({ tag: 'SISTEMA', text: 'Aviso solto', tone: 'info' })
  })
})

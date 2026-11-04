import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api/campaigns.js'
import { ApiError } from '../api/client.js'
import { isAdminCommand, useAdminStore } from './admin.js'

vi.mock('../api/campaigns.js', () => ({ adminLogin: vi.fn(), runAdminCommand: vi.fn() }))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('admin store', () => {
  it('só textos que COMEÇAM com /admin ou /debug são comandos', () => {
    expect(isAdminCommand('/admin help')).toBe(true)
    expect(isAdminCommand('  /debug show_events')).toBe(true)
    expect(isAdminCommand('Eu digo /admin em voz alta')).toBe(false)
    expect(isAdminCommand('/administrar')).toBe(false)
  })

  it('pede a senha uma vez e mostra a saída no console', async () => {
    api.adminLogin.mockResolvedValue('tok')
    api.runAdminCommand.mockResolvedValue({ ok: true, lines: ['Kael (character)'] })
    const store = useAdminStore()
    const ask = vi.fn(() => 'senha')
    await store.run('c1', '/admin status', ask)
    await store.run('c1', '/admin status', ask)
    expect(ask).toHaveBeenCalledTimes(1)
    expect(api.runAdminCommand).toHaveBeenCalledWith('c1', 'tok', '/admin status')
    expect(store.log).toHaveLength(2)
    expect(store.log[0]).toEqual({ command: '/admin status', ok: true, lines: ['Kael (character)'] })
  })

  it('sessão expirada pede a senha de novo e repete o comando', async () => {
    api.adminLogin.mockResolvedValueOnce('velho').mockResolvedValueOnce('novo')
    api.runAdminCommand
      .mockResolvedValueOnce({ ok: true, lines: ['a'] })
      .mockRejectedValueOnce(new ApiError('Sessão expirada', 401))
      .mockResolvedValueOnce({ ok: true, lines: ['b'] })
    const store = useAdminStore()
    await store.run('c1', '/admin help', () => 'senha')
    await store.run('c1', '/admin help', () => 'senha')
    expect(store.token).toBe('novo')
    expect(store.log.map((e) => e.lines[0])).toEqual(['a', 'b'])
  })

  it('cancelar a senha não executa nada', async () => {
    const store = useAdminStore()
    await store.run('c1', '/admin help', () => null)
    expect(api.runAdminCommand).not.toHaveBeenCalled()
  })
})

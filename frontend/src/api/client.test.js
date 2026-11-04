import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, NETWORK_ERROR, request } from './client.js'

afterEach(() => vi.unstubAllGlobals())

const jsonResponse = (status, body) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('request', () => {
  it('envia JSON e devolve a resposta', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(201, { campaign: { id: 'c1' } }))
    vi.stubGlobal('fetch', fetchMock)
    const result = await request('POST', '/api/campaigns', { title: 'T' })
    expect(result).toEqual({ campaign: { id: 'c1' } })
    const [, options] = fetchMock.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'T' })
  })

  it('transforma o erro do servidor em ApiError com a mensagem dele', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse(409, { error: { message: 'Jogada em andamento.' } })),
    )
    await expect(request('GET', '/api/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 409,
      message: 'Jogada em andamento.',
    })
  })

  it('servidor desligado vira ApiError com status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const error = await request('GET', '/api/x').catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(0)
    expect(error.message).toBe(NETWORK_ERROR)
  })

  it('204 devolve null', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    expect(await request('DELETE', '/api/x', {})).toBeNull()
  })
})

import { describe, expect, it } from 'vitest'

import { createSSEParser, readSSEStream } from './sse.js'

function collect() {
  const events = []
  return { events, parser: createSSEParser((e) => events.push(e)) }
}

describe('createSSEParser', () => {
  it('entrega eventos completos com JSON', () => {
    const { events, parser } = collect()
    parser.feed('event: delta\ndata: {"text":"Olá"}\n\nevent: done\ndata: {"ok":true}\n\n')
    expect(events).toEqual([
      { event: 'delta', data: { text: 'Olá' } },
      { event: 'done', data: { ok: true } },
    ])
  })

  it('junta eventos cortados entre pedaços', () => {
    const { events, parser } = collect()
    parser.feed('event: del')
    parser.feed('ta\ndata: {"te')
    expect(events).toEqual([])
    parser.feed('xt":"a"}\n')
    parser.feed('\n')
    expect(events).toEqual([{ event: 'delta', data: { text: 'a' } }])
  })

  it('aceita quebras de linha do Windows (CRLF)', () => {
    const { events, parser } = collect()
    parser.feed('event: turn\r\ndata: {"n":1}\r\n\r\n')
    expect(events).toEqual([{ event: 'turn', data: { n: 1 } }])
  })

  it('flush entrega um último evento sem linha em branco final', () => {
    const { events, parser } = collect()
    parser.feed('event: done\ndata: {"x":1}')
    parser.flush()
    expect(events).toEqual([{ event: 'done', data: { x: 1 } }])
  })
})

describe('readSSEStream', () => {
  it('lê bytes UTF-8 de um stream, inclusive acentos partidos entre pedaços', async () => {
    const bytes = new TextEncoder().encode('event: delta\ndata: {"text":"ação"}\n\n')
    const cut = bytes.indexOf(0xc3) + 1 // corta no meio do "ç"
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(bytes.slice(0, cut))
        controller.enqueue(bytes.slice(cut))
        controller.close()
      },
    })
    const events = []
    await readSSEStream(stream, (e) => events.push(e))
    expect(events).toEqual([{ event: 'delta', data: { text: 'ação' } }])
  })
})

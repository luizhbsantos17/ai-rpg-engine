// Leitor de Server-Sent Events (SSE).
// O navegador recebe o texto em pedaços que podem cortar um evento no meio;
// o parser junta os pedaços e só entrega eventos completos.

export function createSSEParser(onEvent) {
  let buffer = ''

  function emit(block) {
    let event = 'message'
    const dataLines = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
    }
    if (dataLines.length === 0) return
    const raw = dataLines.join('\n')
    let data
    try {
      data = JSON.parse(raw)
    } catch {
      data = raw
    }
    onEvent({ event, data })
  }

  return {
    feed(chunk) {
      buffer += chunk.replace(/\r\n/g, '\n')
      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        if (block.trim()) emit(block)
        boundary = buffer.indexOf('\n\n')
      }
    },
    flush() {
      if (buffer.trim()) emit(buffer)
      buffer = ''
    },
  }
}

// Lê um ReadableStream de bytes (corpo de um fetch) e chama onEvent a cada evento.
export async function readSSEStream(stream, onEvent) {
  const reader = stream.getReader()
  const decoder = new TextDecoder('utf-8')
  const parser = createSSEParser(onEvent)
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    parser.feed(decoder.decode(value, { stream: true }))
  }
  parser.feed(decoder.decode())
  parser.flush()
}

// Chamadas HTTP ao backend. Erros viram ApiError com a mensagem enviada pelo servidor.

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

const NETWORK_ERROR = 'Não foi possível falar com o servidor. Ele está ligado?'

export async function readError(response) {
  let message = `Erro ${response.status}`
  let details = null
  try {
    const body = await response.json()
    if (body?.error?.message) message = body.error.message
    details = body?.error?.details ?? null
  } catch {
    // corpo não é JSON: fica a mensagem genérica
  }
  return new ApiError(message, response.status, details)
}

export async function request(method, path, body) {
  let response
  try {
    response = await fetch(path, {
      method,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(NETWORK_ERROR, 0)
  }
  if (!response.ok) throw await readError(response)
  if (response.status === 204) return null
  return response.json()
}

export { NETWORK_ERROR }

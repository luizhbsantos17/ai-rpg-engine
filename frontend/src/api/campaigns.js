import { ApiError, NETWORK_ERROR, readError, request } from './client.js'
import { readSSEStream } from './sse.js'

export const listCampaigns = () => request('GET', '/api/campaigns').then((r) => r.campaigns)

export const createCampaign = (data) => request('POST', '/api/campaigns', data).then((r) => r.campaign)

export const getHistory = (campaignId) => request('GET', `/api/campaigns/${campaignId}/history`)

export const deleteCampaign = (campaignId, confirmTitle) =>
  request('DELETE', `/api/campaigns/${campaignId}`, { confirm_title: confirmTitle })

// Joga um turno. `handlers` recebe: onTurn, onDelta, onDone, onError (eventos do servidor).
// Erros antes do stream (campanha inexistente, texto vazio...) são lançados como ApiError.
export async function playTurn(campaignId, turnId, input, handlers) {
  let response
  try {
    response = await fetch(`/api/campaigns/${campaignId}/turns`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ turn_id: turnId, input }),
    })
  } catch {
    throw new ApiError(NETWORK_ERROR, 0)
  }
  if (!response.ok) throw await readError(response)

  const routes = {
    turn: handlers.onTurn,
    delta: handlers.onDelta,
    done: handlers.onDone,
    error: handlers.onError,
  }
  await readSSEStream(response.body, ({ event, data }) => routes[event]?.(data))
}

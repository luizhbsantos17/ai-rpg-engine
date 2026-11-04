// Mensagens de sistema chegam como "[TAG] texto"; a interface mostra a etiqueta separada.
const TONES = { ALERTA: 'alert', FALHA: 'error', ERRO: 'error' }

export function parseNotice(content) {
  const match = /^\[([A-ZÀ-Ú]+)\]\s*(.*)$/s.exec(content ?? '')
  const tag = match ? match[1] : 'SISTEMA'
  return { tag, text: match ? match[2] : content ?? '', tone: TONES[tag] ?? 'info' }
}

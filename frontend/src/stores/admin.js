// Console do modo administrador: separado da história (comandos nunca viram fala nem vão para a IA).
import { defineStore } from 'pinia'

import * as api from '../api/campaigns.js'

export const ADMIN_PREFIXES = ['/admin', '/debug']

export function isAdminCommand(text) {
  const t = (text ?? '').trimStart()
  return ADMIN_PREFIXES.some((p) => t === p || t.startsWith(`${p} `))
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    token: null, // só na memória da página: fechar o navegador encerra a sessão
    log: [], // [{ command, ok, lines }]
    busy: false,
  }),
  actions: {
    // askPassword: função que devolve a senha digitada (ou null se o jogador cancelar)
    async run(campaignId, command, askPassword) {
      this.busy = true
      try {
        if (!this.token && !(await this.login(askPassword))) return
        let result
        try {
          result = await api.runAdminCommand(campaignId, this.token, command)
        } catch (err) {
          if (err.status !== 401) throw err
          this.token = null // sessão expirou: pede a senha de novo e tenta uma vez
          if (!(await this.login(askPassword))) return
          result = await api.runAdminCommand(campaignId, this.token, command)
        }
        this.log.push({ command, ok: result.ok, lines: result.lines })
      } catch (err) {
        this.log.push({ command, ok: false, lines: [err.message] })
      } finally {
        this.busy = false
      }
    },

    async login(askPassword) {
      const password = askPassword()
      if (!password) return false
      try {
        this.token = await api.adminLogin(password)
        return true
      } catch (err) {
        this.log.push({ command: 'login', ok: false, lines: [err.message] })
        return false
      }
    },

    clear() {
      this.log = []
    },
  },
})

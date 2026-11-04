import { defineStore } from 'pinia'

import * as api from '../api/campaigns.js'

export const useCampaignsStore = defineStore('campaigns', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),
  actions: {
    async fetch() {
      this.loading = true
      this.error = null
      try {
        this.items = await api.listCampaigns()
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async create(data) {
      const campaign = await api.createCampaign(data)
      this.items = [campaign, ...this.items.filter((c) => c.id !== campaign.id)]
      return campaign
    },
    async importFile(file) {
      let snapshot
      try {
        snapshot = JSON.parse(await file.text())
      } catch {
        throw new Error('O arquivo não é um JSON válido.')
      }
      const campaign = await api.importCampaign(snapshot)
      this.items = [campaign, ...this.items]
      return campaign
    },
    async remove(campaignId, confirmTitle) {
      await api.deleteCampaign(campaignId, confirmTitle)
      this.items = this.items.filter((c) => c.id !== campaignId)
    },
  },
})

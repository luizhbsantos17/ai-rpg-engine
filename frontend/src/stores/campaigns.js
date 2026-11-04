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
    async remove(campaignId, confirmTitle) {
      await api.deleteCampaign(campaignId, confirmTitle)
      this.items = this.items.filter((c) => c.id !== campaignId)
    },
  },
})

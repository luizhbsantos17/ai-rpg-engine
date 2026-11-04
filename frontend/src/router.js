import { createRouter, createWebHistory } from 'vue-router'

import CampaignListView from './views/CampaignListView.vue'
import CampaignCreateView from './views/CampaignCreateView.vue'
import CampaignSettingsView from './views/CampaignSettingsView.vue'
import PlayView from './views/PlayView.vue'

export const routes = [
  { path: '/', name: 'campaigns', component: CampaignListView },
  { path: '/nova', name: 'new-campaign', component: CampaignCreateView },
  { path: '/campanha/:id', name: 'play', component: PlayView, props: true },
  { path: '/campanha/:id/configuracoes', name: 'settings', component: CampaignSettingsView, props: true },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <RouterLink to="/" class="brand">
        <span class="brand-sigil" aria-hidden="true">◆</span>
        <span class="brand-name">AI RPG Engine</span>
      </RouterLink>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, var(--bg-raised), transparent);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text);
  text-decoration: none;
  font-family: var(--font-display);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.95rem;
}

.brand-sigil {
  color: var(--accent);
  text-shadow: 0 0 12px var(--accent-glow);
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  padding: var(--space-5);
}

@media (max-width: 640px) {
  .app-main {
    padding: var(--space-3);
  }
}
</style>

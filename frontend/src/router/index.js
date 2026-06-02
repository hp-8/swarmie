import { createRouter, createWebHistory } from 'vue-router'

// Swarmie: fast founder-validation flow
// Home is eager so the landing page loads instantly.
// All other views are lazy-loaded to keep the initial bundle small.
import Home from '../views/Home.vue'

const routes = [
  // --- Swarmie primary flow ---
  { path: '/', name: 'Home', component: Home },
  { path: '/new', name: 'PitchInput', component: () => import('../views/swarm/PitchInput.vue') },
  { path: '/run/:jobId', name: 'Watching', component: () => import('../views/swarm/Watching.vue'), props: true },
  { path: '/result/:jobId', name: 'Result', component: () => import('../views/swarm/Result.vue'), props: true },

  // --- Legal ---
  { path: '/terms', name: 'Terms', component: () => import('../views/legal/Terms.vue') },
  { path: '/privacy', name: 'Privacy', component: () => import('../views/legal/Privacy.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

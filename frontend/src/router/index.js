import { createRouter, createWebHistory } from 'vue-router'

// Swarmie: fast founder-validation flow
import Home from '../views/Home.vue'
import PitchInput from '../views/swarm/PitchInput.vue'
import Watching from '../views/swarm/Watching.vue'
import Result from '../views/swarm/Result.vue'
import Terms from '../views/legal/Terms.vue'
import Privacy from '../views/legal/Privacy.vue'

const routes = [
  // --- Swarmie primary flow ---
  { path: '/', name: 'Home', component: Home },
  { path: '/new', name: 'PitchInput', component: PitchInput },
  { path: '/run/:jobId', name: 'Watching', component: Watching, props: true },
  { path: '/result/:jobId', name: 'Result', component: Result, props: true },

  // --- Legal ---
  { path: '/terms', name: 'Terms', component: Terms },
  { path: '/privacy', name: 'Privacy', component: Privacy },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

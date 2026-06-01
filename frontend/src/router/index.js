import { createRouter, createWebHistory } from 'vue-router'

// Swarmie: fast founder-validation flow
import Home from '../views/Home.vue'
import PitchInput from '../views/swarm/PitchInput.vue'
import Watching from '../views/swarm/Watching.vue'
import Result from '../views/swarm/Result.vue'
import Terms from '../views/legal/Terms.vue'
import Privacy from '../views/legal/Privacy.vue'

// Legacy MiroFish deep-simulation flow (kept functional, not surfaced).
import LegacyMain from '../views/MainView.vue'
import LegacySimulation from '../views/SimulationView.vue'
import LegacySimulationRun from '../views/SimulationRunView.vue'
import LegacyReport from '../views/ReportView.vue'
import LegacyInteraction from '../views/InteractionView.vue'

const routes = [
  // --- Swarmie primary flow ---
  { path: '/', name: 'Home', component: Home },
  { path: '/new', name: 'PitchInput', component: PitchInput },
  { path: '/run/:jobId', name: 'Watching', component: Watching, props: true },
  { path: '/result/:jobId', name: 'Result', component: Result, props: true },

  // --- Legal ---
  { path: '/terms', name: 'Terms', component: Terms },
  { path: '/privacy', name: 'Privacy', component: Privacy },

  // --- Legacy deep-sim flow (preserved; reachable but not promoted) ---
  { path: '/legacy/process/:projectId', name: 'LegacyProcess', component: LegacyMain, props: true },
  { path: '/legacy/simulation/:simulationId', name: 'LegacySimulation', component: LegacySimulation, props: true },
  { path: '/legacy/simulation/:simulationId/start', name: 'LegacySimulationRun', component: LegacySimulationRun, props: true },
  { path: '/legacy/report/:reportId', name: 'LegacyReport', component: LegacyReport, props: true },
  { path: '/legacy/interaction/:reportId', name: 'LegacyInteraction', component: LegacyInteraction, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

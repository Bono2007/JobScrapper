import { initSearch } from './tabs/search.js'
import { initResults, loadJobs } from './tabs/results.js'
import { initDetail } from './tabs/detail.js'

async function init() {
  const port = await window.api.getPort()
  window.__API_BASE__ = `http://127.0.0.1:${port}`

  initSearch()
  await initResults()  // await pour que loadSources() soit terminé
  initDetail()
  setupTabs()

  // Charger les offres existantes en base au démarrage
  await loadJobs()
}

function setupTabs() {
  const buttons = document.querySelectorAll('.tab-btn')
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'))
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'))
      btn.classList.add('active')
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active')
    })
  })
}

init()

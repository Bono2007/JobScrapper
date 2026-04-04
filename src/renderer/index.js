import { initSearch } from './tabs/search.js'
import { initResults, loadJobs, setFilters } from './tabs/results.js'

async function init() {
  const port = await window.api.getPort()
  window.__API_BASE__ = `http://127.0.0.1:${port}`

  initSearch()
  await initResults()
  setupSidebar()
  await loadJobs()
}

function setupSidebar() {
  // Navigation principale
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault()
      const tab = item.dataset.tab
      const source = item.dataset.source ?? ''
      const status = item.dataset.status ?? ''

      // Activer le nav-item cliqué
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'))
      item.classList.add('active')

      // Activer le panel correspondant
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'))
      const panel = document.getElementById(`tab-${tab}`)
      if (panel) panel.classList.add('active')

      if (tab === 'results') {
        setFilters({ status, source })
      }
    })
  })

  // Dark/light toggle
  const themeToggle = document.getElementById('theme-toggle')
  const savedTheme = localStorage.getItem('theme') || 'dark'
  document.documentElement.setAttribute('data-theme', savedTheme)
  themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙'

  themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme')
    const next = current === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', next)
    localStorage.setItem('theme', next)
    themeToggle.textContent = next === 'dark' ? '☀️' : '🌙'
  })

  // Actions sidebar footer : export CSV et vider la base
  document.getElementById('sb-export')?.addEventListener('click', async () => {
    const status = document.getElementById('r-status')?.value || ''
    const source = document.getElementById('r-source')?.value || ''
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (source) params.set('source', source)
    const url = `${window.__API_BASE__}/export?${params}`
    const result = await window.api.saveCsv(url)
    if (result.saved) alert(`Fichier sauvegardé : ${result.filePath}`)
  })

  document.getElementById('sb-clear')?.addEventListener('click', async () => {
    if (!confirm('Vider toute la base de données ?')) return
    await fetch(`${window.__API_BASE__}/admin/clear`, { method: 'POST' })
    loadJobs()
  })
}

init()

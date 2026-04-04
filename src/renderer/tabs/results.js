import { switchTab } from '../router.js'
import { loadDetail } from './detail.js'
import { escapeHtml } from '../utils/html.js'

let currentJobs = []

export async function initResults() {
  const panel = document.getElementById('tab-results')
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h2 style="font-size:18px;">Résultats <span id="r-count" style="font-size:14px;color:#6e6e73;"></span></h2>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-secondary btn-sm" id="r-export">Exporter CSV</button>
        <button class="btn btn-secondary btn-sm" id="r-clear">Vider la base</button>
      </div>
    </div>
    <div class="filters">
      <input id="r-search" type="text" placeholder="Rechercher dans les offres…" style="flex:1;min-width:200px;">
      <select id="r-status">
        <option value="">Tous les statuts</option>
        <option value="new">Nouveau</option>
        <option value="seen">Vu</option>
        <option value="interested">Intéressé</option>
        <option value="rejected">Rejeté</option>
      </select>
      <select id="r-source">
        <option value="">Toutes les sources</option>
      </select>
    </div>
    <ul class="job-list" id="r-list"></ul>
  `

  document.getElementById('r-search').addEventListener('input', () => renderList())
  document.getElementById('r-status').addEventListener('change', () => loadJobs())
  document.getElementById('r-source').addEventListener('change', () => loadJobs())
  document.getElementById('r-export').addEventListener('click', handleExport)
  document.getElementById('r-clear').addEventListener('click', handleClear)

  await loadSources()  // await ici pour que les sources soient chargées avant loadJobs()
}

export async function loadJobs() {
  const status = document.getElementById('r-status')?.value || ''
  const source = document.getElementById('r-source')?.value || ''
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (source) params.set('source', source)
  try {
    const res = await fetch(`${window.__API_BASE__}/jobs?${params}`)
    currentJobs = await res.json()
    renderList()
    updateCount()
  } catch (err) {
    console.error('[loadJobs]', err)
    const list = document.getElementById('r-list')
    if (list) list.innerHTML = '<li style="padding:20px;text-align:center;color:#c00">Erreur de connexion au backend.</li>'
  }
}

function renderList() {
  const query = document.getElementById('r-search')?.value.toLowerCase() || ''
  const filtered = query
    ? currentJobs.filter(j =>
        j.title.toLowerCase().includes(query) ||
        j.company.toLowerCase().includes(query) ||
        j.location.toLowerCase().includes(query)
      )
    : currentJobs

  const list = document.getElementById('r-list')
  if (!list) return

  if (filtered.length === 0) {
    list.innerHTML = '<li style="padding:20px;text-align:center;color:#6e6e73;">Aucune offre</li>'
    return
  }

  list.innerHTML = filtered.map(job => `
    <li class="job-item" data-id="${job.offer_id}">
      <div>
        <div class="job-title">${escapeHtml(job.title)}</div>
        <div class="job-meta">${escapeHtml(job.company)} — ${escapeHtml(job.location)}</div>
        <div class="job-meta">${escapeHtml(job.source_site)}${job.published_date ? ' · ' + job.published_date : ''}</div>
      </div>
      <span class="badge badge-${job.status}">${labelStatus(job.status)}</span>
    </li>
  `).join('')

  list.querySelectorAll('.job-item').forEach(item => {
    item.addEventListener('click', () => {
      loadDetail(item.dataset.id)
      switchTab('detail')
    })
  })
}

function updateCount() {
  const el = document.getElementById('r-count')
  if (el) el.textContent = `(${currentJobs.length})`
  const badge = document.getElementById('results-count')
  if (badge) badge.textContent = currentJobs.length > 0 ? `(${currentJobs.length})` : ''
}

async function loadSources() {
  try {
    const res = await fetch(`${window.__API_BASE__}/sources`)
    const srcs = await res.json()
    const select = document.getElementById('r-source')
    if (!select) return
    srcs.forEach(s => {
      const opt = document.createElement('option')
      opt.value = s
      opt.textContent = s
      select.appendChild(opt)
    })
  } catch (err) {
    console.error('[loadSources]', err)
  }
}

async function handleExport() {
  const status = document.getElementById('r-status')?.value || ''
  const source = document.getElementById('r-source')?.value || ''
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (source) params.set('source', source)
  const url = `${window.__API_BASE__}/export?${params}`
  const result = await window.api.saveCsv(url)
  if (result.saved) {
    alert(`Fichier sauvegardé : ${result.filePath}`)
  }
}

async function handleClear() {
  if (!confirm('Vider toute la base de données ?')) return
  await fetch(`${window.__API_BASE__}/admin/clear`, { method: 'POST' })
  currentJobs = []
  renderList()
  updateCount()
}

export function labelStatus(status) {
  return { new: 'Nouveau', seen: 'Vu', interested: 'Intéressé', rejected: 'Rejeté' }[status] || status
}


import { escapeHtml } from '../utils/html.js'

let currentJobs = []
let _status = ''
let _source = ''

export function setFilters({ status = '', source = '' } = {}) {
  _status = status
  _source = source
  loadJobs()
}

function isCorbeille() {
  return _status === 'rejected'
}

export async function initResults() {
  const panel = document.getElementById('tab-results')
  panel.innerHTML = `
    <div class="results-header">
      <h2 class="page-title">Résultats <span id="r-count" style="font-size:14px;font-weight:400;color:var(--text-muted);"></span></h2>
    </div>
    <div class="filters">
      <input id="r-search" type="text" placeholder="Rechercher dans les offres…">
      <select id="r-source">
        <option value="">Toutes les sources</option>
      </select>
    </div>
    <ul class="job-list" id="r-list"></ul>
  `

  document.getElementById('r-search').addEventListener('input', () => renderList())
  document.getElementById('r-source').addEventListener('change', (e) => {
    _source = e.target.value
    loadJobs()
  })

  await loadSources()
}

export async function loadJobs() {
  const params = new URLSearchParams()
  if (_status) params.set('status', _status)
  if (_source) params.set('source', _source)

  // Sync source select with current filter
  const sourceSelect = document.getElementById('r-source')
  if (sourceSelect) sourceSelect.value = _source

  try {
    const res = await fetch(`${window.__API_BASE__}/jobs?${params}`)
    currentJobs = await res.json()
    renderList()
    updateCount()
    const allRes = await fetch(`${window.__API_BASE__}/jobs`)
    updateSidebarSites(await allRes.json())
  } catch (err) {
    console.error('[loadJobs]', err)
    const list = document.getElementById('r-list')
    if (list) list.innerHTML = '<li style="padding:20px;text-align:center;color:var(--red)">Erreur de connexion au backend.</li>'
  }
}

function renderList() {
  const query = document.getElementById('r-search')?.value.toLowerCase() || ''

  const visible = isCorbeille()
    ? currentJobs
    : currentJobs.filter(j => j.status !== 'rejected')

  const filtered = query
    ? visible.filter(j =>
        j.title.toLowerCase().includes(query) ||
        j.company.toLowerCase().includes(query) ||
        j.location.toLowerCase().includes(query)
      )
    : visible

  const list = document.getElementById('r-list')
  if (!list) return

  if (filtered.length === 0) {
    list.innerHTML = '<li style="padding:20px;text-align:center;color:var(--text-muted);">Aucune offre</li>'
    return
  }

  const corbeille = isCorbeille()

  list.innerHTML = filtered.map(job => `
    <li class="job-item" data-id="${job.offer_id}">
      <div class="job-item-summary">
        <div class="job-item-info">
          <div class="job-title">${escapeHtml(job.title)}</div>
          <div class="job-meta">${escapeHtml(job.company)} — ${escapeHtml(job.location)}</div>
          <div class="job-meta">${escapeHtml(job.source_site)}${job.published_date ? ' · ' + job.published_date : ''}</div>
        </div>
        <span class="badge badge-${job.status}">${labelStatus(job.status)}</span>
      </div>
      <div class="job-item-expanded hidden">
        ${job.description
          ? `<div class="job-expand-desc">${escapeHtml(job.description)}</div>`
          : `<p class="job-expand-nodesc">Pas de description disponible. <a class="job-expand-link" href="#" data-url="${escapeHtml(job.url)}">Voir l'offre ↗</a></p>`
        }
        <div class="job-expand-actions">
          ${corbeille
            ? `<button class="btn btn-secondary btn-sm action-restore" data-id="${job.offer_id}">Restaurer</button>
               <button class="btn btn-sm action-delete-hard" data-id="${job.offer_id}" style="color:var(--red);border:1px solid var(--red);background:none;">Supprimer définitivement</button>`
            : `<button class="btn btn-secondary btn-sm action-interested" data-id="${job.offer_id}">Intéressé</button>
               <button class="btn btn-secondary btn-sm action-reject" data-id="${job.offer_id}">🗑 Refuser</button>`
          }
        </div>
      </div>
    </li>
  `).join('')

  list.querySelectorAll('.job-item').forEach(item => {
    item.querySelector('.job-item-summary').addEventListener('click', () => {
      const expanded = item.querySelector('.job-item-expanded')
      const isOpen = !expanded.classList.contains('hidden')
      list.querySelectorAll('.job-item-expanded').forEach(e => e.classList.add('hidden'))
      list.querySelectorAll('.job-item').forEach(i => i.classList.remove('expanded'))
      if (!isOpen) {
        expanded.classList.remove('hidden')
        item.classList.add('expanded')
        const job = currentJobs.find(j => j.offer_id === item.dataset.id)
        if (job?.status === 'new') {
          fetch(`${window.__API_BASE__}/jobs/${item.dataset.id}/status?status=seen`, { method: 'PATCH' })
            .then(() => {
              job.status = 'seen'
              item.querySelector('.badge').className = 'badge badge-seen'
              item.querySelector('.badge').textContent = labelStatus('seen')
            })
            .catch(console.error)
        }
      }
    })

    item.querySelector('.job-expand-link')?.addEventListener('click', (e) => {
      e.preventDefault()
      window.api.openExternal(e.target.dataset.url)
    })

    // Vue normale : Intéressé / Refuser (→ Corbeille)
    item.querySelector('.action-interested')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}/status?status=interested`, { method: 'PATCH' })
      await loadJobs()
    })

    item.querySelector('.action-reject')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}/status?status=rejected`, { method: 'PATCH' })
      await loadJobs()
    })

    // Vue Corbeille : Restaurer / Supprimer définitivement
    item.querySelector('.action-restore')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}/status?status=new`, { method: 'PATCH' })
      await loadJobs()
    })

    item.querySelector('.action-delete-hard')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      if (!confirm('Supprimer définitivement cette offre ?')) return
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}`, { method: 'DELETE' })
      await loadJobs()
    })
  })
}

function updateCount() {
  const el = document.getElementById('r-count')
  if (el) el.textContent = `(${currentJobs.length})`
  const badgeAll = document.getElementById('badge-all')
  if (badgeAll) badgeAll.textContent = currentJobs.length > 0 ? currentJobs.length : ''
}

function updateSidebarSites(jobs) {
  const container = document.getElementById('sidebar-sites')
  if (!container) return

  // Compter par source (hors rejetés)
  const counts = {}
  jobs.filter(j => j.status !== 'rejected').forEach(j => {
    counts[j.source_site] = (counts[j.source_site] || 0) + 1
  })

  const sites = Object.entries(counts).sort((a, b) => b[1] - a[1])

  if (sites.length === 0) {
    container.innerHTML = ''
  } else {
    container.innerHTML = sites.map(([site, count]) => `
      <a class="nav-item nav-item-site" data-tab="results" data-source="${site}" href="#">
        <span class="nav-icon">·</span>
        <span class="nav-label">${escapeHtml(site)}</span>
        <span class="nav-badge">${count}</span>
      </a>
    `).join('')

    container.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault()
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'))
        item.classList.add('active')
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'))
        document.getElementById('tab-results').classList.add('active')
        setFilters({ status: '', source: item.dataset.source })
      })
    })
  }

  // Badge Corbeille
  const rejectedCount = jobs.filter(j => j.status === 'rejected').length
  const badgeRejected = document.getElementById('badge-rejected')
  if (badgeRejected) badgeRejected.textContent = rejectedCount > 0 ? rejectedCount : ''
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

export function labelStatus(status) {
  return { new: 'Nouveau', seen: 'Vu', interested: 'Intéressé', rejected: 'Rejeté' }[status] || status
}

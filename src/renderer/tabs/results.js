import { escapeHtml } from '../utils/html.js'

let currentJobs = []

export async function initResults() {
  const panel = document.getElementById('tab-results')
  panel.innerHTML = `
    <div class="results-header">
      <h2 class="page-title">Résultats <span id="r-count" style="font-size:14px;font-weight:400;color:var(--text-muted);"></span></h2>
    </div>
    <div class="filters">
      <input id="r-search" type="text" placeholder="Rechercher dans les offres…">
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

  await loadSources()
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
    // Sidebar : toujours calculer depuis toutes les offres (sans filtre source)
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
    list.innerHTML = '<li style="padding:20px;text-align:center;color:var(--text-muted);">Aucune offre</li>'
    return
  }

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
          <button class="btn btn-secondary btn-sm action-interested" data-id="${job.offer_id}">Intéressé</button>
          <button class="btn btn-secondary btn-sm action-reject" data-id="${job.offer_id}">Refuser</button>
          <button class="btn btn-sm action-delete" data-id="${job.offer_id}" style="color:var(--red);border:1px solid var(--red);background:none;">Supprimer</button>
        </div>
      </div>
    </li>
  `).join('')

  list.querySelectorAll('.job-item').forEach(item => {
    // Toggle expand sur le summary
    item.querySelector('.job-item-summary').addEventListener('click', () => {
      const expanded = item.querySelector('.job-item-expanded')
      const isOpen = !expanded.classList.contains('hidden')
      // Fermer tous les autres
      list.querySelectorAll('.job-item-expanded').forEach(e => e.classList.add('hidden'))
      list.querySelectorAll('.job-item').forEach(i => i.classList.remove('expanded'))
      if (!isOpen) {
        expanded.classList.remove('hidden')
        item.classList.add('expanded')
        // Marquer comme vu
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

    // Lien "Voir l'offre"
    item.querySelector('.job-expand-link')?.addEventListener('click', (e) => {
      e.preventDefault()
      window.api.openExternal(e.target.dataset.url)
    })

    // Intéressé
    item.querySelector('.action-interested')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}/status?status=interested`, { method: 'PATCH' })
      await loadJobs()
    })

    // Refuser
    item.querySelector('.action-reject')?.addEventListener('click', async (e) => {
      e.stopPropagation()
      await fetch(`${window.__API_BASE__}/jobs/${e.target.dataset.id}/status?status=rejected`, { method: 'PATCH' })
      await loadJobs()
    })

    // Supprimer
    item.querySelector('.action-delete')?.addEventListener('click', async (e) => {
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

  // Compter par source
  const counts = {}
  jobs.forEach(j => {
    counts[j.source_site] = (counts[j.source_site] || 0) + 1
  })

  // Générer les items par site
  const sites = Object.entries(counts).sort((a, b) => b[1] - a[1])

  if (sites.length === 0) {
    container.innerHTML = ''
    return
  }

  container.innerHTML = sites.map(([site, count]) => `
    <a class="nav-item nav-item-site" data-tab="results" data-source="${site}" href="#">
      <span class="nav-icon">·</span>
      <span class="nav-label">${escapeHtml(site)}</span>
      <span class="nav-badge">${count}</span>
    </a>
  `).join('')

  // Compteur Corbeille
  const rejectedCount = jobs.filter(j => j.status === 'rejected').length
  const badgeRejected = document.getElementById('badge-rejected')
  if (badgeRejected) badgeRejected.textContent = rejectedCount > 0 ? rejectedCount : ''

  // Re-attacher les event listeners pour les nouveaux items
  container.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault()
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'))
      item.classList.add('active')
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'))
      document.getElementById('tab-results').classList.add('active')
      const sourceSelect = document.getElementById('r-source')
      if (sourceSelect) {
        sourceSelect.value = item.dataset.source
        loadJobs()
      }
    })
  })
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

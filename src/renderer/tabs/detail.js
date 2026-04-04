import { switchTab } from '../router.js'
import { loadJobs, labelStatus } from './results.js'
import { escapeHtml } from '../utils/html.js'

export function initDetail() {
  const panel = document.getElementById('tab-detail')
  panel.innerHTML = '<p style="color:#6e6e73;padding:20px;">Sélectionner une offre dans les Résultats.</p>'
}

export async function loadDetail(offerId) {
  const panel = document.getElementById('tab-detail')
  panel.innerHTML = '<p style="color:#6e6e73;padding:20px;">Chargement…</p>'

  const res = await fetch(`${window.__API_BASE__}/jobs/${offerId}`)
  if (!res.ok) {
    panel.innerHTML = '<p style="color:#c00;padding:20px;">Offre introuvable.</p>'
    return
  }
  let job = await res.json()

  // Marquer comme "vu" si statut encore "new"
  if (job.status === 'new') {
    await fetch(`${window.__API_BASE__}/jobs/${offerId}/status?status=seen`, { method: 'PATCH' })
    job = { ...job, status: 'seen' }
  }

  renderDetail(panel, job)
}

function renderDetail(panel, job) {
  panel.innerHTML = `
    <div style="max-width:800px;">
      <button class="btn btn-secondary btn-sm" id="d-back">← Retour aux résultats</button>

      <div class="detail-header" style="margin-top:16px;">
        <div class="detail-title">${escapeHtml(job.title)}</div>
        <div class="detail-company">${escapeHtml(job.company)}</div>
        <div class="detail-meta">
          <span>📍 ${escapeHtml(job.location)}</span>
          ${job.salary ? `<span>💶 ${escapeHtml(job.salary)}</span>` : ''}
          ${job.contract_type ? `<span>📄 ${escapeHtml(job.contract_type)}</span>` : ''}
          <span>🌐 ${escapeHtml(job.source_site)}</span>
          ${job.published_date ? `<span>📅 ${job.published_date}</span>` : ''}
        </div>
      </div>

      <div class="detail-actions">
        ${['new','seen','interested','rejected'].map(s => `
          <button class="btn ${job.status === s ? 'btn-primary' : 'btn-secondary'} btn-sm status-btn"
                  data-status="${s}">
            ${labelStatus(s)}
          </button>
        `).join('')}
        <button class="btn btn-secondary btn-sm" id="d-open-url" style="margin-left:auto;">
          Ouvrir dans le navigateur ↗
        </button>
      </div>

      ${job.description
        ? `<div class="detail-description">${escapeHtml(job.description)}</div>`
        : '<p style="color:#6e6e73;font-style:italic;">Pas de description disponible.</p>'
      }
    </div>
  `

  document.getElementById('d-back').addEventListener('click', () => switchTab('results'))

  document.getElementById('d-open-url').addEventListener('click', () => {
    window.api.openExternal(job.url)
  })

  panel.querySelectorAll('.status-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const newStatus = btn.dataset.status
      await fetch(`${window.__API_BASE__}/jobs/${job.offer_id}/status?status=${newStatus}`, { method: 'PATCH' })
      job = { ...job, status: newStatus }
      renderDetail(panel, job)
      loadJobs()
    })
  })
}


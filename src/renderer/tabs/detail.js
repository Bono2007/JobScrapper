import { switchTab } from '../router.js'
import { loadJobs, labelStatus } from './results.js'
import { escapeHtml } from '../utils/html.js'

export function initDetail() {
  const panel = document.getElementById('tab-detail')
  panel.innerHTML = '<p style="padding:28px;color:var(--text-muted);">Sélectionner une offre dans les Résultats.</p>'
}

export async function loadDetail(offerId) {
  const panel = document.getElementById('tab-detail')
  panel.innerHTML = '<p style="padding:28px;color:var(--text-muted);">Chargement…</p>'

  try {
    const res = await fetch(`${window.__API_BASE__}/jobs/${offerId}`)
    if (!res.ok) {
      panel.innerHTML = '<p style="padding:28px;color:var(--red);">Offre introuvable.</p>'
      return
    }
    let job = await res.json()

    // Marquer comme "vu" si statut encore "new"
    if (job.status === 'new') {
      await fetch(`${window.__API_BASE__}/jobs/${offerId}/status?status=seen`, { method: 'PATCH' })
      job = { ...job, status: 'seen' }
    }

    renderDetail(panel, job)
  } catch (err) {
    console.error('[loadDetail]', err)
    panel.innerHTML = `<p style="padding:28px;color:var(--red);">Erreur : ${escapeHtml(err.message)}</p>`
  }
}

function renderDetail(panel, job) {
  panel.scrollTop = 0  // scroll to top

  const statusColors = {
    new: 'badge-new',
    seen: 'badge-seen',
    interested: 'badge-interested',
    rejected: 'badge-rejected'
  }

  panel.innerHTML = `
    <div style="max-width:800px;">
      <button class="btn btn-secondary btn-sm" id="d-back">← Résultats</button>

      <div class="detail-header" style="margin-top:20px;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px;">
          <div class="detail-title" style="flex:1;">${escapeHtml(job.title)}</div>
          <span class="badge ${statusColors[job.status] || 'badge-seen'}">${labelStatus(job.status)}</span>
        </div>
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
                  data-status="${s}" ${job.status === s ? 'disabled' : ''}>
            ${labelStatus(s)}
          </button>
        `).join('')}
        <button class="btn btn-secondary btn-sm" id="d-open-url" style="margin-left:auto;">
          Voir l'offre ↗
        </button>
      </div>

      ${job.description
        ? `<div class="detail-description">${escapeHtml(job.description)}</div>`
        : `<div style="padding:20px;border:1px solid var(--border);border-radius:var(--radius-lg);text-align:center;color:var(--text-muted);">
            <p style="margin-bottom:12px;">Pas de description disponible pour cette offre.</p>
            <button class="btn btn-secondary btn-sm" id="d-open-url-2">Voir l'offre complète sur ${escapeHtml(job.source_site)} ↗</button>
           </div>`
      }
    </div>
  `

  document.getElementById('d-back').addEventListener('click', () => switchTab('results'))

  const openUrl = () => {
    if (window.api?.openExternal) {
      window.api.openExternal(job.url)
    }
  }
  document.getElementById('d-open-url').addEventListener('click', openUrl)
  document.getElementById('d-open-url-2')?.addEventListener('click', openUrl)

  panel.querySelectorAll('.status-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (btn.disabled) return
      const newStatus = btn.dataset.status
      // Disable all buttons during request
      panel.querySelectorAll('.status-btn').forEach(b => { b.disabled = true })
      try {
        await fetch(`${window.__API_BASE__}/jobs/${job.offer_id}/status?status=${newStatus}`, { method: 'PATCH' })
        job = { ...job, status: newStatus }
        renderDetail(panel, job)
        loadJobs()
      } catch (err) {
        console.error('[updateStatus]', err)
        // Re-enable on error
        panel.querySelectorAll('.status-btn').forEach(b => { b.disabled = false })
      }
    })
  })
}

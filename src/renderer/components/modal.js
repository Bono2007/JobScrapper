import { escapeHtml } from '../utils/html.js'

export function openModal(sseUrl, scraperNames, onDone) {
  const overlay = document.getElementById('modal-overlay')
  const box = document.getElementById('modal-box')

  const state = {}
  scraperNames.forEach(name => { state[name] = { status: 'pending', count: 0, error: null } })

  function render() {
    const rows = scraperNames.map(name => {
      const s = state[name]
      let statusHtml
      if (s.status === 'pending') {
        statusHtml = '<span class="scraper-status">⏳ En attente…</span>'
      } else if (s.status === 'error') {
        const msg = s.error ? escapeHtml(s.error.slice(0, 80)) : 'Erreur'
        statusHtml = `<span class="scraper-status" style="color:var(--red)" title="${escapeHtml(s.error || '')}">❌ ${msg}</span>`
      } else {
        statusHtml = `<span class="scraper-status" style="color:var(--green)">✅ ${s.count} offre${s.count > 1 ? 's' : ''}</span>`
      }
      return `<div class="scraper-row"><span>${escapeHtml(name)}</span>${statusHtml}</div>`
    }).join('')

    const doneCount = scraperNames.filter(n => state[n].status !== 'pending').length

    box.innerHTML = `
      <div class="modal-title">🔍 Recherche en cours…</div>
      ${rows}
      <div class="modal-footer">${doneCount} / ${scraperNames.length} sites terminés</div>
    `
  }

  overlay.classList.remove('hidden')
  render()

  const es = new EventSource(sseUrl)

  es.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.done) {
      es.close()
      box.innerHTML = `
        <div class="modal-title">✅ Recherche terminée</div>
        <div style="text-align:center;padding:20px;font-size:15px;">
          <strong>${data.total}</strong> offre${data.total > 1 ? 's' : ''} unique${data.total > 1 ? 's' : ''} trouvée${data.total > 1 ? 's' : ''}
        </div>
        <div style="text-align:center;">
          <button class="btn btn-primary" id="modal-close-btn">Voir les résultats</button>
        </div>
      `
      document.getElementById('modal-close-btn').addEventListener('click', () => {
        overlay.classList.add('hidden')
        onDone()
      })
      setTimeout(() => {
        if (!overlay.classList.contains('hidden')) {
          overlay.classList.add('hidden')
          onDone()
        }
      }, 2500)
      return
    }

    if (state[data.site] !== undefined) {
      state[data.site] = {
        status: data.error ? 'error' : 'done',
        count: data.count,
        error: data.error || null,
      }
    }
    render()
  }

  es.onerror = () => {
    es.close()
    scraperNames.forEach(name => {
      if (state[name].status === 'pending') {
        state[name] = { status: 'error', count: 0, error: 'Connexion perdue' }
      }
    })
    render()
    setTimeout(() => {
      overlay.classList.add('hidden')
      onDone()
    }, 3000)
  }
}

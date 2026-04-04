export function openModal(sseUrl, scraperNames, onDone) {
  const overlay = document.getElementById('modal-overlay')
  const box = document.getElementById('modal-box')

  const state = {}
  scraperNames.forEach(name => { state[name] = { status: 'pending', count: 0 } })

  function render() {
    const rows = scraperNames.map(name => {
      const s = state[name]
      let statusHtml
      if (s.status === 'pending') statusHtml = '<span class="scraper-status">⏳ En attente…</span>'
      else if (s.status === 'done') statusHtml = `<span class="scraper-status" style="color:#1a7a1a">✅ ${s.count} offre${s.count > 1 ? 's' : ''}</span>`
      else statusHtml = '<span class="scraper-status" style="color:#c00">❌ Erreur</span>'
      return `<div class="scraper-row"><span>${name}</span>${statusHtml}</div>`
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
      state[data.site] = { status: 'done', count: data.count }
    }
    render()
  }

  es.onerror = () => {
    es.close()
    scraperNames.forEach(name => {
      if (state[name].status === 'pending') {
        state[name] = { status: 'error', count: 0 }
      }
    })
    render()
    setTimeout(() => {
      overlay.classList.add('hidden')
      onDone()
    }, 3000)
  }
}

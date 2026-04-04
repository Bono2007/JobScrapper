import { openModal } from '../components/modal.js'
import { switchTab } from '../index.js'
import { loadJobs } from './results.js'

const DEFAULT_EXCLUDE = 'Alternance, Stage'

export function initSearch() {
  const panel = document.getElementById('tab-search')
  panel.innerHTML = `
    <h2 style="margin-bottom:20px;font-size:18px;">Nouvelle recherche</h2>
    <div style="max-width:600px;">
      <div class="form-group">
        <label>Mots-clés *</label>
        <input id="s-keywords" type="text" placeholder="ex: développeur Python, CRM marketing" required>
      </div>
      <div class="form-group" style="display:flex;gap:12px;">
        <div style="flex:1;">
          <label>Localisation *</label>
          <input id="s-location" type="text" placeholder="ex: Paris, Lille, Lyon">
        </div>
        <div style="width:120px;">
          <label>Rayon (km)</label>
          <input id="s-radius" type="number" value="30" min="0" max="200">
        </div>
      </div>
      <div class="form-group">
        <label>Mots-clés à exclure (séparés par virgule)</label>
        <input id="s-exclude" type="text" value="${DEFAULT_EXCLUDE}">
      </div>
      <div class="form-group">
        <label style="margin-bottom:8px;">Sites à scraper</label>
        <div id="scrapers-container">
          <span style="color:#6e6e73;font-size:13px;">Chargement…</span>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:20px;">
        <button class="btn btn-primary" id="s-submit">Lancer la recherche</button>
        <button class="btn btn-secondary" id="s-select-all">Tout sélectionner</button>
        <button class="btn btn-secondary" id="s-deselect-all">Tout désélectionner</button>
      </div>
    </div>
  `

  loadScrapers()

  document.getElementById('s-submit').addEventListener('click', handleSubmit)
  document.getElementById('s-select-all').addEventListener('click', () => toggleAll(true))
  document.getElementById('s-deselect-all').addEventListener('click', () => toggleAll(false))
}

async function loadScrapers() {
  const res = await fetch(`${window.__API_BASE__}/scrapers`)
  const names = await res.json()
  const container = document.getElementById('scrapers-container')
  container.className = 'scrapers-grid'
  container.innerHTML = names.map(name => `
    <label class="scraper-cb">
      <input type="checkbox" name="scraper" value="${name}" checked>
      ${name}
    </label>
  `).join('')
}

function toggleAll(checked) {
  document.querySelectorAll('input[name="scraper"]').forEach(cb => cb.checked = checked)
}

async function handleSubmit() {
  const keywords = document.getElementById('s-keywords').value.trim()
  const location = document.getElementById('s-location').value.trim()
  const radius = document.getElementById('s-radius').value || '30'
  const exclude = document.getElementById('s-exclude').value.trim()
  const selected = [...document.querySelectorAll('input[name="scraper"]:checked')].map(cb => cb.value)

  if (!keywords || !location) {
    alert('Les champs Mots-clés et Localisation sont obligatoires.')
    return
  }

  const params = new URLSearchParams({
    keywords,
    location,
    radius_km: radius,
    exclude_keywords: exclude,
  })
  selected.forEach(s => params.append('scraper_names', s))

  const url = `${window.__API_BASE__}/search/progress?${params}`
  openModal(url, selected, () => {
    loadJobs()
    switchTab('results')
  })
}

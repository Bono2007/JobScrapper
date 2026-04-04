// Entry point — sera complété dans Task 8
async function init() {
  const port = await window.api.getPort()
  window.__API_BASE__ = `http://127.0.0.1:${port}`
  setupTabs()
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

export function switchTab(name) {
  document.querySelector(`.tab-btn[data-tab="${name}"]`).click()
}

init()

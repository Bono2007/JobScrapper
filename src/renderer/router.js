export function switchTab(name) {
  // Active le bon nav-item et le bon panel
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'))
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'))

  // Active le premier nav-item correspondant à ce tab (sans filtre de source)
  const navItem = document.querySelector(`.nav-item[data-tab="${name}"][data-source=""]`) ||
                  document.querySelector(`.nav-item[data-tab="${name}"]`)
  if (navItem) navItem.classList.add('active')

  const panel = document.getElementById(`tab-${name}`)
  if (panel) panel.classList.add('active')
}

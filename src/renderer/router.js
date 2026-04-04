export function switchTab(name) {
  const btn = document.querySelector(`.tab-btn[data-tab="${name}"]`)
  if (btn) btn.click()
}

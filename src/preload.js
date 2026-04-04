const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  getPort: () => ipcRenderer.invoke('get-port'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  saveCsv: (csvUrl) => ipcRenderer.invoke('save-csv', csvUrl),
})

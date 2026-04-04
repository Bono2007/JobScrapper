const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  getPort: () => ipcRenderer.invoke('get-port'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
})

const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron')
const path = require('path')
const { startPython, stopPython } = require('./python')

let mainWindow = null
let apiPort = null

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'JobScrapper',
    webPreferences: {
      preload: path.join(__dirname, '../preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  try {
    apiPort = await startPython()
  } catch (err) {
    console.error('Impossible de démarrer Python :', err)
    const msg = app.isPackaged
      ? 'Le backend ne peut pas démarrer. Réinstallez l\'application.'
      : `Erreur (dev): ${err.message}`
    mainWindow.loadURL(`data:text/html;charset=utf-8,<h2 style="font-family:sans-serif;padding:20px">${msg}</h2>`)
    return
  }

  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))

  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  stopPython()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

ipcMain.handle('get-port', () => apiPort)
ipcMain.handle('open-external', (_event, url) => shell.openExternal(url))

ipcMain.handle('save-csv', async (_event, csvUrl) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    defaultPath: 'offres_emploi.csv',
    filters: [{ name: 'CSV', extensions: ['csv'] }],
  })
  if (canceled || !filePath) return { saved: false }

  const res = await fetch(csvUrl)
  const buffer = Buffer.from(await res.arrayBuffer())
  require('fs').writeFileSync(filePath, buffer)
  return { saved: true, filePath }
})

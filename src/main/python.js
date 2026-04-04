const { spawn } = require('child_process')
const net = require('net')
const path = require('path')

let pythonProcess = null

async function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port
      server.close(() => resolve(port))
    })
    server.on('error', reject)
  })
}

async function waitForReady(port, timeout = 15000) {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/scrapers`)
      if (res.ok) return
    } catch {}
    await new Promise(r => setTimeout(r, 300))
  }
  throw new Error('Le backend Python ne répond pas après 15 secondes')
}

async function startPython() {
  const isDev = !require('electron').app.isPackaged

  let cmd, args, getCwd

  if (isDev) {
    cmd = 'uv'
    getCwd = () => path.join(__dirname, '../../python')
    args = (port) => ['run', 'uvicorn', 'src.api:app', '--host', '127.0.0.1', '--port', String(port), '--no-access-log']
  } else {
    const binaryName = process.platform === 'win32' ? 'api.exe' : 'api'
    const binaryPath = path.join(process.resourcesPath, 'python-dist', binaryName)
    cmd = binaryPath
    getCwd = () => path.dirname(binaryPath)
    args = (port) => ['--host', '127.0.0.1', '--port', String(port)]
  }

  for (let attempt = 0; attempt < 3; attempt++) {
    const port = await findFreePort()
    const cwd = getCwd()

    pythonProcess = spawn(cmd, args(port), {
      cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    })

    pythonProcess.stdout.on('data', d => console.log('[Python]', d.toString().trim()))
    pythonProcess.stderr.on('data', d => console.error('[Python]', d.toString().trim()))
    pythonProcess.on('exit', code => {
      console.log(`[Python] exit ${code}`)
      // Signaler le crash au renderer si inattendu
      if (code !== 0 && code !== null) {
        const { BrowserWindow } = require('electron')
        const wins = BrowserWindow.getAllWindows()
        wins.forEach(w => w.webContents.send('python-crashed', code))
      }
    })

    try {
      await waitForReady(port)
      return port
    } catch (err) {
      console.warn(`[Python] tentative ${attempt + 1} échouée, nouveau port...`)
      pythonProcess.kill()
      pythonProcess = null
    }
  }

  throw new Error('Impossible de démarrer le backend Python après 3 tentatives')
}

function stopPython() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

module.exports = { startPython, stopPython }

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
  const port = await findFreePort()
  const isDev = !require('electron').app.isPackaged

  let cmd, args, cwd

  if (isDev) {
    cmd = 'uv'
    args = ['run', 'uvicorn', 'src.api:app', '--host', '127.0.0.1', '--port', String(port), '--no-access-log']
    cwd = path.join(__dirname, '../../python')
  } else {
    const binaryName = process.platform === 'win32' ? 'api.exe' : 'api'
    const binaryPath = path.join(process.resourcesPath, 'python-dist', binaryName)
    cmd = binaryPath
    args = ['--host', '127.0.0.1', '--port', String(port)]
    cwd = path.dirname(binaryPath)
  }

  pythonProcess = spawn(cmd, args, {
    cwd,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })

  pythonProcess.stdout.on('data', d => console.log('[Python]', d.toString().trim()))
  pythonProcess.stderr.on('data', d => console.error('[Python]', d.toString().trim()))
  pythonProcess.on('exit', code => console.log(`[Python] exit ${code}`))

  await waitForReady(port)
  return port
}

function stopPython() {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
}

module.exports = { startPython, stopPython }

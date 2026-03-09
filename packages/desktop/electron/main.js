const { app, BrowserWindow, ipcMain, Menu } = require('electron')
const path = require('path')
const fs = require('fs')
const os = require('os')

const isDev = process.env.ELECTRON_DEV === '1'

// ── Config ──────────────────────────────────────────────────────────────────

function getConfig() {
  const configPath = path.join(app.getPath('userData'), 'config.json')
  const defaults = {
    wordTarget: 750,
    outputDir: path.join(os.homedir(), 'WritLarge'),
  }
  try {
    if (fs.existsSync(configPath)) {
      const raw = fs.readFileSync(configPath, 'utf-8')
      return { ...defaults, ...JSON.parse(raw) }
    }
  } catch (_) {}
  return defaults
}

// ── Date helpers ─────────────────────────────────────────────────────────────

function getOutputDir(config) {
  return config.outputDir.startsWith('~')
    ? config.outputDir.replace('~', os.homedir())
    : config.outputDir
}

function getTodayStamp() {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return { date: `${yyyy}-${mm}-${dd}`, time: `${hh}:${mi}:${ss}` }
}

function getTodayFilepath(config) {
  const { date } = getTodayStamp()
  return path.join(getOutputDir(config), `${date}.txt`)
}

// ── Window ───────────────────────────────────────────────────────────────────

let win

function createWindow() {
  // Minimal app menu — keeps Cmd+Q working on macOS, suppresses everything else
  if (process.platform === 'darwin') {
    Menu.setApplicationMenu(
      Menu.buildFromTemplate([
        { label: app.name, submenu: [{ role: 'quit' }] },
      ])
    )
  } else {
    Menu.setApplicationMenu(null)
  }

  win = new BrowserWindow({
    width: 1440,
    height: 900,
    fullscreen: true,
    backgroundColor: '#000000',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (isDev) {
    win.loadURL('http://localhost:5173')
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => app.quit())

// ── IPC handlers ─────────────────────────────────────────────────────────────

ipcMain.handle('get-config', () => getConfig())

ipcMain.handle('check-today', () => {
  const filepath = getTodayFilepath(getConfig())
  return fs.existsSync(filepath)
})

ipcMain.handle('save-session', (_event, text, meta = {}) => {
  const config = getConfig()
  const dir = getOutputDir(config)
  const { date, time } = getTodayStamp()
  const mode = meta.mode ?? 'pages'

  // Freewrite files get a time-stamped stem so multiple sessions can coexist
  const timeTag = time.replace(/:/g, '')  // HHMMSS
  const stem = mode === 'freewrite' ? `${date}-freewrite-${timeTag}` : date

  try {
    fs.mkdirSync(dir, { recursive: true })

    // 1. Plain text file
    const textPath = path.join(dir, `${stem}.txt`)
    fs.writeFileSync(textPath, text, 'utf-8')

    // 2. Keystroke timing file
    if (meta.keystrokes && meta.keystrokes.length > 0) {
      const keysPath = path.join(dir, `${stem}.keys.json`)
      const keysData = JSON.stringify({ start: meta.startTime, keys: meta.keystrokes })
      fs.writeFileSync(keysPath, keysData, 'utf-8')
    }

    // 3. Session stats log (one JSON line appended per session)
    const statsPath = path.join(dir, 'stats.jsonl')
    const statsEntry = JSON.stringify({
      date,
      time_of_day: time,
      mode,
      words: text.match(/\S+/g)?.length ?? 0,
      median_ms: meta.medianMs ?? 0,
      duration_s: meta.elapsed ?? 0,
    })
    fs.appendFileSync(statsPath, statsEntry + '\n', 'utf-8')

    return { success: true, path: textPath }
  } catch (err) {
    return { success: false, error: err.message }
  }
})

ipcMain.handle('quit', () => app.quit())

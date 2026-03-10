const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('writlarge', {
  getConfig:   ()            => ipcRenderer.invoke('get-config'),
  checkToday:  ()            => ipcRenderer.invoke('check-today'),
  saveSession: (text, meta)  => ipcRenderer.invoke('save-session', text, meta),
  listPages:   ()            => ipcRenderer.invoke('list-pages'),
  readFile:    (filePath)    => ipcRenderer.invoke('read-file', filePath),
  quit:        ()            => ipcRenderer.invoke('quit'),
})

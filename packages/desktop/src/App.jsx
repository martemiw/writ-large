import { useState, useEffect } from 'react'
import TitleScreen from './components/TitleScreen'
import WritingCanvas from './components/WritingCanvas'
import BlockedScreen from './components/BlockedScreen'
import FilePickerScreen from './components/FilePickerScreen'
import EditorCanvas from './components/EditorCanvas'

export default function App() {
  const [screen, setScreen] = useState('title') // title | loading | blocked | writing | picker | editing
  const [config, setConfig] = useState(null)
  const [writeMode, setWriteMode] = useState('pages') // pages | freewrite
  const [editFile, setEditFile] = useState(null)

  useEffect(() => {
    window.writlarge.getConfig().then(setConfig)
  }, [])

  async function startMorningPages() {
    setScreen('loading')
    const alreadyDone = await window.writlarge.checkToday()
    if (alreadyDone) {
      setScreen('blocked')
    } else {
      setWriteMode('pages')
      setScreen('writing')
    }
  }

  function startFreeWrite() {
    setWriteMode('freewrite')
    setScreen('writing')
  }

  function openFile(file) {
    setEditFile(file)
    setScreen('editing')
  }

  if (screen === 'title')   return <TitleScreen onMorningPages={startMorningPages} onFreeWrite={startFreeWrite} onEdit={() => setScreen('picker')} onExit={() => window.writlarge.quit()} />
  if (screen === 'loading') return <div className="screen" />
  if (screen === 'blocked') return <BlockedScreen />
  if (screen === 'picker')  return <FilePickerScreen onSelect={openFile} onBack={() => setScreen('title')} />
  if (screen === 'editing') return <EditorCanvas file={editFile} onExit={() => setScreen('title')} />
  return <WritingCanvas config={config} mode={writeMode} />
}

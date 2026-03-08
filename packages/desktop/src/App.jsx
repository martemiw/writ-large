import { useState, useEffect } from 'react'
import TitleScreen from './components/TitleScreen'
import WritingCanvas from './components/WritingCanvas'
import BlockedScreen from './components/BlockedScreen'

export default function App() {
  const [screen, setScreen] = useState('title') // title | loading | blocked | writing
  const [config, setConfig] = useState(null)

  // Load config eagerly so it's ready when Morning Pages starts
  useEffect(() => {
    window.writlarge.getConfig().then(setConfig)
  }, [])

  async function startMorningPages() {
    setScreen('loading')
    const alreadyDone = await window.writlarge.checkToday()
    setScreen(alreadyDone ? 'blocked' : 'writing')
  }

  if (screen === 'title')   return <TitleScreen onMorningPages={startMorningPages} onExit={() => window.writlarge.quit()} />
  if (screen === 'loading') return <div className="screen" />
  if (screen === 'blocked') return <BlockedScreen />
  return <WritingCanvas config={config} />
}

import { useEffect } from 'react'

function formatElapsedVerbose(seconds) {
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''}`
  }
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  const mStr = `${m} minute${m !== 1 ? 's' : ''}`
  return s === 0 ? mStr : `${mStr} ${s} second${s !== 1 ? 's' : ''}`
}

export default function DoneScreen({ wordCount, savedPath, elapsed, medianMs }) {
  // Escape (or Cmd+Q via OS) closes the app
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') window.writlarge.quit()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const displayPath = savedPath.replace(/^\/Users\/[^/]+/, '~')

  return (
    <div className="screen done-screen">
      <div className="done-body">
        <p className="done-heading">done.</p>
        <p className="done-count">{wordCount.toLocaleString()} words</p>
        <p className="done-time">{formatElapsedVerbose(elapsed)}</p>
        <p className="done-time">{medianMs}ms median keystroke</p>
        <p className="done-path">saved to {displayPath}</p>
        <p className="done-quit">esc to close</p>
      </div>
    </div>
  )
}

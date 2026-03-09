function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function HUD({ wordCount, target, elapsed, mode }) {
  const complete = target !== null && wordCount >= target

  return (
    <div className="hud">
      <span className="hud-time">{formatElapsed(elapsed)}</span>
      {mode === 'freewrite' ? (
        <div className="hud-right">
          <span className="hud-count">{wordCount.toLocaleString()}</span>
          <span className="hud-hint">esc · done</span>
        </div>
      ) : (
        <span className={`hud-count${complete ? ' hud-count--complete' : ''}`}>
          {wordCount.toLocaleString()} / {target.toLocaleString()}
        </span>
      )}
    </div>
  )
}

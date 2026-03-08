function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function HUD({ wordCount, target, elapsed }) {
  const complete = wordCount >= target

  return (
    <div className="hud">
      <span className="hud-time">{formatElapsed(elapsed)}</span>
      <span className={`hud-count${complete ? ' hud-count--complete' : ''}`}>
        {wordCount.toLocaleString()} / {target.toLocaleString()}
      </span>
    </div>
  )
}

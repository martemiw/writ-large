import { useState, useEffect } from 'react'

export default function FilePickerScreen({ onSelect, onBack }) {
  const [files, setFiles] = useState(null) // null = loading
  const [cursor, setCursor] = useState(0)

  useEffect(() => {
    window.writlarge.listPages().then(setFiles)
  }, [])

  useEffect(() => {
    if (!files || files.length === 0) return
    function handler(e) {
      if (e.key === 'ArrowUp')   { e.preventDefault(); setCursor(c => Math.max(0, c - 1)) }
      if (e.key === 'ArrowDown') { e.preventDefault(); setCursor(c => Math.min(files.length - 1, c + 1)) }
      if (e.key === 'Enter')     { e.preventDefault(); onSelect(files[cursor]) }
      if (e.key === 'Escape')    { e.preventDefault(); onBack() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [cursor, files, onSelect, onBack])

  // Escape when empty or loading
  useEffect(() => {
    if (files !== null && files.length > 0) return
    function handler(e) {
      if (e.key === 'Escape') { e.preventDefault(); onBack() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [files, onBack])

  if (files === null) return <div className="screen" />

  if (files.length === 0) {
    return (
      <div className="screen picker-screen">
        <div className="picker-body">
          <div className="picker-header">morning pages</div>
          <p className="picker-empty">no sessions found.</p>
          <div className="picker-hint">esc &nbsp; back</div>
        </div>
      </div>
    )
  }

  return (
    <div className="screen picker-screen">
      <div className="picker-body">
        <div className="picker-header">morning pages</div>
        <nav className="picker-list">
          {files.map((file, i) => (
            <div
              key={file.date}
              className={`picker-item${cursor === i ? ' picker-item--active' : ''}`}
              onMouseEnter={() => setCursor(i)}
              onClick={() => onSelect(file)}
            >
              <span className="picker-arrow">{cursor === i ? '▸' : ' '}</span>
              {file.date}
            </div>
          ))}
        </nav>
        <div className="picker-hint">↑ ↓ &nbsp; navigate &nbsp;&nbsp; enter &nbsp; open &nbsp;&nbsp; esc &nbsp; back</div>
      </div>
    </div>
  )
}

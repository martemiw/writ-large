import { useState, useEffect } from 'react'

const ITEMS = [
  { label: 'MORNING PAGES' },
  { label: 'FREE WRITE'    },
  { label: 'EDIT'          },
  { label: 'EXIT'          },
]

export default function TitleScreen({ onMorningPages, onFreeWrite, onEdit, onExit }) {
  const [cursor, setCursor] = useState(0)

  function activate(i) {
    if (i === 0) onMorningPages()
    if (i === 1) onFreeWrite()
    if (i === 2) onEdit()
    if (i === 3) onExit()
  }

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowUp')   { e.preventDefault(); setCursor(c => Math.max(0, c - 1)) }
      if (e.key === 'ArrowDown') { e.preventDefault(); setCursor(c => Math.min(ITEMS.length - 1, c + 1)) }
      if (e.key === 'Enter')     { activate(cursor) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [cursor])

  return (
    <div className="screen title-screen">
      <div className="title-body">

        <div className="title-header">
          <div className="title-rule" />
          <div className="title-wordmark">W&nbsp;R&nbsp;I&nbsp;T&nbsp;L&nbsp;A&nbsp;R&nbsp;G&nbsp;E</div>
          <div className="title-sub">daily writing</div>
          <div className="title-rule" />
        </div>

        <nav className="title-menu">
          {ITEMS.map((item, i) => (
            <div
              key={item.label}
              className={`title-item${cursor === i ? ' title-item--active' : ''}`}
              onMouseEnter={() => setCursor(i)}
              onClick={() => activate(i)}
            >
              <span className="title-arrow">{cursor === i ? '▸' : ' '}</span>
              {item.label}
            </div>
          ))}
        </nav>

        <div className="title-hint">↑ ↓ &nbsp; navigate &nbsp;&nbsp; enter &nbsp; select</div>
      </div>
    </div>
  )
}

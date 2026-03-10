import { useState, useEffect, useCallback, useRef } from 'react'

// ── Layout constants ──────────────────────────────────────────────────────────
const NOVEL_COLS    = 65    // characters per visual row
const FONT_SIZE_REM = 1.5
const LINE_HEIGHT   = 1.8   // unitless multiplier
const LINE_H_REM    = FONT_SIZE_REM * LINE_HEIGHT  // 2.7rem per visual row

// ── Text layout ───────────────────────────────────────────────────────────────

function wrapText(text, cols) {
  const rows = []
  for (const line of text.split('\n')) {
    if (line.length === 0) { rows.push(''); continue }
    let rem = line
    while (rem.length > 0) {
      if (rem.length <= cols) { rows.push(rem); break }
      let bp = rem.lastIndexOf(' ', cols - 1)
      if (bp <= 0) {
        // No space found — hard break
        rows.push(rem.slice(0, cols))
        rem = rem.slice(cols)
      } else {
        rows.push(rem.slice(0, bp))
        rem = rem.slice(bp + 1)
      }
    }
  }
  return rows
}

// ── Word navigation helpers ───────────────────────────────────────────────────

function getWordStarts(rowText) {
  const starts = []
  if (rowText.length > 0 && rowText[0] !== ' ') starts.push(0)
  for (let i = 1; i < rowText.length; i++) {
    if (rowText[i - 1] === ' ' && rowText[i] !== ' ') starts.push(i)
  }
  return starts
}

function nearestWordStart(rowText, targetCol) {
  const starts = getWordStarts(rowText)
  if (starts.length === 0) return 0
  return starts.reduce((best, s) =>
    Math.abs(s - targetCol) < Math.abs(best - targetCol) ? s : best,
    starts[0]
  )
}

function prevWordStart(rows, row, col) {
  let r = row, c = col
  if (c === 0) {
    if (r === 0) return { row: 0, col: 0 }
    r--
    c = rows[r].length
  }
  c--
  while (c > 0 && rows[r][c] === ' ') c--
  while (c > 0 && rows[r][c - 1] !== ' ') c--
  return { row: r, col: c }
}

function nextWordStart(rows, row, col) {
  let r = row, c = col
  while (c < rows[r].length && rows[r][c] !== ' ') c++
  while (c < rows[r].length && rows[r][c] === ' ') c++
  if (c >= rows[r].length) {
    if (r >= rows.length - 1) return { row: r, col: rows[r].length }
    r++
    c = 0
    while (c < rows[r].length && rows[r][c] === ' ') c++
  }
  return { row: r, col: c }
}

// ── Cursor rendering ──────────────────────────────────────────────────────────

function CursorLine({ text, col, visible }) {
  const before    = text.slice(0, col)
  const atCursor  = text[col] ?? '\u00A0'
  const after     = text.slice(col + 1)
  return (
    <>
      {before}
      <span className={`editor-cursor${visible ? '' : ' editor-cursor--hidden'}`}>{atCursor}</span>
      {after}
    </>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function EditorCanvas({ file, onExit }) {
  const [rows, setRows]               = useState([])
  const [cursor, setCursor]           = useState({ row: 0, col: 0 })
  const [stickyCol, setStickyCol]     = useState(0)
  const [wordMode, setWordMode]       = useState(false)
  const [cursorVisible, setCursorVisible] = useState(true)

  // Refs for use inside stable useCallback
  const rowsRef     = useRef([])
  const cursorRef   = useRef({ row: 0, col: 0 })
  const stickyRef   = useRef(0)
  const wordModeRef = useRef(false)
  const blinkRef    = useRef(null)

  useEffect(() => { rowsRef.current   = rows     }, [rows])
  useEffect(() => { cursorRef.current = cursor   }, [cursor])
  useEffect(() => { stickyRef.current = stickyCol }, [stickyCol])
  useEffect(() => { wordModeRef.current = wordMode }, [wordMode])

  // ── Load file ───────────────────────────────────────────────────────────────
  useEffect(() => {
    window.writlarge.readFile(file.path).then(text => {
      setRows(wrapText(text.trimEnd(), NOVEL_COLS))
    })
  }, [file])

  // ── Cursor blink ────────────────────────────────────────────────────────────
  useEffect(() => {
    blinkRef.current = setInterval(() => setCursorVisible(v => !v), 550)
    return () => clearInterval(blinkRef.current)
  }, [])

  function resetBlink() {
    setCursorVisible(true)
    clearInterval(blinkRef.current)
    blinkRef.current = setInterval(() => setCursorVisible(v => !v), 550)
  }

  // ── Movement helpers ────────────────────────────────────────────────────────
  function move(newCursor, newSticky) {
    setCursor(newCursor)
    const sticky = newSticky ?? newCursor.col
    setStickyCol(sticky)
    resetBlink()
  }

  // ── Key handler ─────────────────────────────────────────────────────────────
  const handleKeyDown = useCallback((e) => {
    const rows   = rowsRef.current
    const { row, col } = cursorRef.current
    const sticky = stickyRef.current
    const wm     = wordModeRef.current

    if (rows.length === 0) return

    // Escape: exit word mode first, then exit editor
    if (e.key === 'Escape') {
      e.preventDefault()
      if (wm) { setWordMode(false) } else { onExit() }
      return
    }

    // w: toggle word mode
    if (e.key === 'w' && !e.metaKey && !e.ctrlKey && !e.altKey) {
      e.preventDefault()
      setWordMode(m => !m)
      return
    }

    if (!e.key.startsWith('Arrow')) return
    e.preventDefault()

    if (wm) {
      // ── Word mode ───────────────────────────────────────────────────────────
      switch (e.key) {
        case 'ArrowRight': {
          move(nextWordStart(rows, row, col))
          break
        }
        case 'ArrowLeft': {
          move(prevWordStart(rows, row, col))
          break
        }
        case 'ArrowDown': {
          if (row >= rows.length - 1) return
          move({ row: row + 1, col: nearestWordStart(rows[row + 1], sticky) }, sticky)
          break
        }
        case 'ArrowUp': {
          if (row <= 0) return
          move({ row: row - 1, col: nearestWordStart(rows[row - 1], sticky) }, sticky)
          break
        }
      }
    } else {
      // ── Character mode ──────────────────────────────────────────────────────
      switch (e.key) {
        case 'ArrowRight': {
          if (col < rows[row].length) {
            move({ row, col: col + 1 })
          } else if (row < rows.length - 1) {
            move({ row: row + 1, col: 0 })
          }
          break
        }
        case 'ArrowLeft': {
          if (col > 0) {
            move({ row, col: col - 1 })
          } else if (row > 0) {
            move({ row: row - 1, col: rows[row - 1].length })
          }
          break
        }
        case 'ArrowDown': {
          if (row >= rows.length - 1) return
          move({ row: row + 1, col: Math.min(sticky, rows[row + 1].length) }, sticky)
          break
        }
        case 'ArrowUp': {
          if (row <= 0) return
          move({ row: row - 1, col: Math.min(sticky, rows[row - 1].length) }, sticky)
          break
        }
      }
    }
  }, [onExit])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // ── Render ──────────────────────────────────────────────────────────────────

  // The column translates so that cursor row's vertical centre lands at 50vh
  const translateY = `calc(50vh - ${cursor.row * LINE_H_REM + LINE_H_REM / 2}rem)`

  return (
    <div className="editor-viewport">

      {/* Scrolling document column */}
      <div
        className="editor-column"
        style={{ transform: `translateX(-50%) translateY(${translateY})` }}
      >
        {rows.map((rowText, i) => (
          <div key={i} className="editor-line">
            {i === cursor.row
              ? <CursorLine text={rowText} col={cursor.col} visible={cursorVisible} />
              : (rowText || '\u00A0')
            }
          </div>
        ))}
      </div>

      {/* Gradient fade covering text below cursor line */}
      <div className="editor-fade-below" />

      {/* HUD */}
      <div className="editor-hud">
        <span className="editor-hud-file">{file.date}</span>
        <span className="editor-hud-pos">line {cursor.row + 1} / {rows.length}</span>
      </div>

      {/* Mode bar */}
      <div className={`editor-modebar${wordMode ? ' editor-modebar--word' : ''}`}>
        {wordMode
          ? <><span className="modebar-mode">word</span><span className="modebar-hint">w → char</span></>
          : <><span className="modebar-mode">char</span><span className="modebar-hint">w → word</span></>
        }
      </div>

    </div>
  )
}

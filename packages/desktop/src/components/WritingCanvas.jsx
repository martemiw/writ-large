import { useState, useEffect, useCallback, useRef } from 'react'
import FadeText from './FadeText'
import HUD from './HUD'
import DoneScreen from './DoneScreen'

function countWords(text) {
  const tokens = text.match(/\S+/g)
  return tokens ? tokens.length : 0
}

function calcMedian(keystrokes) {
  const deltas = keystrokes.map(k => k.d).filter(d => d > 0).sort((a, b) => a - b)
  if (deltas.length === 0) return 0
  const mid = Math.floor(deltas.length / 2)
  return deltas.length % 2 === 0
    ? Math.round((deltas[mid - 1] + deltas[mid]) / 2)
    : deltas[mid]
}

export default function WritingCanvas({ config }) {
  const [buffer, setBuffer] = useState('')
  const [done, setDone] = useState(false)
  const [savedPath, setSavedPath] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [medianMs, setMedianMs] = useState(0)
  const saveAttempted = useRef(false)
  const startRef = useRef(Date.now())
  const timerRef = useRef(null)
  const keystrokesRef = useRef([])
  const lastKeyTimeRef = useRef(null)

  const target = config?.wordTarget ?? 750
  const wordCount = countWords(buffer)

  // ── Session timer ────────────────────────────────────────────────────────
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000))
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  // ── Save once when target is reached ────────────────────────────────────
  useEffect(() => {
    if (wordCount >= target && !saveAttempted.current) {
      saveAttempted.current = true
      const median = calcMedian(keystrokesRef.current)
      const finalElapsed = Math.floor((Date.now() - startRef.current) / 1000)
      setMedianMs(median)
      window.writlarge.saveSession(buffer, {
        startTime: startRef.current,
        keystrokes: keystrokesRef.current,
        medianMs: median,
        elapsed: finalElapsed,
      }).then((result) => {
        if (result.success) {
          clearInterval(timerRef.current)
          setElapsed(finalElapsed)
          setSavedPath(result.path)
          setDone(true)
        } else {
          saveAttempted.current = false
          console.error('Save failed:', result.error)
        }
      })
    }
  }, [wordCount, target, buffer])

  // ── Keyboard handler ─────────────────────────────────────────────────────
  const handleKeyDown = useCallback(
    (e) => {
      // Once done, stop intercepting — DoneScreen handles its own keys
      if (done) return

      // Let OS handle Cmd/Ctrl combos (Cmd+Q, etc.)
      if (e.metaKey || e.ctrlKey) return

      // Hard-block backspace and delete — no take-backs
      if (e.key === 'Backspace' || e.key === 'Delete') {
        e.preventDefault()
        return
      }

      // Ignore navigation, function keys, and any multi-char key name
      if (e.key.length > 1 && e.key !== 'Enter') {
        e.preventDefault()
        return
      }

      // No new input after target is reached
      if (wordCount >= target) return

      e.preventDefault()
      setBuffer((prev) => prev + (e.key === 'Enter' ? '\n' : e.key))

      // Record keystroke timing
      const now = Date.now()
      const delta = lastKeyTimeRef.current === null ? 0 : now - lastKeyTimeRef.current
      lastKeyTimeRef.current = now
      keystrokesRef.current.push({ k: e.key === 'Enter' ? '\n' : e.key, d: delta })
    },
    [done, wordCount, target]
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (done) {
    return (
      <DoneScreen
        wordCount={wordCount}
        savedPath={savedPath}
        elapsed={elapsed}
        medianMs={medianMs}
      />
    )
  }

  return (
    <div className="writing-canvas">
      <div className="writing-stage">
        <FadeText buffer={buffer} />
        <span className="cursor-underscore" aria-hidden="true">_</span>
      </div>
      <HUD wordCount={wordCount} target={target} elapsed={elapsed} />
    </div>
  )
}

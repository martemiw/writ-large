import { useEffect } from 'react'

export default function BlockedScreen() {
  // Any keypress or click closes the app
  useEffect(() => {
    const handler = () => window.writlarge.quit()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const date = new Date().toLocaleDateString([], {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="screen blocked-screen" onClick={() => window.writlarge.quit()}>
      <div className="blocked-body">
        <p className="blocked-date">{date}</p>
        <p className="blocked-message">done.</p>
      </div>
    </div>
  )
}

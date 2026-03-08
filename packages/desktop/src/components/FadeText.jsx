const BUFFER_SIZE = 40

export default function FadeText({ buffer }) {
  const tokens = buffer.match(/\S+/g) || []
  const startIdx = Math.max(0, tokens.length - BUFFER_SIZE)
  const visible = tokens.slice(startIdx)

  return (
    <div className="fade-text-area">
      <div className="fade-text">
        {visible.map((word, i) => (
          <span key={startIdx + i} className="fade-word">
            {word}
          </span>
        ))}
      </div>
    </div>
  )
}

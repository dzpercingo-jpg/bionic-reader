import { useEffect, useRef, useState } from 'react'
import type { Document } from '../types'

export function useTts(document: Document | null, enabled: boolean, rate: number) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const [speaking, setSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    if (!enabled || !document) {
      window.speechSynthesis?.cancel()
      setSpeaking(false)
      setActiveIndex(null)
      return
    }
  }, [enabled, document])

  function start() {
    if (!document) return
    const text = document.blocks
      .filter((b) => b.type !== 'spacer' && b.type !== 'code')
      .map((b) => b.text)
      .join('\n\n')
    const u = new SpeechSynthesisUtterance(text)
    u.rate = rate
    u.onstart = () => setSpeaking(true)
    u.onend = () => {
      setSpeaking(false)
      setActiveIndex(null)
    }
    u.onboundary = (e) => {
      if (e.name === 'word') setActiveIndex(e.charIndex)
    }
    utteranceRef.current = u
    window.speechSynthesis?.cancel()
    window.speechSynthesis?.speak(u)
  }

  function stop() {
    window.speechSynthesis?.cancel()
    setSpeaking(false)
    setActiveIndex(null)
  }

  function toggle() {
    if (speaking) stop()
    else start()
  }

  return { activeIndex, speaking, start, stop, toggle }
}

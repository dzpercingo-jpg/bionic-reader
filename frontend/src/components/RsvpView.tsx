import { useEffect, useMemo, useRef, useState } from 'react'
import { Pause, Play, RotateCcw, X } from 'lucide-react'
import { useApp } from '../store'
import { FONT_FAMILY, THEMES } from '../types'
import { transformTextHtml } from '../lib/bionic'

export default function RsvpView() {
  const { document, settings, setSettings } = useApp()
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(true)
  const timerRef = useRef<number | null>(null)

  const words = useMemo(() => {
    if (!document) return [] as string[]
    return document.blocks.flatMap((b) => b.text.split(/\s+/).filter(Boolean))
  }, [document])

  useEffect(() => {
    setIndex(0)
  }, [document?.id])

  useEffect(() => {
    if (!playing) return
    const wpm = settings.rsvpWpm
    const baseDelay = 60_000 / wpm
    const tick = () => {
      const word = words[index] ?? ''
      let delay = baseDelay * settings.rsvpChunkSize
      if (settings.rsvpPauseOnPunct && /[.!?,:;—]/.test(word)) delay *= 1.6
      timerRef.current = window.setTimeout(() => {
        setIndex((i) => Math.min(i + settings.rsvpChunkSize, words.length))
      }, delay)
    }
    tick()
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [playing, index, words, settings.rsvpWpm, settings.rsvpChunkSize, settings.rsvpPauseOnPunct])

  if (!document) return null

  const theme = THEMES[settings.theme]
  const flash = words.slice(index, index + settings.rsvpChunkSize).join(' ')
  const html = transformTextHtml(flash || '✓', settings)
  const progress = words.length > 0 ? Math.round((index / words.length) * 100) : 0
  const finished = index >= words.length

  return (
    <div
      className="flex-1 br-rsvp relative"
      style={{ background: theme.bg, color: theme.fg, fontFamily: FONT_FAMILY[settings.font] }}
    >
      <button
        onClick={() => setSettings({ rsvpEnabled: false })}
        className="absolute top-4 right-4 p-2 rounded-full hover:bg-black/10"
        title="Quitter le mode RSVP"
      >
        <X className="w-5 h-5" />
      </button>

      <div
        className="text-center"
        style={{ fontSize: `${Math.max(settings.fontSize * 2.4, 38)}px` }}
        dangerouslySetInnerHTML={{ __html: finished ? 'Lecture terminée' : html }}
      />

      <div className="absolute left-0 right-0 bottom-0 px-6 pb-5 pt-3" style={{ background: 'rgba(0,0,0,0.04)' }}>
        <div className="h-1 rounded bg-black/20 overflow-hidden mb-3">
          <div className="h-full bg-indigo-500" style={{ width: `${progress}%` }} />
        </div>
        <div className="flex items-center gap-3 max-w-md mx-auto">
          <button
            onClick={() => setPlaying((p) => !p)}
            className="p-2 rounded-full bg-indigo-600 text-white hover:bg-indigo-700"
            disabled={finished}
          >
            {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>
          <button
            onClick={() => setIndex(0)}
            className="p-2 rounded-full bg-stone-200 hover:bg-stone-300"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <input
            type="range"
            min={100}
            max={1000}
            step={25}
            value={settings.rsvpWpm}
            onChange={(e) => setSettings({ rsvpWpm: parseInt(e.target.value) })}
            className="flex-1 accent-indigo-600"
          />
          <span className="text-sm tabular-nums opacity-70">{settings.rsvpWpm} wpm</span>
        </div>
      </div>
    </div>
  )
}

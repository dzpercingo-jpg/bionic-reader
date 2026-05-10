import { Pause, Play, Square } from 'lucide-react'

export default function TtsBar({
  speaking,
  onToggle,
  onStop,
}: {
  speaking: boolean
  onToggle: () => void
  onStop: () => void
}) {
  return (
    <div className="absolute top-4 right-4 z-30 flex gap-2 bg-white/90 backdrop-blur border border-stone-200 rounded-full shadow px-2 py-1 items-center">
      <button onClick={onToggle} className="p-2 rounded-full hover:bg-stone-100" title="Lire / Pause">
        {speaking ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
      </button>
      <button onClick={onStop} className="p-2 rounded-full hover:bg-stone-100" title="Stop">
        <Square className="w-4 h-4" />
      </button>
    </div>
  )
}

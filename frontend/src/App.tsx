import { useEffect } from 'react'
import { AlertCircle, BookOpenText } from 'lucide-react'
import Toolbar from './components/Toolbar'
import Uploader from './components/Uploader'
import Reader from './components/Reader'
import RsvpView from './components/RsvpView'
import TtsBar from './components/TtsBar'
import { useApp } from './store'
import { exportDocument } from './api'
import { useTts } from './hooks/useTts'

function App() {
  const { document, error, settings, setError, setDocument } = useApp()
  const { activeIndex, speaking, toggle, stop } = useTts(
    document,
    settings.ttsEnabled,
    settings.ttsRate,
  )

  useEffect(() => {
    if (!error) return
    const t = window.setTimeout(() => setError(null), 6000)
    return () => window.clearTimeout(t)
  }, [error, setError])

  async function handleExport(format: 'html' | 'docx' | 'txt') {
    if (!document) return
    try {
      const blob = await exportDocument(document, settings, format, document.filename)
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      const stem = document.filename.replace(/\.[^.]+$/, '')
      a.href = url
      a.download = `${stem}.bionic.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Échec export')
    }
  }

  return (
    <div className="h-screen flex bg-stone-50 text-stone-900 font-ui">
      <Toolbar onExport={handleExport} onReset={() => undefined} />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-14 border-b border-stone-200 bg-white flex items-center px-5 gap-3">
          <BookOpenText className="w-5 h-5 text-indigo-600" />
          <h1 className="font-semibold tracking-tight">Bionic Reader Pro</h1>
          <span className="text-xs text-stone-400 ml-2 hidden md:inline">
            Lecture adaptée ADHD · multi-formats · open source
          </span>
          {document && (
            <button
              onClick={() => setDocument(null)}
              className="ml-auto text-sm text-stone-600 hover:text-rose-600"
            >
              Charger un autre fichier
            </button>
          )}
          {!document && (
            <span className="ml-auto text-xs text-stone-400">v0.1</span>
          )}
        </header>

        {error && (
          <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 bg-rose-100 border border-rose-300 text-rose-800 rounded-lg px-4 py-2 flex items-center gap-2 shadow">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {!document ? (
          <div className="flex-1 flex items-center justify-center px-4">
            <div>
              <Uploader />
              <p className="text-center text-xs text-stone-400 mt-6 max-w-md mx-auto">
                Toutes les transformations sont effectuées localement après extraction. Le serveur
                ne stocke aucun fichier.
              </p>
            </div>
          </div>
        ) : settings.rsvpEnabled ? (
          <RsvpView />
        ) : (
          <>
            {settings.ttsEnabled && (
              <TtsBar speaking={speaking} onToggle={toggle} onStop={stop} />
            )}
            <Reader ttsActiveWord={activeIndex} />
          </>
        )}
      </main>
    </div>
  )
}

export default App

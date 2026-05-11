import { useEffect } from 'react'
import { AlertCircle, BookOpenText, Compass, Home } from 'lucide-react'
import Toolbar from './components/Toolbar'
import Uploader from './components/Uploader'
import Reader from './components/Reader'
import RsvpView from './components/RsvpView'
import TtsBar from './components/TtsBar'
import WelcomePage from './components/WelcomePage'
import OnboardingQuiz from './components/OnboardingQuiz'
import GuidedShell from './components/GuidedShell'
import { useApp } from './store'
import { exportDocument } from './api'
import { useTts } from './hooks/useTts'
import { THEMES } from './types'

function App() {
  const {
    mode,
    onboardingDone,
    document,
    error,
    settings,
    setError,
    setDocument,
    setMode,
  } = useApp()
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

  // Route 1: landing page
  if (mode === 'welcome') {
    return <WelcomePage />
  }

  // Route 2: Guided mode — onboarding quiz then guided shell
  if (mode === 'guided') {
    if (!onboardingDone) {
      return <OnboardingQuiz onDone={() => undefined} />
    }
    return (
      <GuidedShell onExport={handleExport}>
        <GuidedContent
          activeIndex={activeIndex}
          speaking={speaking}
          toggle={toggle}
          stop={stop}
        />
      </GuidedShell>
    )
  }

  // Route 3: Expert mode — original toolbar UI, but with the new theme palette
  const theme = THEMES[settings.theme]
  return (
    <div className="h-screen flex font-ui" style={{ background: theme.bg, color: theme.fg }}>
      <Toolbar onExport={handleExport} onReset={() => undefined} />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header
          className="h-14 flex items-center px-5 gap-3 border-b"
          style={{ borderColor: theme.border, background: theme.bg }}
        >
          <BookOpenText className="w-5 h-5" style={{ color: theme.accent }} />
          <h1 className="font-semibold tracking-tight">Bionic Reader · Expert</h1>
          <span className="text-xs opacity-50 ml-2 hidden md:inline">
            mode complet · toutes les options
          </span>
          <button
            onClick={() => setMode('welcome')}
            className="ml-2 text-xs flex items-center gap-1 opacity-60 hover:opacity-100"
            title="Retour à l'accueil"
          >
            <Home className="w-3.5 h-3.5" /> accueil
          </button>
          <button
            onClick={() => setMode('guided')}
            className="text-xs flex items-center gap-1 opacity-60 hover:opacity-100"
            title="Mode guidé"
          >
            <Compass className="w-3.5 h-3.5" /> guidé
          </button>
          {document && (
            <button
              onClick={() => setDocument(null)}
              className="ml-auto text-sm opacity-70 hover:opacity-100"
            >
              Charger un autre fichier
            </button>
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
              <p className="text-center text-xs opacity-50 mt-6 max-w-md mx-auto">
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

function GuidedContent({
  activeIndex,
  speaking,
  toggle,
  stop,
}: {
  activeIndex: number | null
  speaking: boolean
  toggle: () => void
  stop: () => void
}) {
  const { document, settings, error } = useApp()

  return (
    <div className="h-full flex flex-col relative">
      {error && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 z-30 bg-rose-100 border border-rose-300 text-rose-800 rounded-lg px-4 py-2 flex items-center gap-2 shadow text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}
      {!document ? (
        <div className="flex-1 flex items-center justify-center px-4">
          <Uploader />
        </div>
      ) : settings.rsvpEnabled ? (
        <RsvpView />
      ) : (
        <>
          {settings.ttsEnabled && (
            <TtsBar speaking={speaking} onToggle={toggle} onStop={stop} />
          )}
          <div className="flex-1 overflow-hidden">
            <Reader ttsActiveWord={activeIndex} />
          </div>
        </>
      )}
    </div>
  )
}

export default App

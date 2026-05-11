import { useState } from 'react'
import {
  Volume2,
  VolumeX,
  Wind,
  Zap,
  RefreshCw,
  Sliders,
  Home,
  FileDown,
} from 'lucide-react'
import { useApp } from '../store'
import { PROFILE_LABELS } from '../store'
import type { ReadingProfile, Settings } from '../types'
import { THEMES } from '../types'
import { exportDocument } from '../api'

/**
 * Guided shell — the simplified UI shown to onboarded users.
 *
 * Three affordances visible: "plus calme" / "plus de bionique" / "écouter".
 * Everything else hidden behind a soft footer with mode-switch + reset.
 *
 * No tabs, no panels, no jargon.
 */
export default function GuidedShell({
  children,
  onExport,
}: {
  children: React.ReactNode
  onExport: (fmt: 'html' | 'docx' | 'txt') => void
}) {
  const { settings, setSettings, setMode, profile, setOnboardingDone, applyProfile, document } =
    useApp()
  const [exportOpen, setExportOpen] = useState(false)

  const theme = THEMES[settings.theme]

  function calmer() {
    // Move along the quietness axis toward "cocoon"
    const newQuietness = Math.min(2, settings.quietness + 1) as 0 | 1 | 2
    const patch: Partial<Settings> = {
      quietness: newQuietness,
      fixationRatio: Math.max(0.3, settings.fixationRatio - 0.05),
      focusModeStrength: Math.min(1, settings.focusModeStrength + 0.05),
      lineHeight: Math.min(2.0, settings.lineHeight + 0.05),
      fontSize: Math.min(22, settings.fontSize + 1),
      colorVowels: false,
      colorFirstLetter: false,
      useColorInsteadOfBold: false,
      posColoring: false,
    }
    setSettings(patch)
  }

  function more() {
    // Move along the quietness axis toward "tonique" — more bionic guidance
    const newQuietness = Math.max(0, settings.quietness - 1) as 0 | 1 | 2
    const patch: Partial<Settings> = {
      quietness: newQuietness,
      bionicEnabled: true,
      fixationRatio: Math.min(0.6, settings.fixationRatio + 0.05),
      eyeAnchor: true,
    }
    setSettings(patch)
  }

  function toggleTts() {
    setSettings({ ttsEnabled: !settings.ttsEnabled })
  }

  return (
    <div
      className="h-screen w-full flex flex-col font-ui relative"
      style={{ background: theme.bg, color: theme.fg }}
    >
      {/* Slim top progress / context bar */}
      <header
        className="flex items-center gap-3 px-4 py-2.5 border-b text-sm shrink-0"
        style={{ borderColor: theme.border }}
      >
        <button
          onClick={() => setMode('welcome')}
          className="opacity-70 hover:opacity-100 flex items-center gap-1.5 px-2 py-1 rounded-lg"
          title="Retour à l'accueil"
        >
          <Home className="w-4 h-4" />
        </button>
        {profile && (
          <span
            className="text-xs px-2.5 py-1 rounded-full"
            style={{ background: theme.accent + '22', color: theme.accent }}
          >
            {PROFILE_LABELS[profile].name}
          </span>
        )}
        <span className="opacity-60 text-xs hidden md:inline truncate">
          {document ? document.filename : 'Mode guidé · choisis un fichier ci-dessous'}
        </span>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => {
              setOnboardingDone(false)
              applyProfile(null as ReadingProfile)
              setMode('guided')
            }}
            className="opacity-70 hover:opacity-100 text-xs px-2.5 py-1 rounded-lg flex items-center gap-1.5"
            title="Refaire le quiz"
          >
            <RefreshCw className="w-3.5 h-3.5" /> quiz
          </button>
          <button
            onClick={() => setMode('expert')}
            className="opacity-70 hover:opacity-100 text-xs px-2.5 py-1 rounded-lg flex items-center gap-1.5"
            title="Mode expert"
          >
            <Sliders className="w-3.5 h-3.5" /> expert
          </button>
        </div>
      </header>

      {/* Main reading area */}
      <div className="flex-1 overflow-hidden">{children}</div>

      {/* Soft bottom action bar — only 3 affordances + export */}
      <footer
        className="shrink-0 border-t flex items-center gap-2 px-4 py-2.5"
        style={{ borderColor: theme.border, background: theme.bg }}
      >
        <GuidedButton onClick={calmer} active={settings.quietness === 2}>
          <Wind className="w-4 h-4" /> Plus calme
        </GuidedButton>
        <GuidedButton onClick={more} active={settings.quietness === 0}>
          <Zap className="w-4 h-4" /> Plus de bionique
        </GuidedButton>
        <GuidedButton onClick={toggleTts} active={settings.ttsEnabled}>
          {settings.ttsEnabled ? (
            <Volume2 className="w-4 h-4" />
          ) : (
            <VolumeX className="w-4 h-4" />
          )}
          {settings.ttsEnabled ? 'Audio' : 'Écouter'}
        </GuidedButton>

        <QuietnessIndicator value={settings.quietness} theme={theme} />

        <div className="ml-auto relative">
          {document && (
            <>
              <button
                onClick={() => setExportOpen((o) => !o)}
                className="px-3 py-2 rounded-lg flex items-center gap-1.5 text-sm opacity-80 hover:opacity-100"
                style={{ background: theme.border + '55' }}
              >
                <FileDown className="w-4 h-4" /> Export
              </button>
              {exportOpen && (
                <div
                  className="absolute bottom-full right-0 mb-2 rounded-xl shadow-lg overflow-hidden text-sm min-w-[160px]"
                  style={{ background: theme.bg, border: `1px solid ${theme.border}` }}
                >
                  {(['html', 'docx', 'txt'] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => {
                        onExport(f)
                        setExportOpen(false)
                      }}
                      className="block w-full text-left px-4 py-2.5 hover:bg-black/5"
                    >
                      {f.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </footer>
    </div>
  )
}

function GuidedButton({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode
  active?: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="px-3.5 py-2 rounded-lg flex items-center gap-1.5 text-sm transition-all"
      style={{
        background: active ? 'rgba(0,0,0,0.08)' : 'transparent',
        border: '1px solid rgba(0,0,0,0.07)',
      }}
    >
      {children}
    </button>
  )
}

function QuietnessIndicator({ value, theme }: { value: 0 | 1 | 2; theme: { accent: string; muted: string } }) {
  const labels = ['Tonique', 'Équilibré', 'Cocoon']
  return (
    <div className="hidden md:flex items-center gap-1.5 ml-2 text-xs opacity-70">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full"
            style={{ background: i === value ? theme.accent : theme.muted + '55' }}
          />
        ))}
      </div>
      <span className="tabular-nums">{labels[value]}</span>
    </div>
  )
}

// Re-export not strictly needed but useful for stories
export { exportDocument }

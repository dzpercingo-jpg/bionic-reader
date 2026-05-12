import {
  BookOpen,
  Eye,
  Palette,
  Type,
  Sparkles,
  Volume2,
  Zap,
  Settings as Cog,
  RotateCcw,
  Atom,
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useApp } from '../store'
import type { Settings } from '../types'
import { THEMES } from '../types'

type Panel = 'bionic' | 'advanced' | 'typo' | 'theme' | 'aids' | 'rsvp' | 'tts' | 'export'

const PANELS: { id: Panel; label: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'bionic', label: 'Bionic', icon: BookOpen },
  { id: 'advanced', label: 'Avancé', icon: Atom },
  { id: 'typo', label: 'Typo', icon: Type },
  { id: 'theme', label: 'Couleurs', icon: Palette },
  { id: 'aids', label: 'Aides', icon: Eye },
  { id: 'rsvp', label: 'RSVP', icon: Zap },
  { id: 'tts', label: 'Audio', icon: Volume2 },
  { id: 'export', label: 'Export', icon: Sparkles },
]

import type { ExportFormat } from '../types'

export default function Toolbar({
  onExport,
  onReset,
}: {
  onExport: (fmt: ExportFormat) => void
  onReset: () => void
}) {
  const [active, setActive] = useState<Panel | null>('bionic')
  const { settings, setSettings, resetSettings } = useApp()

  return (
    <aside className="w-[340px] shrink-0 bg-white border-r border-stone-200 flex flex-col h-full overflow-hidden">
      <header className="p-4 border-b border-stone-200 flex items-center gap-2">
        <Cog className="w-5 h-5 text-stone-700" />
        <h1 className="font-semibold text-stone-900">Boîte à outils</h1>
        <button
          onClick={() => {
            resetSettings()
            onReset()
          }}
          className="ml-auto text-xs text-stone-500 hover:text-rose-600 flex items-center gap-1"
          title="Réinitialiser les paramètres"
        >
          <RotateCcw className="w-3.5 h-3.5" /> reset
        </button>
      </header>

      <nav className="px-3 pt-3 grid grid-cols-4 gap-1">
        {PANELS.map((p) => {
          const Icon = p.icon
          return (
            <button
              key={p.id}
              onClick={() => setActive((a) => (a === p.id ? null : p.id))}
              className={clsx(
                'flex flex-col items-center justify-center px-1 py-2 rounded-lg text-[11px] gap-1',
                active === p.id
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-stone-600 hover:bg-stone-100',
              )}
            >
              <Icon className="w-4 h-4" />
              {p.label}
            </button>
          )
        })}
      </nav>

      <div className="flex-1 overflow-y-auto br-scroll p-4 space-y-6">
        {active === 'bionic' && <BionicPanel settings={settings} setSettings={setSettings} />}
        {active === 'advanced' && <AdvancedPanel settings={settings} setSettings={setSettings} />}
        {active === 'typo' && <TypoPanel settings={settings} setSettings={setSettings} />}
        {active === 'theme' && <ThemePanel settings={settings} setSettings={setSettings} />}
        {active === 'aids' && <AidsPanel settings={settings} setSettings={setSettings} />}
        {active === 'rsvp' && <RsvpPanel settings={settings} setSettings={setSettings} />}
        {active === 'tts' && <TtsPanel settings={settings} setSettings={setSettings} />}
        {active === 'export' && <ExportPanel onExport={onExport} />}
      </div>
    </aside>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
        {title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description?: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <label className="flex items-start justify-between gap-3 cursor-pointer">
      <div>
        <div className="text-sm font-medium text-stone-800">{label}</div>
        {description && <div className="text-xs text-stone-500 mt-0.5">{description}</div>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={clsx(
          'mt-1 relative inline-flex h-5 w-9 shrink-0 rounded-full transition-colors',
          checked ? 'bg-indigo-600' : 'bg-stone-300',
        )}
        aria-pressed={checked}
      >
        <span
          className={clsx(
            'absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
            checked && 'translate-x-4',
          )}
        />
      </button>
    </label>
  )
}

function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  unit,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit?: string
  onChange: (v: number) => void
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm mb-1">
        <span className="text-stone-700">{label}</span>
        <span className="text-xs text-stone-500 tabular-nums">
          {value}
          {unit ?? ''}
        </span>
      </div>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-indigo-600"
      />
    </div>
  )
}

function ColorRow({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label className="flex items-center justify-between text-sm">
      <span className="text-stone-700">{label}</span>
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-7 w-12 rounded border border-stone-300 cursor-pointer"
      />
    </label>
  )
}

interface PanelProps {
  settings: Settings
  setSettings: (p: Partial<Settings>) => void
}

function BionicPanel({ settings, setSettings }: PanelProps) {
  return (
    <Section title="Lecture bionique">
      <Toggle
        label="Activer la lecture bionique"
        description="Met en évidence les premières lettres pour guider la saccade."
        checked={settings.bionicEnabled}
        onChange={(v) => setSettings({ bionicEnabled: v })}
      />
      <Slider
        label="Ratio de fixation"
        value={Math.round(settings.fixationRatio * 100)}
        min={20}
        max={80}
        unit="%"
        onChange={(v) => setSettings({ fixationRatio: v / 100 })}
      />
      <Toggle
        label="Saccade adaptative"
        description="Ajuste le préfixe selon la longueur du mot (recommandé)."
        checked={settings.saccadeAdaptive}
        onChange={(v) => setSettings({ saccadeAdaptive: v })}
      />
      <Slider
        label="Longueur min. du mot"
        value={settings.minWordLength}
        min={1}
        max={6}
        onChange={(v) => setSettings({ minWordLength: v })}
      />
      <Toggle
        label="Couleur plutôt que gras"
        description="Utile sur les écrans à mauvais rendu de gras."
        checked={settings.useColorInsteadOfBold}
        onChange={(v) => setSettings({ useColorInsteadOfBold: v })}
      />
      {settings.useColorInsteadOfBold && (
        <ColorRow
          label="Couleur du préfixe"
          value={settings.prefixColor}
          onChange={(v) => setSettings({ prefixColor: v })}
        />
      )}
      <Toggle
        label="Colorer les voyelles"
        description="Aide au décodage phonologique."
        checked={settings.colorVowels}
        onChange={(v) => setSettings({ colorVowels: v })}
      />
      {settings.colorVowels && (
        <ColorRow
          label="Couleur des voyelles"
          value={settings.vowelColor}
          onChange={(v) => setSettings({ vowelColor: v })}
        />
      )}
      <Toggle
        label="Première lettre colorée"
        checked={settings.colorFirstLetter}
        onChange={(v) => setSettings({ colorFirstLetter: v })}
      />
      {settings.colorFirstLetter && (
        <ColorRow
          label="Couleur"
          value={settings.firstLetterColor}
          onChange={(v) => setSettings({ firstLetterColor: v })}
        />
      )}
    </Section>
  )
}

function AdvancedPanel({ settings, setSettings }: PanelProps) {
  return (
    <>
      <Section title="Techniques avancées (conseil d'experts)">
        <p className="text-xs text-stone-500">
          Combinaison de techniques issues de la recherche en neurosciences de la lecture, design
          d&apos;information et clinique TDAH. Voir COUNCIL.md du repo.
        </p>
        <Toggle
          label="Point OVP (Dehaene)"
          description="Petit point gris à la position de fixation optimale de chaque mot."
          checked={settings.eyeAnchor}
          onChange={(v) => setSettings({ eyeAnchor: v })}
        />
        {settings.eyeAnchor && (
          <ColorRow
            label="Couleur du point"
            value={settings.eyeAnchorColor}
            onChange={(v) => setSettings({ eyeAnchorColor: v })}
          />
        )}
        <Toggle
          label="Phrase chunking (Pinker)"
          description="Petite respiration visuelle tous les N mots."
          checked={settings.phraseChunking}
          onChange={(v) => setSettings({ phraseChunking: v })}
        />
        {settings.phraseChunking && (
          <Slider
            label="Mots par groupe"
            value={settings.phraseChunkSize}
            min={2}
            max={8}
            onChange={(v) => setSettings({ phraseChunkSize: v })}
          />
        )}
        <Toggle
          label="POS coloring (Pinker, Treisman)"
          description="Colore subtilement les connecteurs logiques (mais, donc, parce que…)."
          checked={settings.posColoring}
          onChange={(v) => setSettings({ posColoring: v })}
        />
        {settings.posColoring && (
          <ColorRow
            label="Couleur connecteurs"
            value={settings.posColor}
            onChange={(v) => setSettings({ posColor: v })}
          />
        )}
        <Toggle
          label="Cadence pulse (Hallowell)"
          description="Une ligne grise descend lentement à travers le texte."
          checked={settings.pulseCadence}
          onChange={(v) => setSettings({ pulseCadence: v })}
        />
        {settings.pulseCadence && (
          <Slider
            label="Vitesse de cadence"
            value={settings.pulseCadenceWpm}
            min={120}
            max={400}
            step={10}
            unit=" wpm"
            onChange={(v) => setSettings({ pulseCadenceWpm: v })}
          />
        )}
        <Toggle
          label="Respiration de mot (Csikszentmihalyi)"
          description="Pulse de poids sur le mot en cours de lecture audio (au lieu du surlignage jaune)."
          checked={settings.breathingWord}
          onChange={(v) => setSettings({ breathingWord: v })}
        />
      </Section>
    </>
  )
}

function TypoPanel({ settings, setSettings }: PanelProps) {
  return (
    <>
      <Section title="Police">
        <select
          value={settings.font}
          onChange={(e) => setSettings({ font: e.target.value as Settings['font'] })}
          className="w-full px-3 py-2 text-sm border border-stone-300 rounded-md bg-white"
        >
          <option value="lexend">Lexend (recommandé pour la lecture)</option>
          <option value="atkinson">Atkinson Hyperlegible</option>
          <option value="opendyslexic">OpenDyslexic</option>
          <option value="inter">Inter</option>
          <option value="georgia">Georgia (sérif)</option>
          <option value="system">Système</option>
          <option value="mono">Monospace</option>
        </select>
        <Slider
          label="Taille"
          value={settings.fontSize}
          min={12}
          max={32}
          unit="px"
          onChange={(v) => setSettings({ fontSize: v })}
        />
        <Slider
          label="Poids"
          value={settings.fontWeight}
          min={300}
          max={700}
          step={100}
          onChange={(v) => setSettings({ fontWeight: v })}
        />
      </Section>
      <Section title="Espacement">
        <Slider
          label="Hauteur de ligne"
          value={settings.lineHeight}
          min={1.0}
          max={2.5}
          step={0.05}
          onChange={(v) => setSettings({ lineHeight: v })}
        />
        <Slider
          label="Inter-lettre"
          value={settings.letterSpacing}
          min={0}
          max={0.2}
          step={0.005}
          unit="em"
          onChange={(v) => setSettings({ letterSpacing: v })}
        />
        <Slider
          label="Inter-mot"
          value={settings.wordSpacing}
          min={0}
          max={1}
          step={0.05}
          unit="em"
          onChange={(v) => setSettings({ wordSpacing: v })}
        />
        <Slider
          label="Espacement paragraphes"
          value={settings.paragraphSpacing}
          min={0.3}
          max={3}
          step={0.1}
          unit="em"
          onChange={(v) => setSettings({ paragraphSpacing: v })}
        />
      </Section>
      <Section title="Mise en page">
        <Slider
          label="Largeur de ligne"
          value={settings.maxLineWidth}
          min={40}
          max={110}
          unit="ch"
          onChange={(v) => setSettings({ maxLineWidth: v })}
        />
        <Toggle
          label="Justification"
          description="Désactivée par défaut (rivières blanches)."
          checked={settings.justify}
          onChange={(v) => setSettings({ justify: v })}
        />
      </Section>
    </>
  )
}

function ThemePanel({ settings, setSettings }: PanelProps) {
  return (
    <>
      <Section title="Thème">
        <div className="grid grid-cols-3 gap-2">
          {(Object.keys(THEMES) as (keyof typeof THEMES)[]).map((key) => {
            const t = THEMES[key]
            return (
              <button
                key={key}
                onClick={() => setSettings({ theme: key })}
                className={clsx(
                  'rounded-lg p-2 text-xs border-2 transition',
                  settings.theme === key ? 'border-indigo-500' : 'border-transparent',
                )}
                style={{ background: t.bg, color: t.fg }}
              >
                {key}
              </button>
            )
          })}
        </div>
      </Section>
      <Section title="Couleurs">
        <ColorRow
          label="Fond personnalisé"
          value={settings.customBg}
          onChange={(v) => setSettings({ customBg: v })}
        />
        <ColorRow
          label="Texte personnalisé"
          value={settings.customFg}
          onChange={(v) => setSettings({ customFg: v })}
        />
      </Section>
      <Section title="Overlay coloré (Irlen)">
        <Toggle
          label="Activer l'overlay"
          description="Filtre coloré sur l'écran (utile sensibilité scotopique)."
          checked={settings.overlayEnabled}
          onChange={(v) => setSettings({ overlayEnabled: v })}
        />
        {settings.overlayEnabled && (
          <>
            <ColorRow
              label="Couleur"
              value={settings.overlayColor}
              onChange={(v) => setSettings({ overlayColor: v })}
            />
            <Slider
              label="Opacité"
              value={Math.round(settings.overlayOpacity * 100)}
              min={5}
              max={70}
              unit="%"
              onChange={(v) => setSettings({ overlayOpacity: v / 100 })}
            />
          </>
        )}
      </Section>
    </>
  )
}

function AidsPanel({ settings, setSettings }: PanelProps) {
  return (
    <>
      <Section title="Repères visuels">
        <Toggle
          label="Reading ruler"
          description="Une barre suit le pointeur pour guider la ligne courante."
          checked={settings.rulerEnabled}
          onChange={(v) => setSettings({ rulerEnabled: v })}
        />
        <Toggle
          label="Mode focus"
          description="Atténue les paragraphes hors du paragraphe courant."
          checked={settings.focusModeEnabled}
          onChange={(v) => setSettings({ focusModeEnabled: v })}
        />
        {settings.focusModeEnabled && (
          <Slider
            label="Atténuation"
            value={Math.round(settings.focusModeStrength * 100)}
            min={20}
            max={90}
            unit="%"
            onChange={(v) => setSettings({ focusModeStrength: v / 100 })}
          />
        )}
        <Toggle
          label="Chunking visuel"
          description="Insère des espaces tous les N mots pour découper la ligne."
          checked={settings.chunkingEnabled}
          onChange={(v) => setSettings({ chunkingEnabled: v })}
        />
        {settings.chunkingEnabled && (
          <Slider
            label="Mots par chunk"
            value={settings.chunkSize}
            min={3}
            max={30}
            onChange={(v) => setSettings({ chunkSize: v })}
          />
        )}
      </Section>
    </>
  )
}

function RsvpPanel({ settings, setSettings }: PanelProps) {
  return (
    <Section title="RSVP — flash de mots">
      <p className="text-xs text-stone-500">
        Affiche les mots un à un au même endroit. Supprime les saccades, utile pour un sprint de
        lecture rapide.
      </p>
      <Toggle
        label="Activer le mode RSVP"
        checked={settings.rsvpEnabled}
        onChange={(v) => setSettings({ rsvpEnabled: v })}
      />
      <Slider
        label="Vitesse"
        value={settings.rsvpWpm}
        min={100}
        max={1000}
        step={25}
        unit=" wpm"
        onChange={(v) => setSettings({ rsvpWpm: v })}
      />
      <Slider
        label="Mots par flash"
        value={settings.rsvpChunkSize}
        min={1}
        max={5}
        onChange={(v) => setSettings({ rsvpChunkSize: v })}
      />
      <Toggle
        label="Pause sur ponctuation"
        checked={settings.rsvpPauseOnPunct}
        onChange={(v) => setSettings({ rsvpPauseOnPunct: v })}
      />
    </Section>
  )
}

function TtsPanel({ settings, setSettings }: PanelProps) {
  return (
    <Section title="Synthèse vocale (Web Speech API)">
      <Toggle
        label="Activer la lecture audio"
        description="Lit le texte à voix haute avec surlignage synchronisé."
        checked={settings.ttsEnabled}
        onChange={(v) => setSettings({ ttsEnabled: v })}
      />
      <Slider
        label="Vitesse"
        value={settings.ttsRate}
        min={0.5}
        max={2}
        step={0.05}
        unit="×"
        onChange={(v) => setSettings({ ttsRate: v })}
      />
      <Toggle
        label="Surlignage du mot lu"
        checked={settings.ttsHighlight}
        onChange={(v) => setSettings({ ttsHighlight: v })}
      />
    </Section>
  )
}

function ExportPanel({ onExport }: { onExport: (fmt: ExportFormat) => void }) {
  const { sourceFile } = useApp()
  const ext = sourceFile?.name.split('.').pop()?.toLowerCase() ?? ''
  const canInplace = ['pdf', 'doc', 'docx', 'pptx', 'xlsx'].includes(ext)
  const inplaceLabel: Record<string, string> = {
    pdf: 'PDF (préserve images, vecteurs, signatures + OCR si scanné)',
    doc: 'Word 97-2003 → DOCX (préserve images & contenu)',
    docx: 'Word (préserve images, tableaux, styles)',
    pptx: 'PowerPoint (préserve diapos & images)',
    xlsx: 'Excel (préserve formules & graphes)',
  }
  return (
    <Section title="Export">
      <p className="text-xs text-stone-500">
        Génère un nouveau fichier transformé. Le fichier source d&apos;origine n&apos;est jamais
        modifié.
      </p>
      <div className="grid grid-cols-1 gap-2">
        {canInplace && (
          <button
            onClick={() => onExport('inplace')}
            className="px-3 py-2 text-sm rounded-md bg-emerald-600 text-white hover:bg-emerald-700 flex flex-col items-start"
          >
            <span className="font-medium">Garder le format d&apos;origine</span>
            <span className="text-[10px] opacity-80 mt-0.5">{inplaceLabel[ext]}</span>
          </button>
        )}
        <button
          onClick={() => onExport('html')}
          className="px-3 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
        >
          Télécharger en HTML
        </button>
        <button
          onClick={() => onExport('docx')}
          className="px-3 py-2 text-sm rounded-md bg-stone-800 text-white hover:bg-stone-900"
        >
          Télécharger en DOCX (Word)
        </button>
        <button
          onClick={() => onExport('txt')}
          className="px-3 py-2 text-sm rounded-md border border-stone-300 hover:bg-stone-100"
        >
          Télécharger en TXT brut
        </button>
      </div>
    </Section>
  )
}

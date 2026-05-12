import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronRight, BookOpenText, Loader2, Brain, Activity, Timer } from 'lucide-react'
import { useApp, PROFILE_LABELS } from '../store'
import { THEMES, type Settings } from '../types'
import type {
  AsrsAnswerPayload,
  PvtTrialPayload,
  ReadingTrialPayload,
  AssessmentResultResp,
} from '../api'
import { scoreOnboarding } from '../api'

/**
 * Evidence-based ADHD-aware onboarding (replaces the original 6-question
 * declarative quiz). See `RESEARCH_GUIDED_MODE.md` for the design
 * rationale, the clinical literature it draws from, and the scoring
 * equations (which live on the backend in `app/onboarding/`).
 *
 * Stages
 *   1. Intro         — clear, jargon-free explanation, ~15 s.
 *   2. ASRS-v1.1     — 6 Likert questions (validated WHO screener). ~45 s.
 *   3. PVT           — Psychomotor Vigilance Task, 16 trials. ~60 s.
 *   4. Reading       — read a calibrated paragraph (60 words). ~30 s.
 *   5. Results       — display profile vector + recommended preset.
 *
 * ADHD-friendly UX choices throughout
 *   - One focal action per screen, generous whitespace.
 *   - Visible progress bar + step counter; never any hidden state.
 *   - `prefers-reduced-motion` honored everywhere (transitions disable).
 *   - Large 56 px+ buttons, ≥7:1 contrast, sans-serif system font stack.
 *   - The user can SKIP any stage (the scorer degrades confidence
 *     gracefully — it never refuses a partial assessment).
 */

type Stage = 'intro' | 'asrs' | 'pvt' | 'reading' | 'submitting' | 'result'

const ASRS_QUESTIONS: { qid: AsrsAnswerPayload['qid']; text: string }[] = [
  {
    qid: 'q1',
    text:
      'Quand tu dois rester concentré sur une tâche ennuyeuse, à quelle fréquence as-tu du mal à tenir l’attention jusqu’au bout ?',
  },
  {
    qid: 'q2',
    text:
      'Quand tu fais une tâche qui demande de l’organisation, à quelle fréquence as-tu du mal à mettre les choses dans l’ordre ?',
  },
  {
    qid: 'q3',
    text:
      'À quelle fréquence oublies-tu des rendez-vous ou des engagements ?',
  },
  {
    qid: 'q4',
    text:
      'Quand tu dois te lancer dans une tâche qui demande beaucoup de réflexion, à quelle fréquence évites-tu ou repousses-tu ?',
  },
  {
    qid: 'q5',
    text:
      'À quelle fréquence bouges-tu, gigotes-tu, ou as-tu du mal à rester en place pendant longtemps ?',
  },
  {
    qid: 'q6',
    text:
      'À quelle fréquence te sens-tu poussé à agir, comme si tu étais "monté sur ressort" ?',
  },
]

const ASRS_LABELS = ['Jamais', 'Rarement', 'Parfois', 'Souvent', 'Très souvent']

const READING_PARAGRAPH = `La lecture bionique guide l'oeil en mettant en gras la moitié initiale de chaque mot, ce qui aide les lecteurs présentant des troubles de l'attention à fixer leur regard. Cette technique exploite la manière dont le cerveau reconnaît les mots à partir de leur préfixe, sans avoir besoin de lire chaque lettre. Quand tu auras fini de lire ce paragraphe, clique sur le bouton.`
const READING_WORD_COUNT = READING_PARAGRAPH.trim().split(/\s+/).length

interface OnboardingV2Props {
  onDone: () => void
}

export default function OnboardingV2({ onDone }: OnboardingV2Props) {
  const { applyProfile, setOnboardingDone, setSettings } = useApp()
  const theme = THEMES.paper
  const reducedMotion = useReducedMotion()

  const [stage, setStage] = useState<Stage>('intro')
  const [asrs, setAsrs] = useState<AsrsAnswerPayload[]>([])
  const [pvt, setPvt] = useState<PvtTrialPayload[]>([])
  const [reading, setReading] = useState<ReadingTrialPayload | null>(null)
  const [result, setResult] = useState<AssessmentResultResp | null>(null)
  const [error, setError] = useState<string | null>(null)

  const totalStages = 5
  const stageIndex: Record<Stage, number> = {
    intro: 1,
    asrs: 2,
    pvt: 3,
    reading: 4,
    submitting: 5,
    result: 5,
  }
  const progress = (stageIndex[stage] / totalStages) * 100

  const submit = useCallback(
    async (overrides?: {
      asrs?: AsrsAnswerPayload[]
      pvt?: PvtTrialPayload[]
      reading?: ReadingTrialPayload | null
    }) => {
      setStage('submitting')
      setError(null)
      try {
        const r = await scoreOnboarding({
          asrs: overrides?.asrs ?? asrs,
          pvt: overrides?.pvt ?? pvt,
          reading: overrides?.reading !== undefined ? overrides.reading : reading,
          locale: navigator.language,
        })
        setResult(r)
        setStage('result')
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err))
        setStage('result')
      }
    },
    [asrs, pvt, reading],
  )

  function commit() {
    if (!result) return
    applyProfile(result.preset.profile)
    // Override with interpolated settings (numeric blend). The applyProfile
    // call above seeded the four anchor defaults; we now layer the
    // backend-interpolated values on top so settings reflect the user's
    // actual profile, not just the winning anchor.
    const overrides = remapBackendSettings(result.preset.settings)
    setSettings(overrides)
    setOnboardingDone(true)
    onDone()
  }

  return (
    <div
      className="h-screen w-full flex items-center justify-center px-4 font-ui"
      style={{ background: theme.bg, color: theme.fg }}
    >
      <div className="w-full max-w-2xl">
        {/* --- Header / progress --- */}
        <div className="flex items-center gap-2 mb-6">
          <BookOpenText className="w-5 h-5" style={{ color: theme.accent }} />
          <span className="text-sm font-medium">Mode guidé · calibration</span>
          <span className="ml-auto text-xs opacity-70 tabular-nums">
            étape {stageIndex[stage]} / {totalStages}
          </span>
        </div>
        <div
          className="h-[3px] rounded-full mb-12"
          style={{ background: theme.border }}
        >
          <div
            className="h-full rounded-full"
            style={{
              width: `${progress}%`,
              background: theme.accent,
              transition: reducedMotion ? 'none' : 'width 0.4s ease',
            }}
          />
        </div>

        {/* --- Stage body --- */}
        {stage === 'intro' && (
          <IntroStage onContinue={() => setStage('asrs')} onSkip={() => submit({ asrs: [], pvt: [], reading: null })} />
        )}
        {stage === 'asrs' && (
          <AsrsStage
            onDone={(answers) => {
              setAsrs(answers)
              setStage('pvt')
            }}
            onSkip={() => setStage('pvt')}
          />
        )}
        {stage === 'pvt' && (
          <PvtStage
            onDone={(trials) => {
              setPvt(trials)
              setStage('reading')
            }}
            onSkip={() => setStage('reading')}
          />
        )}
        {stage === 'reading' && (
          <ReadingStage
            onDone={(trial) => {
              setReading(trial)
              void submit({ reading: trial })
            }}
            onSkip={() => void submit({ reading: null })}
          />
        )}
        {stage === 'submitting' && (
          <div className="flex items-center gap-3 text-base opacity-80">
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyse en cours…
          </div>
        )}
        {stage === 'result' && (
          <ResultStage
            result={result}
            error={error}
            onCommit={commit}
            onRedo={() => {
              setAsrs([])
              setPvt([])
              setReading(null)
              setResult(null)
              setStage('intro')
            }}
          />
        )}
      </div>
    </div>
  )
}

// ---------- Stage 1: intro ------------------------------------------------

function IntroStage({ onContinue, onSkip }: { onContinue: () => void; onSkip: () => void }) {
  const theme = THEMES.paper
  return (
    <div>
      <h1 className="text-2xl md:text-3xl font-semibold leading-tight mb-3">
        Calibrons ton mode de lecture.
      </h1>
      <p className="text-base opacity-80 leading-relaxed mb-2">
        On va te demander :
      </p>
      <ul className="space-y-3 mb-8 text-base">
        <li className="flex items-start gap-3">
          <Brain className="w-5 h-5 mt-0.5 shrink-0" style={{ color: theme.accent }} />
          <span>
            6 questions courtes sur ton attention au quotidien (validées par l’OMS).
          </span>
        </li>
        <li className="flex items-start gap-3">
          <Activity className="w-5 h-5 mt-0.5 shrink-0" style={{ color: theme.accent }} />
          <span>
            Un petit jeu de réflexes (45&nbsp;secondes) — mesure objective, pas un avis.
          </span>
        </li>
        <li className="flex items-start gap-3">
          <Timer className="w-5 h-5 mt-0.5 shrink-0" style={{ color: theme.accent }} />
          <span>Lire un court paragraphe pour calibrer ta vitesse.</span>
        </li>
      </ul>
      <p className="text-sm opacity-70 leading-relaxed mb-8">
        Ce n’est <strong>pas un diagnostic</strong>. C’est juste pour adapter
        l’affichage (taille, gras, vitesse RSVP…) à ta façon de lire. Tu peux
        passer n’importe quelle étape — on ajuste l’estimation en conséquence.
      </p>
      <div className="flex flex-col-reverse sm:flex-row gap-3">
        <button
          onClick={onSkip}
          className="px-5 py-3.5 rounded-xl text-sm opacity-70 hover:opacity-100"
          style={{ border: `1px solid ${theme.border}`, background: 'transparent', color: theme.fg }}
        >
          Tout passer (utiliser un profil par défaut)
        </button>
        <button
          onClick={onContinue}
          className="flex-1 px-5 py-3.5 rounded-xl font-medium flex items-center justify-center gap-2"
          style={{ background: theme.accent, color: theme.bg }}
        >
          Commencer <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// ---------- Stage 2: ASRS -------------------------------------------------

function AsrsStage({
  onDone,
  onSkip,
}: {
  onDone: (answers: AsrsAnswerPayload[]) => void
  onSkip: () => void
}) {
  const theme = THEMES.paper
  const [i, setI] = useState(0)
  const [answers, setAnswers] = useState<AsrsAnswerPayload[]>([])
  const q = ASRS_QUESTIONS[i]
  const subProgress = ((i + 1) / ASRS_QUESTIONS.length) * 100

  function answer(score: 0 | 1 | 2 | 3 | 4) {
    const next = [...answers, { qid: q.qid, score }]
    if (i + 1 >= ASRS_QUESTIONS.length) onDone(next)
    else {
      setAnswers(next)
      setI(i + 1)
    }
  }

  return (
    <div>
      <p className="text-sm opacity-70 mb-2 tabular-nums">
        question {i + 1} / {ASRS_QUESTIONS.length}
      </p>
      <div className="h-[2px] rounded-full mb-8" style={{ background: theme.border }}>
        <div className="h-full rounded-full" style={{ width: `${subProgress}%`, background: theme.muted }} />
      </div>
      <h2 className="text-xl md:text-2xl font-semibold leading-snug mb-8">
        {q.text}
      </h2>
      <div className="space-y-2.5">
        {ASRS_LABELS.map((label, score) => (
          <button
            key={label}
            onClick={() => answer(score as 0 | 1 | 2 | 3 | 4)}
            className="w-full text-left px-5 py-4 rounded-xl"
            style={{
              background: '#f5f1e8',
              border: `1px solid ${theme.border}`,
              color: theme.fg,
              minHeight: 56,
            }}
          >
            <span className="font-medium">{label}</span>
          </button>
        ))}
      </div>
      <div className="flex justify-end mt-6">
        <button onClick={onSkip} className="text-xs opacity-60 hover:opacity-100 underline">
          Passer cette étape
        </button>
      </div>
    </div>
  )
}

// ---------- Stage 3: PVT --------------------------------------------------

const PVT_TRIAL_COUNT = 16
const PVT_MIN_WAIT_MS = 1000
const PVT_MAX_WAIT_MS = 3000

function PvtStage({
  onDone,
  onSkip,
}: {
  onDone: (trials: PvtTrialPayload[]) => void
  onSkip: () => void
}) {
  const theme = THEMES.paper
  type Phase = 'instr' | 'waiting' | 'stimulus' | 'done'
  const [phase, setPhase] = useState<Phase>('instr')
  const [trials, setTrials] = useState<PvtTrialPayload[]>([])
  const [lastRt, setLastRt] = useState<number | null>(null)
  const [lastFalseStart, setLastFalseStart] = useState(false)

  const stimulusStartRef = useRef<number | null>(null)
  const timeoutRef = useRef<number | null>(null)

  const beginTrial = useCallback(() => {
    setLastRt(null)
    setLastFalseStart(false)
    setPhase('waiting')
    const wait = PVT_MIN_WAIT_MS + Math.random() * (PVT_MAX_WAIT_MS - PVT_MIN_WAIT_MS)
    timeoutRef.current = window.setTimeout(() => {
      stimulusStartRef.current = performance.now()
      setPhase('stimulus')
    }, wait)
  }, [])

  const startBlock = useCallback(() => {
    setTrials([])
    beginTrial()
  }, [beginTrial])

  // Handle key/click for response.
  useEffect(() => {
    function handle() {
      if (phase === 'waiting') {
        // False start.
        if (timeoutRef.current) window.clearTimeout(timeoutRef.current)
        const t: PvtTrialPayload = { rt_ms: 0, false_start: true, lapse: false }
        const next = [...trials, t]
        setTrials(next)
        setLastFalseStart(true)
        setPhase('instr')
        if (next.length >= PVT_TRIAL_COUNT) setPhase('done')
        return
      }
      if (phase === 'stimulus' && stimulusStartRef.current) {
        const rt = performance.now() - stimulusStartRef.current
        stimulusStartRef.current = null
        const t: PvtTrialPayload = { rt_ms: rt, false_start: false, lapse: rt > 500 }
        const next = [...trials, t]
        setTrials(next)
        setLastRt(rt)
        setPhase('instr')
        if (next.length >= PVT_TRIAL_COUNT) setPhase('done')
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.code === 'Space' || e.code === 'Enter') {
        e.preventDefault()
        handle()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, trials])

  // Auto-continue between trials.
  useEffect(() => {
    if (phase === 'instr' && trials.length > 0 && trials.length < PVT_TRIAL_COUNT) {
      const id = window.setTimeout(() => beginTrial(), 900)
      return () => window.clearTimeout(id)
    }
    return undefined
  }, [phase, trials.length, beginTrial])

  useEffect(() => {
    if (phase === 'done') {
      const id = window.setTimeout(() => onDone(trials), 600)
      return () => window.clearTimeout(id)
    }
    return undefined
  }, [phase, trials, onDone])

  function clickResponse() {
    // Synthesize a keyboard-style event for click users.
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Space' }))
  }

  if (phase === 'instr' && trials.length === 0) {
    return (
      <div>
        <h2 className="text-xl md:text-2xl font-semibold mb-3">Test de réflexes (PVT)</h2>
        <p className="text-base opacity-80 leading-relaxed mb-2">
          Fixe le centre de l’écran. Un point gris apparaît puis devient un{' '}
          <span style={{ color: theme.accent, fontWeight: 600 }}>cercle plein</span> après
          un délai imprévisible.
        </p>
        <p className="text-base opacity-80 leading-relaxed mb-2">
          Dès que le cercle se remplit, appuie sur <kbd className="px-2 py-0.5 rounded bg-black/5">Espace</kbd> aussi
          vite que possible.
        </p>
        <p className="text-sm opacity-70 leading-relaxed mb-8">
          {PVT_TRIAL_COUNT} essais courts. Ce n’est pas un examen — c’est juste pour
          mesurer la régularité de ton attention.
        </p>
        <div className="flex flex-col-reverse sm:flex-row gap-3">
          <button
            onClick={onSkip}
            className="px-5 py-3.5 rounded-xl text-sm opacity-70 hover:opacity-100"
            style={{ border: `1px solid ${theme.border}`, background: 'transparent', color: theme.fg }}
          >
            Passer
          </button>
          <button
            onClick={startBlock}
            className="flex-1 px-5 py-3.5 rounded-xl font-medium flex items-center justify-center gap-2"
            style={{ background: theme.accent, color: theme.bg }}
          >
            Lancer le test <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="flex items-center gap-3 text-base opacity-80">
        <Loader2 className="w-5 h-5 animate-spin" />
        Test terminé. Passage à l’étape suivante…
      </div>
    )
  }

  // Active trial (waiting or stimulus) or short-pause between trials.
  return (
    <div className="flex flex-col items-center">
      <p className="text-sm opacity-70 mb-2 tabular-nums">
        essai {Math.min(trials.length + 1, PVT_TRIAL_COUNT)} / {PVT_TRIAL_COUNT}
      </p>
      <button
        onClick={clickResponse}
        className="w-full h-72 rounded-2xl flex items-center justify-center select-none"
        style={{
          background:
            phase === 'stimulus' ? theme.accent : '#f5f1e8',
          border: `1px solid ${theme.border}`,
          cursor: 'pointer',
        }}
        aria-label="Zone de réponse PVT"
      >
        {phase === 'stimulus' ? (
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: theme.bg,
            }}
          />
        ) : (
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: theme.muted,
            }}
          />
        )}
      </button>
      <p className="text-sm opacity-70 mt-4 h-5">
        {phase === 'waiting' && 'Attends que le cercle se remplisse…'}
        {phase === 'instr' && lastFalseStart && 'Trop tôt ! Attends le signal.'}
        {phase === 'instr' && !lastFalseStart && lastRt !== null && `Temps : ${Math.round(lastRt)} ms`}
      </p>
    </div>
  )
}

// ---------- Stage 4: reading speed ----------------------------------------

function ReadingStage({
  onDone,
  onSkip,
}: {
  onDone: (trial: ReadingTrialPayload) => void
  onSkip: () => void
}) {
  const theme = THEMES.paper
  const [started, setStarted] = useState(false)
  const startRef = useRef<number | null>(null)

  function begin() {
    startRef.current = performance.now()
    setStarted(true)
  }
  function finish() {
    if (!startRef.current) return
    const elapsed_ms = performance.now() - startRef.current
    onDone({ word_count: READING_WORD_COUNT, elapsed_ms })
  }

  if (!started) {
    return (
      <div>
        <h2 className="text-xl md:text-2xl font-semibold mb-3">Calibrage de vitesse</h2>
        <p className="text-base opacity-80 leading-relaxed mb-8">
          Tu vas voir un paragraphe d’environ {READING_WORD_COUNT}&nbsp;mots. Lis-le à ton rythme normal,
          ni plus vite ni plus lentement. Quand tu as fini, clique sur le bouton.
        </p>
        <div className="flex flex-col-reverse sm:flex-row gap-3">
          <button
            onClick={onSkip}
            className="px-5 py-3.5 rounded-xl text-sm opacity-70"
            style={{ border: `1px solid ${theme.border}`, background: 'transparent', color: theme.fg }}
          >
            Passer
          </button>
          <button
            onClick={begin}
            className="flex-1 px-5 py-3.5 rounded-xl font-medium flex items-center justify-center gap-2"
            style={{ background: theme.accent, color: theme.bg }}
          >
            Démarrer la lecture <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <p
        className="text-lg leading-relaxed mb-8 select-text"
        style={{ color: theme.fg }}
      >
        {READING_PARAGRAPH}
      </p>
      <button
        onClick={finish}
        className="w-full px-5 py-3.5 rounded-xl font-medium flex items-center justify-center gap-2"
        style={{ background: theme.accent, color: theme.bg }}
      >
        J’ai fini <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  )
}

// ---------- Stage 5: result ----------------------------------------------

function ResultStage({
  result,
  error,
  onCommit,
  onRedo,
}: {
  result: AssessmentResultResp | null
  error: string | null
  onCommit: () => void
  onRedo: () => void
}) {
  const theme = THEMES.paper
  if (error || !result) {
    return (
      <div>
        <h2 className="text-xl font-semibold mb-2 text-red-700">Calibration impossible</h2>
        <p className="text-sm opacity-80 mb-4">{error ?? 'Réponse invalide.'}</p>
        <button
          onClick={onRedo}
          className="px-5 py-3.5 rounded-xl font-medium"
          style={{ background: theme.accent, color: theme.bg }}
        >
          Recommencer
        </button>
      </div>
    )
  }

  const profileLabel = PROFILE_LABELS[result.preset.profile]
  const dims = result.profile
  const weights = result.preset.profile_weights

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-1">
        Profil recommandé · {profileLabel.name}
      </h2>
      <p className="text-base opacity-80 leading-relaxed mb-5">
        {profileLabel.tagline}
      </p>

      <p className="text-sm opacity-70 leading-relaxed mb-7">
        <strong style={{ color: theme.accent }}>Pourquoi :</strong> {result.preset.rationale}
      </p>

      {/* Dimension bars */}
      <div className="space-y-3 mb-6">
        <DimensionBar
          label="Difficulté d'attention"
          value={dims.inattention}
          unit="/100"
          color={theme.accent}
        />
        <DimensionBar
          label="Tendance hyperactive / impulsive"
          value={dims.hyperactivity}
          unit="/100"
          color={theme.accent}
        />
        <DimensionBar
          label="Régularité des réflexes"
          value={dims.consistency}
          unit="/100"
          color={theme.accent}
        />
        <DimensionBar
          label="Vitesse de lecture mesurée"
          value={Math.round(dims.reading_speed_wpm)}
          unit=" wpm"
          color={theme.accent}
          scale={500}
        />
      </div>

      {/* Profile weights */}
      <div className="text-xs opacity-70 mb-7">
        <div className="opacity-60 mb-1.5">Affinité avec chaque profil :</div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {Object.entries(weights)
            .sort((a, b) => b[1] - a[1])
            .map(([k, v]) => (
              <div key={k} className="flex items-center justify-between tabular-nums">
                <span>{PROFILE_LABELS[k as keyof typeof PROFILE_LABELS].name}</span>
                <span>{Math.round(v * 100)}%</span>
              </div>
            ))}
        </div>
      </div>

      <p className="text-xs opacity-50 mb-8">
        Confiance d’estimation : {Math.round(dims.confidence * 100)} % ·
        {' '}
        {dims.confidence >= 0.95
          ? 'toutes les étapes complétées'
          : dims.confidence >= 0.5
          ? 'au moins une étape passée'
          : 'profil par défaut (aucune donnée)'}
      </p>

      <div className="flex flex-col-reverse sm:flex-row gap-3">
        <button
          onClick={onRedo}
          className="px-5 py-3.5 rounded-xl text-sm opacity-80"
          style={{ border: `1px solid ${theme.border}`, background: 'transparent', color: theme.fg }}
        >
          Refaire la calibration
        </button>
        <button
          onClick={onCommit}
          className="flex-1 px-5 py-3.5 rounded-xl font-medium flex items-center justify-center gap-2"
          style={{ background: theme.accent, color: theme.bg }}
        >
          Appliquer et lire <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function DimensionBar({
  label,
  value,
  unit,
  color,
  scale = 100,
}: {
  label: string
  value: number
  unit: string
  color: string
  scale?: number
}) {
  const theme = THEMES.paper
  const pct = Math.min(100, (value / scale) * 100)
  return (
    <div>
      <div className="flex items-center justify-between text-xs opacity-80 mb-1.5">
        <span>{label}</span>
        <span className="tabular-nums">
          {typeof value === 'number' ? Math.round(value) : value}
          {unit}
        </span>
      </div>
      <div className="h-[5px] rounded-full" style={{ background: theme.border }}>
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  )
}

// ---------- helpers -------------------------------------------------------

function useReducedMotion(): boolean {
  const getInitial = () => {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }
  const [v, setV] = useState<boolean>(getInitial)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const h = (e: MediaQueryListEvent) => setV(e.matches)
    mq.addEventListener('change', h)
    return () => mq.removeEventListener('change', h)
  }, [])
  return v
}

/**
 * Map backend snake_case onboarding settings keys to the camelCase keys
 * used by the frontend `Settings` type. Only the keys we know about are
 * relayed — unknown keys are silently dropped so a backend schema bump
 * never leaks unknown state into the store.
 */
function remapBackendSettings(
  backend: Record<string, string | number | boolean>,
): Partial<Settings> {
  const map: Record<string, keyof Settings> = {
    theme: 'theme',
    bionicEnabled: 'bionicEnabled',
    fixationRatio: 'fixationRatio',
    minWordLength: 'minWordLength',
    fontSize: 'fontSize',
    lineHeight: 'lineHeight',
    saccadeAdaptive: 'saccadeAdaptive',
    eyeAnchorEnabled: 'eyeAnchor',
    phraseChunkingEnabled: 'phraseChunking',
    posColoringEnabled: 'posColoring',
    guidedPulseEnabled: 'pulseCadence',
    rsvpEnabled: 'rsvpEnabled',
    rsvpWpm: 'rsvpWpm',
  }
  const out: Partial<Settings> = {}
  for (const [k, v] of Object.entries(backend)) {
    const key = map[k]
    if (!key) continue
    // We trust the backend's value types here — the API contract guarantees them.
    ;(out as Record<string, unknown>)[key] = v
  }
  return out
}



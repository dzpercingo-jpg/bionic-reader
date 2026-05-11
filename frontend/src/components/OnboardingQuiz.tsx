import { useMemo, useState } from 'react'
import { ChevronRight, BookOpenText } from 'lucide-react'
import type { ReadingProfile } from '../types'
import { THEMES } from '../types'
import { useApp } from '../store'
import { PROFILE_LABELS } from '../store'

/**
 * Onboarding quiz — 6 questions, 30 seconds.
 *
 * Each answer carries a vector that contributes to four profile scores
 * (apaise / equilibre / concentre / sprint). The highest-scoring profile
 * is then applied via `applyProfile()` from the store.
 *
 * Design constraints (council debate):
 * - max 6 questions (Barkley WM limit)
 * - no jargon ("combien de gras", not "fixation ratio")
 * - no neutral middle option (Pinker: forcing a stance reveals preference)
 * - one screen per question (Tufte: no scrolling, max signal)
 */

interface Choice {
  label: string
  vector: ProfileVector
}

interface ProfileVector {
  apaise: number
  equilibre: number
  concentre: number
  sprint: number
}

interface Question {
  q: string
  hint?: string
  choices: Choice[]
}

const QUESTIONS: Question[] = [
  {
    q: 'Quand tu lis longtemps, qu’est-ce qui te coûte le plus ?',
    hint: 'Tu as le droit d’une seule réponse — celle qui résonne le plus.',
    choices: [
      {
        label: 'Mes yeux fatiguent et le texte devient flou',
        vector: { apaise: 3, equilibre: 1, concentre: 0, sprint: 0 },
      },
      {
        label: 'Je décroche, je relis sans rien retenir',
        vector: { apaise: 1, equilibre: 1, concentre: 3, sprint: 0 },
      },
      {
        label: 'Je lis trop lentement par rapport à mon temps',
        vector: { apaise: 0, equilibre: 0, concentre: 1, sprint: 3 },
      },
      {
        label: 'Je m’ennuie, j’ai besoin de varier',
        vector: { apaise: 0, equilibre: 2, concentre: 1, sprint: 2 },
      },
    ],
  },
  {
    q: 'Tu préfères un fond de page…',
    choices: [
      {
        label: 'Doux, neutre, type papier vieilli',
        vector: { apaise: 3, equilibre: 2, concentre: 1, sprint: 0 },
      },
      {
        label: 'Gris froid, un peu technique',
        vector: { apaise: 1, equilibre: 1, concentre: 3, sprint: 1 },
      },
      {
        label: 'Coloré (lavande, menthe, pastel)',
        vector: { apaise: 2, equilibre: 1, concentre: 0, sprint: 0 },
      },
      {
        label: 'Blanc franc, ça me va',
        vector: { apaise: 0, equilibre: 1, concentre: 0, sprint: 2 },
      },
    ],
  },
  {
    q: 'À quel point as-tu besoin de gras pour suivre les lignes ?',
    hint: 'Le gras de la lecture bionique guide ton œil — mais trop, c’est fatigant.',
    choices: [
      {
        label: 'Très peu, presque invisible',
        vector: { apaise: 3, equilibre: 1, concentre: 0, sprint: 0 },
      },
      { label: 'Modéré', vector: { apaise: 1, equilibre: 3, concentre: 2, sprint: 1 } },
      { label: 'Marqué', vector: { apaise: 0, equilibre: 1, concentre: 3, sprint: 2 } },
      { label: 'Je n’ai pas d’avis', vector: { apaise: 1, equilibre: 2, concentre: 1, sprint: 1 } },
    ],
  },
  {
    q: 'En général, tes sessions de lecture durent…',
    choices: [
      {
        label: 'Plus de 30 minutes (j’aime le calme)',
        vector: { apaise: 3, equilibre: 2, concentre: 1, sprint: 0 },
      },
      {
        label: '10 à 30 minutes (mode normal)',
        vector: { apaise: 1, equilibre: 3, concentre: 2, sprint: 0 },
      },
      {
        label: 'Moins de 10 minutes (je scanne souvent)',
        vector: { apaise: 0, equilibre: 0, concentre: 1, sprint: 3 },
      },
      {
        label: 'Ça dépend, c’est très variable',
        vector: { apaise: 1, equilibre: 2, concentre: 2, sprint: 1 },
      },
    ],
  },
  {
    q: 'Préfères-tu lire avec les yeux ou écouter ?',
    choices: [
      {
        label: 'Yeux uniquement, l’audio me distrait',
        vector: { apaise: 2, equilibre: 2, concentre: 3, sprint: 1 },
      },
      {
        label: 'Yeux principalement, parfois écouter',
        vector: { apaise: 2, equilibre: 3, concentre: 1, sprint: 0 },
      },
      {
        label: 'Surtout écouter, le texte est un repère',
        vector: { apaise: 3, equilibre: 1, concentre: 0, sprint: 0 },
      },
      {
        label: 'Lire un mot à la fois, très vite (RSVP)',
        vector: { apaise: 0, equilibre: 0, concentre: 0, sprint: 4 },
      },
    ],
  },
  {
    q: 'Quel est ton objectif principal aujourd’hui ?',
    choices: [
      {
        label: 'Lire un texte de fond posément',
        vector: { apaise: 3, equilibre: 2, concentre: 1, sprint: 0 },
      },
      {
        label: 'Bien comprendre un texte dense',
        vector: { apaise: 0, equilibre: 1, concentre: 4, sprint: 0 },
      },
      {
        label: 'Scanner / aller à l’essentiel',
        vector: { apaise: 0, equilibre: 0, concentre: 0, sprint: 4 },
      },
      {
        label: 'Découvrir / juste tester l’app',
        vector: { apaise: 1, equilibre: 3, concentre: 1, sprint: 1 },
      },
    ],
  },
]

function scoreToProfile(answers: ProfileVector): Exclude<ReadingProfile, null> {
  const entries = Object.entries(answers) as [Exclude<ReadingProfile, null>, number][]
  entries.sort((a, b) => b[1] - a[1])
  return entries[0][0]
}

export default function OnboardingQuiz({ onDone }: { onDone: () => void }) {
  const { applyProfile, setOnboardingDone } = useApp()
  const [step, setStep] = useState(0)
  const [scores, setScores] = useState<ProfileVector>({
    apaise: 0,
    equilibre: 0,
    concentre: 0,
    sprint: 0,
  })
  const [done, setDone] = useState(false)
  const [chosenProfile, setChosenProfile] = useState<Exclude<ReadingProfile, null> | null>(null)

  const theme = THEMES.paper
  const current = QUESTIONS[step]
  const progress = useMemo(() => ((step + (done ? 1 : 0)) / QUESTIONS.length) * 100, [step, done])

  function answer(choice: Choice) {
    const newScores = {
      apaise: scores.apaise + choice.vector.apaise,
      equilibre: scores.equilibre + choice.vector.equilibre,
      concentre: scores.concentre + choice.vector.concentre,
      sprint: scores.sprint + choice.vector.sprint,
    }
    setScores(newScores)
    if (step + 1 < QUESTIONS.length) {
      setStep(step + 1)
    } else {
      const p = scoreToProfile(newScores)
      setChosenProfile(p)
      setDone(true)
    }
  }

  function commit() {
    if (!chosenProfile) return
    applyProfile(chosenProfile)
    setOnboardingDone(true)
    onDone()
  }

  return (
    <div
      className="h-screen w-full flex items-center justify-center px-4 font-ui"
      style={{ background: theme.bg, color: theme.fg }}
    >
      <div className="w-full max-w-2xl">
        <div className="flex items-center gap-2 mb-6">
          <BookOpenText className="w-5 h-5" style={{ color: theme.accent }} />
          <span className="text-sm font-medium">Mode guidé · onboarding</span>
          <span className="ml-auto text-xs opacity-60 tabular-nums">
            {done ? QUESTIONS.length : step + 1} / {QUESTIONS.length}
          </span>
        </div>

        <div
          className="h-[3px] rounded-full mb-12"
          style={{ background: theme.border, position: 'relative' }}
        >
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${progress}%`, background: theme.accent }}
          />
        </div>

        {!done ? (
          <>
            <h2 className="text-xl md:text-2xl font-semibold leading-snug mb-2">
              {current.q}
            </h2>
            {current.hint && (
              <p className="text-sm opacity-60 mb-7">{current.hint}</p>
            )}
            <div className="space-y-2.5">
              {current.choices.map((c) => (
                <button
                  key={c.label}
                  onClick={() => answer(c)}
                  className="w-full text-left px-5 py-3.5 rounded-xl transition-all hover:translate-x-1 focus:outline-none focus:ring-2"
                  style={{
                    background: '#f5f1e8',
                    border: `1px solid ${theme.border}`,
                    color: theme.fg,
                  }}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </>
        ) : (
          chosenProfile && (
            <div>
              <h2 className="text-xl md:text-2xl font-semibold mb-2">
                Profil recommandé · {PROFILE_LABELS[chosenProfile].name}
              </h2>
              <p className="text-sm opacity-80 mb-6 leading-relaxed">
                {PROFILE_LABELS[chosenProfile].tagline}
              </p>

              <div className="text-xs opacity-60 mb-8 grid grid-cols-2 gap-2">
                {(Object.entries(scores) as [Exclude<ReadingProfile, null>, number][])
                  .sort((a, b) => b[1] - a[1])
                  .map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between gap-2">
                      <span>{PROFILE_LABELS[k].name}</span>
                      <div
                        className="flex-1 h-[3px] rounded-full ml-2"
                        style={{ background: theme.border }}
                      >
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(v / Math.max(...Object.values(scores))) * 100}%`,
                            background:
                              k === chosenProfile ? theme.accent : theme.muted,
                          }}
                        />
                      </div>
                      <span className="tabular-nums w-6 text-right">{v}</span>
                    </div>
                  ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={commit}
                  className="px-5 py-3 rounded-xl font-medium flex items-center gap-2"
                  style={{ background: theme.accent, color: 'white' }}
                >
                  Commencer à lire <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setStep(0)
                    setScores({ apaise: 0, equilibre: 0, concentre: 0, sprint: 0 })
                    setDone(false)
                    setChosenProfile(null)
                  }}
                  className="px-5 py-3 rounded-xl text-sm opacity-70 hover:opacity-100"
                >
                  Refaire le quiz
                </button>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}

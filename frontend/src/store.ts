import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AppMode, Document, ReadingProfile, Settings } from './types'
import { defaultSettings } from './types'

interface AppState {
  // Top-level
  mode: AppMode
  onboardingDone: boolean
  profile: ReadingProfile

  // Document & UI state
  document: Document | null
  /**
   * The original uploaded `File` object (DOCX/PDF/PPTX/XLSX). Kept in memory
   * so we can ship its raw bytes back to the in-place exporter endpoint and
   * produce a fidelity-preserving transformed file. Cleared whenever the
   * user loads a different document. Not persisted to localStorage.
   */
  sourceFile: File | null
  settings: Settings
  busy: boolean
  error: string | null

  // Actions
  setMode: (m: AppMode) => void
  setOnboardingDone: (b: boolean) => void
  setProfile: (p: ReadingProfile) => void
  applyProfile: (p: ReadingProfile) => void
  setDocument: (d: Document | null, file?: File | null) => void
  setSettings: (patch: Partial<Settings>) => void
  resetSettings: () => void
  setBusy: (b: boolean) => void
  setError: (e: string | null) => void
}

/**
 * Concrete settings presets for each Reading Profile.
 *
 * These are the **outputs** of the onboarding quiz scoring algorithm.
 * Each preset is a coherent design — never a random pick of options —
 * tuned with the simulated friction score in mind (see ADHD_SIMULATOR.md).
 */
export const PRESETS: Record<Exclude<ReadingProfile, null>, Partial<Settings>> = {
  apaise: {
    theme: 'paper',
    bionicEnabled: true,
    fixationRatio: 0.35,
    minWordLength: 4,
    saccadeAdaptive: true,
    useColorInsteadOfBold: false,
    colorVowels: false,
    colorFirstLetter: false,
    eyeAnchor: true,
    phraseChunking: false,
    posColoring: false,
    breathingWord: true,
    focusModeEnabled: true,
    focusModeStrength: 0.8,
    fontSize: 19,
    lineHeight: 1.85,
    letterSpacing: 0.012,
    maxLineWidth: 62,
    paragraphSpacing: 1.2,
    rsvpEnabled: false,
    quietness: 2,
  },
  equilibre: {
    theme: 'paper',
    bionicEnabled: true,
    fixationRatio: 0.45,
    minWordLength: 4,
    saccadeAdaptive: true,
    useColorInsteadOfBold: false,
    colorVowels: false,
    colorFirstLetter: false,
    eyeAnchor: true,
    phraseChunking: false,
    posColoring: false,
    breathingWord: true,
    focusModeEnabled: true,
    focusModeStrength: 0.7,
    fontSize: 19,
    lineHeight: 1.75,
    letterSpacing: 0.01,
    maxLineWidth: 64,
    paragraphSpacing: 1.1,
    rsvpEnabled: false,
    quietness: 1,
  },
  concentre: {
    theme: 'fog',
    bionicEnabled: true,
    fixationRatio: 0.5,
    minWordLength: 3,
    saccadeAdaptive: true,
    useColorInsteadOfBold: false,
    colorVowels: false,
    colorFirstLetter: false,
    eyeAnchor: true,
    phraseChunking: true,
    phraseChunkSize: 4,
    posColoring: false,
    breathingWord: true,
    focusModeEnabled: true,
    focusModeStrength: 0.9,
    fontSize: 18,
    lineHeight: 1.65,
    letterSpacing: 0.008,
    maxLineWidth: 60,
    paragraphSpacing: 1.0,
    pulseCadence: true,
    pulseCadenceWpm: 240,
    rsvpEnabled: false,
    quietness: 0,
  },
  sprint: {
    theme: 'paper',
    bionicEnabled: true,
    fixationRatio: 0.5,
    minWordLength: 3,
    saccadeAdaptive: true,
    eyeAnchor: false,
    phraseChunking: false,
    posColoring: false,
    breathingWord: false,
    focusModeEnabled: false,
    rsvpEnabled: true,
    rsvpWpm: 350,
    rsvpChunkSize: 1,
    rsvpPauseOnPunct: true,
    quietness: 1,
  },
}

export const PROFILE_LABELS: Record<Exclude<ReadingProfile, null>, { name: string; tagline: string }> = {
  apaise: {
    name: 'Apaisé',
    tagline: 'Lecture immersive, longue, sans fatigue. Pour les sessions de fond.',
  },
  equilibre: {
    name: 'Équilibré',
    tagline: 'Polyvalent, le bon réflexe pour la plupart des contenus.',
  },
  concentre: {
    name: 'Concentré',
    tagline: 'Pour les textes denses où il faut tenir le fil.',
  },
  sprint: {
    name: 'Sprint',
    tagline: 'Mode RSVP : un mot à la fois pour scanner vite. Compréhension réduite.',
  },
}

export const useApp = create<AppState>()(
  persist(
    (set) => ({
      mode: 'welcome',
      onboardingDone: false,
      profile: null,

      document: null,
      sourceFile: null,
      settings: defaultSettings,
      busy: false,
      error: null,

      setMode: (mode) => set({ mode }),
      setOnboardingDone: (b) => set({ onboardingDone: b }),
      setProfile: (profile) => set({ profile }),
      applyProfile: (profile) => {
        if (!profile) {
          set({ profile: null, settings: defaultSettings })
          return
        }
        const preset = PRESETS[profile]
        set({
          profile,
          settings: { ...defaultSettings, ...preset },
        })
      },
      setDocument: (d, file = null) =>
        set({ document: d, sourceFile: file ?? null, error: null }),
      setSettings: (patch) => set((state) => ({ settings: { ...state.settings, ...patch } })),
      resetSettings: () => set({ settings: { ...defaultSettings } }),
      setBusy: (busy) => set({ busy }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'bionic-reader-state',
      version: 2,
      partialize: (state) => ({
        mode: state.mode,
        onboardingDone: state.onboardingDone,
        profile: state.profile,
        settings: state.settings,
      }),
      migrate: (persisted: unknown, version): unknown => {
        // v1 → v2 : new fields (eyeAnchor, mode, onboardingDone, profile)
        const p = (persisted as Record<string, unknown>) ?? {}
        if (version < 2) {
          return {
            ...p,
            mode: 'welcome',
            onboardingDone: false,
            profile: null,
            settings: { ...defaultSettings, ...((p.settings as Partial<Settings>) ?? {}) },
          }
        }
        return p
      },
    },
  ),
)

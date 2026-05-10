import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Document, Settings } from './types'
import { defaultSettings } from './types'

interface AppState {
  document: Document | null
  settings: Settings
  busy: boolean
  error: string | null
  setDocument: (d: Document | null) => void
  setSettings: (patch: Partial<Settings>) => void
  resetSettings: () => void
  setBusy: (b: boolean) => void
  setError: (e: string | null) => void
}

export const useApp = create<AppState>()(
  persist(
    (set) => ({
      document: null,
      settings: defaultSettings,
      busy: false,
      error: null,
      setDocument: (d) => set({ document: d, error: null }),
      setSettings: (patch) => set((state) => ({ settings: { ...state.settings, ...patch } })),
      resetSettings: () => set({ settings: defaultSettings }),
      setBusy: (busy) => set({ busy }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'bionic-reader-state',
      partialize: (state) => ({ settings: state.settings }),
    },
  ),
)

export type BlockType =
  | 'heading'
  | 'paragraph'
  | 'list_item'
  | 'blockquote'
  | 'code'
  | 'image_caption'
  | 'table_row'
  | 'spacer'

export interface Block {
  type: BlockType
  text: string
  level?: number | null
  ordered?: boolean | null
  language?: string | null
}

export interface Document {
  id: string
  filename: string
  format: string
  word_count: number
  char_count: number
  blocks: Block[]
  warnings: string[]
}

export type FontChoice =
  | 'lexend'
  | 'inter'
  | 'atkinson'
  | 'opendyslexic'
  | 'georgia'
  | 'system'
  | 'mono'

export type ThemeChoice = 'light' | 'sepia' | 'cream' | 'dark' | 'highContrast' | 'lowContrast'

export interface Settings {
  // Bionic core
  bionicEnabled: boolean
  fixationRatio: number  // 0.2..0.8
  saccadeAdaptive: boolean
  minWordLength: number
  skipShortWords: boolean
  useColorInsteadOfBold: boolean
  prefixColor: string
  colorVowels: boolean
  vowelColor: string
  colorFirstLetter: boolean
  firstLetterColor: string

  // Typography
  font: FontChoice
  fontSize: number          // px
  fontWeight: number        // 300..700
  letterSpacing: number     // em
  wordSpacing: number       // em
  lineHeight: number        // unitless
  maxLineWidth: number      // ch
  paragraphSpacing: number  // em
  justify: boolean
  hyphens: boolean

  // Theme & color
  theme: ThemeChoice
  customBg: string
  customFg: string
  overlayEnabled: boolean
  overlayColor: string
  overlayOpacity: number    // 0..1

  // Visual aids
  rulerEnabled: boolean
  focusModeEnabled: boolean   // dim non-focused paragraphs
  focusModeStrength: number   // 0..1
  chunkingEnabled: boolean
  chunkSize: number           // words per chunk
  paginate: boolean

  // Modes
  rsvpEnabled: boolean
  rsvpWpm: number             // 100..1000
  rsvpChunkSize: number       // words per flash
  rsvpPauseOnPunct: boolean

  // TTS
  ttsEnabled: boolean
  ttsRate: number             // 0.5..2.0
  ttsVoice: string | null
  ttsHighlight: boolean
}

export const defaultSettings: Settings = {
  bionicEnabled: true,
  fixationRatio: 0.5,
  saccadeAdaptive: true,
  minWordLength: 2,
  skipShortWords: true,
  useColorInsteadOfBold: false,
  prefixColor: '#0f172a',
  colorVowels: false,
  vowelColor: '#dc2626',
  colorFirstLetter: false,
  firstLetterColor: '#2563eb',

  font: 'lexend',
  fontSize: 19,
  fontWeight: 400,
  letterSpacing: 0,
  wordSpacing: 0,
  lineHeight: 1.7,
  maxLineWidth: 70,
  paragraphSpacing: 1,
  justify: false,
  hyphens: false,

  theme: 'cream',
  customBg: '#fbfaf6',
  customFg: '#1a1a1a',
  overlayEnabled: false,
  overlayColor: '#fde68a',
  overlayOpacity: 0.25,

  rulerEnabled: false,
  focusModeEnabled: false,
  focusModeStrength: 0.5,
  chunkingEnabled: false,
  chunkSize: 12,
  paginate: false,

  rsvpEnabled: false,
  rsvpWpm: 350,
  rsvpChunkSize: 1,
  rsvpPauseOnPunct: true,

  ttsEnabled: false,
  ttsRate: 1.0,
  ttsVoice: null,
  ttsHighlight: true,
}

export const FONT_FAMILY: Record<FontChoice, string> = {
  lexend: '"Lexend", "Inter", system-ui, sans-serif',
  inter: '"Inter", system-ui, sans-serif',
  atkinson: '"Atkinson Hyperlegible", "Inter", system-ui, sans-serif',
  opendyslexic: '"OpenDyslexic", "Lexend", sans-serif',
  georgia: 'Georgia, "Times New Roman", serif',
  system: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  mono: '"JetBrains Mono", "Fira Code", ui-monospace, monospace',
}

export interface Theme {
  bg: string
  fg: string
  muted: string
  accent: string
  border: string
}

export const THEMES: Record<ThemeChoice, Theme> = {
  light:        { bg: '#ffffff', fg: '#111827', muted: '#6b7280', accent: '#2563eb', border: '#e5e7eb' },
  cream:        { bg: '#fbfaf6', fg: '#1a1a1a', muted: '#5b5b55', accent: '#7c5e2a', border: '#e8e3d4' },
  sepia:        { bg: '#f4ecd8', fg: '#3a2e1f', muted: '#6e5e44', accent: '#a05a1a', border: '#d8c8a0' },
  dark:         { bg: '#13141a', fg: '#e8e8e8', muted: '#a0a0a0', accent: '#7dd3fc', border: '#262934' },
  highContrast: { bg: '#000000', fg: '#ffff00', muted: '#aaaa00', accent: '#00ffff', border: '#444400' },
  lowContrast:  { bg: '#2b2c33', fg: '#bcbcc6', muted: '#7c7d8a', accent: '#a3b8d8', border: '#3b3c45' },
}

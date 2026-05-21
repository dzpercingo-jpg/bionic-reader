import type { BionicSettings } from './apiTypes'
import type { Document, Settings } from './types'

const API_BASE: string =
  (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE ??
  ''

export async function parseFile(file: File): Promise<Document> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${API_BASE}/api/parse`, { method: 'POST', body: fd })
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail ?? `Parse failed (${res.status})`)
  }
  return (await res.json()) as Document
}

export async function exportDocument(
  document: Document,
  settings: Settings,
  format: 'html' | 'docx' | 'txt',
  title?: string,
): Promise<Blob> {
  const payload = {
    document,
    settings: settingsToBackend(settings),
    format,
    title: title ?? null,
  }
  const res = await fetch(`${API_BASE}/api/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail ?? `Export failed (${res.status})`)
  }
  return await res.blob()
}

export function settingsToBackend(s: Settings): BionicSettings {
  return {
    enabled: s.bionicEnabled,
    fixation_ratio: s.fixationRatio,
    min_word_length: s.minWordLength,
    skip_short_words: s.skipShortWords,
    use_color_instead_of_bold: s.useColorInsteadOfBold,
    prefix_color: s.prefixColor,
    color_vowels: s.colorVowels,
    vowel_color: s.vowelColor,
    saccade_adaptive: s.saccadeAdaptive,
    eye_anchor: s.eyeAnchor,
    eye_anchor_color: s.eyeAnchorColor,
    phrase_chunking: s.phraseChunking,
    phrase_chunk_size: s.phraseChunkSize,
    pos_coloring: s.posColoring,
    pos_color: s.posColor,
  }
}

/**
 * Apply bionic transformation directly on the user's original file bytes.
 *
 * Preserves images, tables, charts, embedded objects, formulas (XLSX),
 * animations (PPTX), fonts, colors, headers/footers, and the document's
 * overall structure. The output file's format always matches the source
 * format.
 */
export async function exportDocumentInplace(
  file: File,
  settings: Settings,
): Promise<{ blob: Blob; filename: string | null }> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('settings', JSON.stringify(settingsToBackend(settings)))
  const res = await fetch(`${API_BASE}/api/export-inplace`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail ?? `In-place export failed (${res.status})`)
  }
  // Backend may convert the source extension (e.g. legacy .doc → .docx) and
  // reports the correct output filename in Content-Disposition. Honor it so
  // the download has the right extension and opens correctly in Word/etc.
  const filename = parseContentDispositionFilename(res.headers.get('Content-Disposition'))
  return { blob: await res.blob(), filename }
}

function parseContentDispositionFilename(header: string | null): string | null {
  if (!header) return null
  // RFC 6266: filename*=UTF-8''... takes precedence over filename="..."
  const star = /filename\*\s*=\s*([^;]+)/i.exec(header)
  if (star) {
    const raw = star[1].trim()
    const m = /^[^']*'[^']*'(.+)$/.exec(raw)
    if (m) {
      try {
        return decodeURIComponent(m[1])
      } catch {
        return m[1]
      }
    }
  }
  const plain = /filename\s*=\s*"?([^";]+)"?/i.exec(header)
  return plain ? plain[1].trim() : null
}

export const INPLACE_FORMATS = new Set(['pdf', 'doc', 'docx', 'pptx', 'xlsx'])

// ----------------------------------------------------------------------------
// Onboarding scoring API
// ----------------------------------------------------------------------------

export interface AsrsAnswerPayload {
  qid: 'q1' | 'q2' | 'q3' | 'q4' | 'q5' | 'q6'
  score: 0 | 1 | 2 | 3 | 4
}

export interface PvtTrialPayload {
  rt_ms: number
  false_start: boolean
  lapse: boolean
}

export interface ReadingTrialPayload {
  word_count: number
  elapsed_ms: number
  comprehension_correct?: number
  comprehension_total?: number
}

export interface AssessmentPayload {
  asrs: AsrsAnswerPayload[]
  pvt: PvtTrialPayload[]
  reading: ReadingTrialPayload | null
  locale?: string | null
}

export interface ProfileVectorResp {
  inattention: number
  hyperactivity: number
  reading_speed_wpm: number
  consistency: number
  confidence: number
}

export interface RecommendedPresetResp {
  profile: 'apaise' | 'equilibre' | 'concentre' | 'sprint'
  rationale: string
  settings: Record<string, string | number | boolean>
  profile_weights: Record<string, number>
}

export interface AssessmentResultResp {
  profile: ProfileVectorResp
  preset: RecommendedPresetResp
}

export async function scoreOnboarding(
  payload: AssessmentPayload,
): Promise<AssessmentResultResp> {
  const res = await fetch(`${API_BASE}/api/onboarding/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail ?? `Onboarding score failed (${res.status})`)
  }
  return (await res.json()) as AssessmentResultResp
}

export function getExtension(filename: string): string {
  const i = filename.lastIndexOf('.')
  return i === -1 ? '' : filename.slice(i + 1).toLowerCase()
}

async function safeDetail(res: Response): Promise<string | null> {
  try {
    const j = await res.json()
    return typeof j?.detail === 'string' ? j.detail : null
  } catch {
    return null
  }
}

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

async function safeDetail(res: Response): Promise<string | null> {
  try {
    const j = await res.json()
    return typeof j?.detail === 'string' ? j.detail : null
  } catch {
    return null
  }
}

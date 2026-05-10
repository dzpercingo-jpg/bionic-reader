/**
 * Bionic transformation engine — mirrors backend/app/transformer.py exactly.
 *
 * Pure functions, no React. Used both for live preview and for offline export.
 */
import type { Settings } from '../types'

const WORD_RE = /(\p{L}+)/gu
const VOWELS = new Set('aeiouyàâäéèêëîïôöùûüÿœæ'.split(''))

export function prefixLength(word: string, s: Settings): number {
  const n = word.length
  if (n < s.minWordLength) return 0
  if (n === 1) return s.skipShortWords ? 0 : 1

  let ratio: number
  if (s.saccadeAdaptive) {
    let adaptive: number
    if (n <= 3) adaptive = 0.5
    else if (n <= 5) adaptive = 0.5
    else if (n <= 8) adaptive = 0.45
    else if (n <= 12) adaptive = 0.4
    else adaptive = 0.35
    ratio = (adaptive + s.fixationRatio) / 2
  } else {
    ratio = s.fixationRatio
  }
  const prefix = Math.max(1, Math.round(n * ratio))
  return n > 1 ? Math.min(prefix, n - 1) : prefix
}

function escapeHtml(s: string): string {
  return s
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

function colorVowelsHtml(text: string, s: Settings): string {
  if (!s.colorVowels) return escapeHtml(text)
  let out = ''
  for (const ch of text) {
    if (VOWELS.has(ch.toLowerCase())) {
      out += `<span style="color:${s.vowelColor}">${escapeHtml(ch)}</span>`
    } else {
      out += escapeHtml(ch)
    }
  }
  return out
}

export function transformWordHtml(word: string, s: Settings): string {
  const len = prefixLength(word, s)
  if (len === 0) return colorVowelsHtml(word, s)

  let prefix = word.slice(0, len)
  const suffix = word.slice(len)

  let firstLetterHtml = ''
  if (s.colorFirstLetter && prefix.length > 0) {
    firstLetterHtml = `<span style="color:${s.firstLetterColor}">${escapeHtml(prefix[0])}</span>`
    prefix = prefix.slice(1)
  }

  const styleParts: string[] = []
  if (s.useColorInsteadOfBold) styleParts.push(`color:${s.prefixColor}`)
  styleParts.push('font-weight:700')
  const style = styleParts.join(';')

  const prefixRendered = colorVowelsHtml(prefix, s)
  const suffixRendered = colorVowelsHtml(suffix, s)
  return `<b class="br-prefix" style="${style}">${firstLetterHtml}${prefixRendered}</b>${suffixRendered}`
}

export function transformTextHtml(text: string, s: Settings): string {
  if (!s.bionicEnabled) return escapeHtml(text)
  let out = ''
  let lastEnd = 0
  for (const m of text.matchAll(WORD_RE)) {
    const start = m.index ?? 0
    const end = start + m[0].length
    if (start > lastEnd) out += escapeHtml(text.slice(lastEnd, start))
    out += transformWordHtml(m[0], s)
    lastEnd = end
  }
  if (lastEnd < text.length) out += escapeHtml(text.slice(lastEnd))
  return out
}

/** Insert visual chunk separators every `chunkSize` words. */
export function chunkifyHtml(html: string, chunkSize: number): string {
  if (chunkSize <= 0) return html
  const tokens = html.split(/(<[^>]+>|\s+)/g)
  let wordCount = 0
  let out = ''
  for (const tok of tokens) {
    if (!tok) continue
    if (tok.startsWith('<')) {
      out += tok
      continue
    }
    if (/^\s+$/.test(tok)) {
      out += tok
      continue
    }
    out += tok
    wordCount += tok.split(/\s+/).filter(Boolean).length
    if (wordCount >= chunkSize) {
      out += '<span style="display:inline-block;width:0.9em"></span>'
      wordCount = 0
    }
  }
  return out
}

export function flatWords(text: string): string[] {
  return text.split(/\s+/).filter(Boolean)
}

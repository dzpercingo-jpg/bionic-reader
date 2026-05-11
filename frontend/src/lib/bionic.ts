/**
 * Bionic transformation engine — mirrors backend/app/transformer.py exactly.
 *
 * Pure functions, no React. Used both for live preview and for offline export.
 *
 * v2 extends v1 with eye-anchor dots (Dehaene OVP), phrase chunking, and
 * POS coloring for logical connectors.
 */
import type { Settings } from '../types'

const WORD_RE = /(\p{L}+)/gu
const VOWELS = new Set('aeiouyàâäéèêëîïôöùûüÿœæ'.split(''))

/**
 * French logical connectors that, when subtly colored, help readers
 * see the *structure* of the argument at a glance.
 */
const CONNECTORS = new Set([
  'mais', 'donc', 'car', 'or', 'ni', 'puisque', 'parce', 'pourtant',
  'cependant', 'néanmoins', 'toutefois', 'ainsi', 'alors', 'ensuite',
  'enfin', 'premièrement', 'deuxièmement', 'finalement', 'autrement',
  'sinon', 'malgré', 'bien', 'tandis', 'tant', 'lorsque', 'quand',
  'comme', 'si', 'puis', 'aussi', 'effet', 'fait', 'résumé',
  'conclusion', 'exemple', 'instance', 'because', 'however', 'therefore',
  'thus', 'hence', 'moreover', 'furthermore', 'nevertheless', 'although',
  'whereas', 'while',
])

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

/**
 * Optimal Viewing Position — index (0-based) of the letter where the
 * fovea lands most efficiently. Based on O'Regan 1987 / Brysbaert 1996.
 *
 *   length 1-2 → 0
 *   length 3-4 → 1
 *   length 5-6 → 2
 *   length 7-9 → 3
 *   length 10+ → ~length/3
 */
export function ovpIndex(wordLen: number): number {
  if (wordLen <= 2) return 0
  if (wordLen <= 4) return 1
  if (wordLen <= 6) return 2
  if (wordLen <= 9) return 3
  return Math.round(wordLen / 3)
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

/** Wrap a word in a span that paints the OVP letter with a tiny gray dot under it. */
function wrapWithEyeAnchor(html: string, word: string, s: Settings): string {
  if (!s.eyeAnchor || word.length < 3) return html
  // We don't try to inject inside the prefix/suffix markup — instead we tag
  // the whole word with a CSS gradient that places a 2px dot under the OVP letter.
  // This is purely visual; the underlying text is untouched.
  const ovp = ovpIndex(word.length)
  const pct = ((ovp + 0.5) / word.length) * 100
  // The dot is a radial gradient anchored to the OVP column.
  const bgStyle = `background-image:radial-gradient(circle at ${pct}% 105%, ${s.eyeAnchorColor} 1px, transparent 2.5px);background-repeat:no-repeat;background-size:100% 4px;background-position:bottom`
  return `<span class="br-anchored" style="${bgStyle}">${html}</span>`
}

function maybeWrapConnector(word: string, html: string, s: Settings): string {
  if (!s.posColoring) return html
  if (CONNECTORS.has(word.toLowerCase())) {
    return `<span class="br-connector" style="color:${s.posColor};font-weight:500">${html}</span>`
  }
  return html
}

export function transformWordHtml(word: string, s: Settings): string {
  const len = prefixLength(word, s)
  let inner: string

  if (len === 0) {
    inner = colorVowelsHtml(word, s)
  } else {
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
    inner = `<b class="br-prefix" style="${style}">${firstLetterHtml}${prefixRendered}</b>${suffixRendered}`
  }

  inner = wrapWithEyeAnchor(inner, word, s)
  inner = maybeWrapConnector(word, inner, s)
  return inner
}

function renderWord(word: string, s: Settings): string {
  if (s.bionicEnabled) return transformWordHtml(word, s)
  let inner = escapeHtml(word)
  inner = wrapWithEyeAnchor(inner, word, s)
  inner = maybeWrapConnector(word, inner, s)
  return inner
}

export function transformTextHtml(text: string, s: Settings): string {
  if (!s.bionicEnabled && !s.eyeAnchor && !s.posColoring && !s.phraseChunking) {
    return escapeHtml(text)
  }

  if (s.phraseChunking && s.phraseChunkSize > 0) {
    // Chunk at SOURCE level (before generating HTML), so we never split
    // bionic <b> tags across phrase boundaries.
    type Tok = { kind: 'word' | 'sep'; value: string }
    const chunks: Tok[][] = []
    let cur: Tok[] = []
    let wordsInCur = 0
    let lastEnd = 0
    for (const m of text.matchAll(WORD_RE)) {
      const start = m.index ?? 0
      const end = start + m[0].length
      if (start > lastEnd) cur.push({ kind: 'sep', value: text.slice(lastEnd, start) })
      cur.push({ kind: 'word', value: m[0] })
      wordsInCur++
      lastEnd = end
      if (wordsInCur >= s.phraseChunkSize) {
        chunks.push(cur)
        cur = []
        wordsInCur = 0
      }
    }
    if (lastEnd < text.length) cur.push({ kind: 'sep', value: text.slice(lastEnd) })
    if (cur.length) chunks.push(cur)

    return chunks
      .map((chunk) => {
        const buf = chunk
          .map((t) => (t.kind === 'word' ? renderWord(t.value, s) : escapeHtml(t.value)))
          .join('')
        return `<span class="br-phrase">${buf}</span>`
      })
      .join('<span class="br-phrase-gap"> </span>')
  }

  let out = ''
  let lastEnd = 0
  for (const m of text.matchAll(WORD_RE)) {
    const start = m.index ?? 0
    const end = start + m[0].length
    if (start > lastEnd) out += escapeHtml(text.slice(lastEnd, start))
    out += renderWord(m[0], s)
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

/**
 * Phrase chunking — insert a thin gap every N words to expose phrase groups.
 * Different from `chunkifyHtml` (which uses larger inline spacers): this one
 * adds a sub-em letter-spacing reset for visual rhythm.
 */
export function phraseChunkHtml(html: string, chunkSize: number): string {
  if (chunkSize <= 0) return html
  // Split on whitespace BETWEEN tokens but preserve word groups
  const parts: string[] = []
  let buffer: string[] = []
  let wordsInBuffer = 0
  const tokens = html.split(/(\s+)/g)
  for (const t of tokens) {
    if (/^\s+$/.test(t)) {
      buffer.push(t)
      continue
    }
    buffer.push(t)
    // Count actual words (strip HTML tags inside)
    const plain = t.replace(/<[^>]+>/g, '').trim()
    if (plain) wordsInBuffer += 1
    if (wordsInBuffer >= chunkSize) {
      parts.push(`<span class="br-phrase">${buffer.join('')}</span>`)
      buffer = []
      wordsInBuffer = 0
    }
  }
  if (buffer.length > 0) {
    parts.push(`<span class="br-phrase">${buffer.join('')}</span>`)
  }
  return parts.join('<span class="br-phrase-gap"> </span>')
}

export function flatWords(text: string): string[] {
  return text.split(/\s+/).filter(Boolean)
}

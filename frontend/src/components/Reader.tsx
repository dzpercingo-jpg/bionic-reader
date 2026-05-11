import { useEffect, useMemo, useRef, useState } from 'react'
import { useApp } from '../store'
import { FONT_FAMILY, THEMES } from '../types'
import type { Block, Settings } from '../types'
import { chunkifyHtml, transformTextHtml } from '../lib/bionic'

function blockHtml(block: Block, settings: Settings): string {
  // transformTextHtml now handles phrase chunking internally (at source level)
  // so HTML nesting is never broken across phrase boundaries.
  let html = transformTextHtml(block.text, settings)
  if (settings.chunkingEnabled) {
    html = chunkifyHtml(html, settings.chunkSize)
  }
  return html
}

export default function Reader({ ttsActiveWord }: { ttsActiveWord: number | null }) {
  const { document, settings } = useApp()
  const containerRef = useRef<HTMLDivElement>(null)
  const [rulerY, setRulerY] = useState<number | null>(null)
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)
  const [pulseY, setPulseY] = useState<number>(0)

  const theme = THEMES[settings.theme]
  // Background uses overlayColor as a *tint* of the theme bg when overlay enabled
  // (NOT a floating layer on top — that's the bug we fix).
  const bg = settings.overlayEnabled
    ? mixColors(theme.bg, settings.overlayColor, settings.overlayOpacity)
    : theme.bg
  const fg = theme.fg

  const flatWordCount = useMemo(() => {
    if (!document) return 0
    return document.blocks.reduce(
      (sum, b) => sum + b.text.split(/\s+/).filter(Boolean).length,
      0,
    )
  }, [document])

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      if (settings.rulerEnabled) setRulerY(e.clientY)
    }
    window.addEventListener('mousemove', handleMove)
    return () => window.removeEventListener('mousemove', handleMove)
  }, [settings.rulerEnabled])

  // Pulse cadence : a slow horizontal cursor that descends through the text.
  // wpm → pixels-per-second mapping assumes ~1 line ≈ 35 px, ~10 words per line.
  useEffect(() => {
    if (!settings.pulseCadence) return
    const pixelsPerSecond = (settings.pulseCadenceWpm / 10) * 35
    let raf = 0
    let lastT = performance.now()
    const tick = (t: number) => {
      const dt = (t - lastT) / 1000
      lastT = t
      setPulseY((y) => {
        const next = y + dt * pixelsPerSecond
        const container = containerRef.current
        if (container && next > container.clientHeight) return 0
        return next
      })
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [settings.pulseCadence, settings.pulseCadenceWpm])

  if (!document) return null

  const readerStyle: React.CSSProperties = {
    fontFamily: FONT_FAMILY[settings.font],
    fontSize: `${settings.fontSize}px`,
    fontWeight: settings.fontWeight,
    lineHeight: settings.lineHeight,
    letterSpacing: `${settings.letterSpacing}em`,
    wordSpacing: `${settings.wordSpacing}em`,
    maxWidth: `${settings.maxLineWidth}ch`,
    color: fg,
    textAlign: settings.justify ? 'justify' : 'left',
    hyphens: settings.hyphens ? 'auto' : 'manual',
    margin: '0 auto',
    padding: '2.5rem 1.5rem 6rem',
  }

  const containerStyle: React.CSSProperties = {
    background: bg,
    color: fg,
    minHeight: '100%',
    position: 'relative',
  }

  return (
    <div ref={containerRef} style={containerStyle} className="h-full overflow-y-auto br-scroll relative">
      {settings.rulerEnabled && rulerY !== null && (
        <div className="br-ruler" style={{ top: rulerY - 14 }} />
      )}
      {settings.pulseCadence && (
        <div
          className="br-pulse-cadence"
          style={{ top: pulseY, borderColor: theme.muted }}
        />
      )}

      <article
        style={readerStyle}
        className={settings.focusModeEnabled ? 'br-focus-dim' : ''}
      >
        <header className="mb-6 pb-3" style={{ borderBottom: `1px solid ${theme.border}` }}>
          <h1 style={{ fontSize: '1.6em', fontWeight: 700, margin: 0 }}>{document.filename}</h1>
          <p className="text-sm opacity-60 mt-1">
            {document.format.toUpperCase()} · {flatWordCount.toLocaleString('fr')} mots ·
            {' '}~{Math.ceil(flatWordCount / 220)} min de lecture
          </p>
          {document.warnings.length > 0 && (
            <ul className="mt-2 text-xs opacity-60 list-disc pl-5">
              {document.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          )}
        </header>

        {document.blocks.map((block, i) =>
          renderBlock(block, i, settings, ttsActiveWord, focusedIndex, setFocusedIndex),
        )}
      </article>
    </div>
  )
}

function renderBlock(
  block: Block,
  index: number,
  settings: Settings,
  ttsActiveWord: number | null,
  focusedIndex: number | null,
  setFocusedIndex: (i: number | null) => void,
): React.ReactElement | null {
  const html = blockHtml(block, settings)

  const dim =
    settings.focusModeEnabled && focusedIndex !== null && focusedIndex !== index
      ? 1 - settings.focusModeStrength
      : 1

  const baseProps = {
    onMouseEnter: () => settings.focusModeEnabled && setFocusedIndex(index),
    onFocus: () => settings.focusModeEnabled && setFocusedIndex(index),
    style: {
      opacity: dim,
      marginBottom: `${settings.paragraphSpacing}em`,
      transition: 'opacity 0.3s ease',
    } as React.CSSProperties,
    'data-block-index': index,
  }

  if (block.type === 'heading') {
    const level = Math.max(1, Math.min(block.level ?? 2, 6))
    const tag = `h${level}` as keyof React.JSX.IntrinsicElements
    return (
      <div key={index}>
        {renderHeading(tag, html, baseProps, level)}
      </div>
    )
  }
  if (block.type === 'list_item') {
    return (
      <ul key={index} style={{ paddingLeft: '1.5em', listStyleType: block.ordered ? 'decimal' : 'disc' }}>
        <li {...baseProps} dangerouslySetInnerHTML={{ __html: html }} />
      </ul>
    )
  }
  if (block.type === 'blockquote') {
    return (
      <blockquote
        key={index}
        {...baseProps}
        style={{
          ...baseProps.style,
          borderLeft: '4px solid currentColor',
          opacity: dim * 0.85,
          paddingLeft: '1em',
          fontStyle: 'italic',
        }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    )
  }
  if (block.type === 'code') {
    return (
      <pre
        key={index}
        {...baseProps}
        style={{
          ...baseProps.style,
          background: 'rgba(0,0,0,0.06)',
          padding: '1em',
          borderRadius: 6,
          overflow: 'auto',
          fontFamily: 'JetBrains Mono, ui-monospace, monospace',
          fontSize: '0.9em',
        }}
      >
        <code>{block.text}</code>
      </pre>
    )
  }
  if (block.type === 'spacer') {
    return <div key={index} style={{ height: '1em' }} />
  }
  return (
    <p
      key={index}
      {...baseProps}
      data-tts-block={index}
      data-tts-active={ttsActiveWord !== null ? 'true' : undefined}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

function renderHeading(
  tag: keyof React.JSX.IntrinsicElements,
  html: string,
  baseProps: Record<string, unknown>,
  level: number,
): React.ReactElement {
  const sizes = [0, 2.0, 1.6, 1.35, 1.15, 1.05, 1.0]
  const Tag = tag as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  const style = (baseProps as { style: React.CSSProperties }).style
  return (
    <Tag
      {...(baseProps as Record<string, unknown>)}
      style={{
        ...style,
        fontSize: `${sizes[level]}em`,
        fontWeight: 700,
        lineHeight: 1.2,
        marginTop: '1.5em',
      }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

/** Blend two hex colors (#rrggbb) with the given opacity for the overlay color. */
function mixColors(base: string, overlay: string, opacity: number): string {
  const b = hexToRgb(base)
  const o = hexToRgb(overlay)
  if (!b || !o) return base
  const r = Math.round(b.r * (1 - opacity) + o.r * opacity)
  const g = Math.round(b.g * (1 - opacity) + o.g * opacity)
  const bl = Math.round(b.b * (1 - opacity) + o.b * opacity)
  return `rgb(${r}, ${g}, ${bl})`
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const m = /^#?([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})$/i.exec(hex)
  if (!m) return null
  return {
    r: parseInt(m[1], 16),
    g: parseInt(m[2], 16),
    b: parseInt(m[3], 16),
  }
}

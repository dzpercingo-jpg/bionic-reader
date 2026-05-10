import { useEffect, useMemo, useRef, useState } from 'react'
import { useApp } from '../store'
import { FONT_FAMILY, THEMES } from '../types'
import type { Block, Settings } from '../types'
import { chunkifyHtml, transformTextHtml } from '../lib/bionic'

function blockHtml(block: Block, settings: Settings): string {
  const html = transformTextHtml(block.text, settings)
  return settings.chunkingEnabled ? chunkifyHtml(html, settings.chunkSize) : html
}

export default function Reader({ ttsActiveWord }: { ttsActiveWord: number | null }) {
  const { document, settings } = useApp()
  const containerRef = useRef<HTMLDivElement>(null)
  const [rulerY, setRulerY] = useState<number | null>(null)
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)

  const theme = THEMES[settings.theme]
  const bg = settings.theme === 'cream' ? settings.customBg : theme.bg
  const fg = settings.theme === 'cream' ? settings.customFg : theme.fg

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
    <div ref={containerRef} style={containerStyle} className="flex-1 overflow-y-auto br-scroll">
      {settings.overlayEnabled && (
        <div
          className="br-overlay"
          style={{ background: settings.overlayColor, opacity: settings.overlayOpacity }}
        />
      )}
      {settings.rulerEnabled && rulerY !== null && (
        <div className="br-ruler" style={{ top: rulerY - 14 }} />
      )}

      <article style={readerStyle} className={settings.focusModeEnabled ? 'br-focus-dim' : ''}>
        <header className="mb-6 pb-3 border-b border-stone-200/30">
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
          opacity: 0.75,
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

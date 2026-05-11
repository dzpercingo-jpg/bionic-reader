import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileUp, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import { useApp } from '../store'
import { parseFile } from '../api'

const ACCEPTED_EXT = [
  'pdf', 'docx', 'doc', 'pptx', 'xlsx', 'txt', 'md', 'markdown',
  'html', 'htm', 'epub', 'rtf',
]

export default function Uploader() {
  const { setDocument, setBusy, setError, busy } = useApp()

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0]
      if (!file) return
      setBusy(true)
      setError(null)
      try {
        const doc = await parseFile(file)
        // Keep the original File around so we can call /api/export-inplace
        // later and preserve images, tables, formulas, etc.
        setDocument(doc, file)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur de lecture du fichier')
      } finally {
        setBusy(false)
      }
    },
    [setDocument, setBusy, setError],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/epub+zip': ['.epub'],
      'application/rtf': ['.rtf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md', '.markdown'],
      'text/html': ['.html', '.htm'],
    },
  })

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-2xl p-10 cursor-pointer transition-colors text-center',
          isDragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-stone-300 hover:border-indigo-400 hover:bg-stone-50',
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          {busy ? (
            <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
          ) : (
            <FileUp className="w-12 h-12 text-stone-400" />
          )}
          <div className="text-lg font-medium text-stone-700">
            {busy
              ? 'Analyse du fichier…'
              : isDragActive
                ? 'Lâche le fichier ici'
                : 'Glisse-dépose un fichier ou clique pour parcourir'}
          </div>
          <div className="text-sm text-stone-500">
            Formats : {ACCEPTED_EXT.map((e) => e.toUpperCase()).join(' · ')} · max 50 MB
          </div>
          <div className="text-xs text-stone-400 max-w-md">
            Le fichier original n&apos;est jamais modifié. Une copie transformée est générée à la
            demande.
          </div>
        </div>
      </div>
    </div>
  )
}

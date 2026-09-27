import React, { useState, useRef } from 'react'
import { Upload, FileText, CheckCircle } from 'lucide-react'
import { ingestDocument } from '../api/ingestion'
import { Button } from '../components/common/Button'
import { ErrorPanel } from '../components/common/ErrorPanel'
import type { IngestResponse } from '../api/ingestion'

interface IngestionError {
  message: string
  code?: string
  requestId?: string
}

export const IngestionPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<IngestionError | null>(null)
  const [result, setResult] = useState<IngestResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
      setError(null)
      setResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    try {
      const res = await ingestDocument(file)
      setResult(res)
      setFile(null) // clear file after success
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err: any) {
      setError({
        message: err.message || 'Failed to upload document',
        code: err.code,
        requestId: err.requestId,
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
          Document Ingestion
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
          Upload text or markdown documents to the vector store. The documents will be chunked, embedded, and indexed for retrieval.
        </p>
      </div>

      <div
        style={{
          border: '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--bg-surface)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div style={{ 
          width: '48px', 
          height: '48px', 
          borderRadius: '50%', 
          backgroundColor: 'var(--bg-raised)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 'var(--space-4)',
          color: 'var(--text-secondary)'
        }}>
          <Upload size={24} />
        </div>
        
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          accept=".txt,.md,.markdown"
        />
        
        {file ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
            <FileText size={16} color="var(--text-secondary)" />
            <span style={{ color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}>{file.name}</span>
            <span style={{ color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)' }}>
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-4)' }}>
            Select a .txt, .md, or .markdown file to upload
          </p>
        )}

        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Button 
            variant="secondary" 
            onClick={() => fileInputRef.current?.click()}
          >
            {file ? 'Change File' : 'Select File'}
          </Button>
          
          <Button 
            variant="primary" 
            onClick={handleUpload}
            disabled={!file || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload & Index'}
          </Button>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <ErrorPanel
            title="Ingestion Failed"
            message={error.message}
            code={error.code}
            requestId={error.requestId}
          />
        </div>
      )}

      {result && (
        <div style={{ 
          padding: 'var(--space-4)', 
          backgroundColor: 'rgba(52, 211, 153, 0.05)', 
          border: '1px solid rgba(52, 211, 153, 0.2)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 'var(--space-3)'
        }}>
          <CheckCircle size={18} color="rgb(52, 211, 153)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h3 style={{ color: 'var(--text-primary)', fontSize: 'var(--text-sm)', fontWeight: 500, marginBottom: 'var(--space-1)' }}>
              Document Successfully Indexed
            </h3>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-xs)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div><span style={{ color: 'var(--text-tertiary)' }}>ID:</span> <code style={{ fontFamily: 'var(--font-mono)' }}>{result.document_id}</code></div>
              <div><span style={{ color: 'var(--text-tertiary)' }}>Chunks:</span> {result.chunk_count}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

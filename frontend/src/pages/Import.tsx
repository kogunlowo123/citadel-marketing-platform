import { useState, useRef } from 'react';
import { Upload, CheckCircle, XCircle } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { useImportCSV, useImports } from '../api/hooks';

interface ImportJob {
  id: string; original_filename: string; status: string; total_rows: number;
  imported_count: number; skipped_count: number; duplicate_count: number; error_count: number; created_at: string;
}

export default function Import() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [tags, setTags] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const importMutation = useImportCSV();
  const { data: imports } = useImports() as { data: ImportJob[] | undefined };

  const handleFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tags', tags);
    await importMutation.mutateAsync(formData);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith('.csv')) handleFile(file);
  };

  return (
    <div className="fade-in">
      <h1 style={{ fontSize: '1.75rem', marginBottom: 24 }}>Import Contacts</h1>

      <div className="card" style={{ marginBottom: 32 }}>
        <div
          onDragOver={e => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          style={{
            border: `2px dashed ${dragActive ? 'var(--accent)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)', padding: 48, textAlign: 'center', cursor: 'pointer',
            background: dragActive ? 'var(--accent-dim)' : 'transparent', transition: 'all 0.2s',
          }}
        >
          <Upload size={40} color={dragActive ? 'var(--accent)' : 'var(--text-muted)'} style={{ marginBottom: 12 }} />
          <p style={{ fontWeight: 600, marginBottom: 4 }}>Drop your CSV file here</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>or click to browse — CSV files only</p>
        </div>
        <input ref={fileRef} type="file" accept=".csv" hidden onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />

        <div style={{ marginTop: 20 }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Tags to apply (comma-separated)</label>
          <input placeholder="e.g. newsletter, cloud-pros" value={tags} onChange={e => setTags(e.target.value)} style={{ maxWidth: 400 }} />
        </div>

        {importMutation.isSuccess && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, color: 'var(--success)' }}>
            <CheckCircle size={16} /> Import started — processing in background
          </div>
        )}
        {importMutation.isError && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, color: 'var(--danger)' }}>
            <XCircle size={16} /> {importMutation.error?.message}
          </div>
        )}
      </div>

      <h2 style={{ fontSize: '1.125rem', marginBottom: 16 }}>Recent Imports</h2>
      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table>
          <thead><tr><th>File</th><th>Status</th><th>Total</th><th>Imported</th><th>Duplicates</th><th>Errors</th><th>Date</th></tr></thead>
          <tbody>
            {(!imports || imports.length === 0) && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No imports yet</td></tr>}
            {imports?.map(j => (
              <tr key={j.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{j.original_filename}</td>
                <td><StatusBadge status={j.status} /></td>
                <td>{j.total_rows.toLocaleString()}</td>
                <td style={{ color: 'var(--success)' }}>{j.imported_count.toLocaleString()}</td>
                <td style={{ color: 'var(--warning)' }}>{j.duplicate_count}</td>
                <td style={{ color: j.error_count > 0 ? 'var(--danger)' : 'inherit' }}>{j.error_count}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(j.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

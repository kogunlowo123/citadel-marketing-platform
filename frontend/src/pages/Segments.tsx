import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useSegments, useCreateSegment } from '../api/hooks';

interface Segment { id: string; name: string; description: string | null; contact_count: number; is_dynamic: boolean; rules: unknown }
interface SegmentList { items: Segment[] }

export default function Segments() {
  const { data } = useSegments() as { data: SegmentList | undefined };
  const createMutation = useCreateSegment();
  const segments = data?.items || [];

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [field, setField] = useState('tags');
  const [operator, setOperator] = useState('contains');
  const [value, setValue] = useState('');

  const handleCreate = async () => {
    await createMutation.mutateAsync({ name, description, rules: [{ field, operator, value }] });
    setShowCreate(false);
    setName(''); setDescription(''); setValue('');
  };

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.75rem' }}>Segments</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}><Plus size={16} style={{ marginRight: 8 }} />New Segment</button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: '1.125rem', marginBottom: 16 }}>Create Segment</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input placeholder="Segment name" value={name} onChange={e => setName(e.target.value)} />
            <input placeholder="Description (optional)" value={description} onChange={e => setDescription(e.target.value)} />
            <div style={{ display: 'flex', gap: 12 }}>
              <select value={field} onChange={e => setField(e.target.value)} style={{ flex: 1 }}>
                <option value="tags">Tags</option><option value="source">Source</option><option value="company">Company</option>
                <option value="engagement_score">Engagement Score</option><option value="email">Email</option>
              </select>
              <select value={operator} onChange={e => setOperator(e.target.value)} style={{ flex: 1 }}>
                <option value="contains">Contains</option><option value="equals">Equals</option><option value="not_contains">Not contains</option>
                <option value="greater_than">Greater than</option><option value="less_than">Less than</option>
              </select>
              <input placeholder="Value" value={value} onChange={e => setValue(e.target.value)} style={{ flex: 1 }} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleCreate} disabled={!name || !value || createMutation.isPending}>Create</button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
        {segments.map(s => (
          <div key={s.id} className="card">
            <h3 style={{ fontSize: '1rem', marginBottom: 8 }}>{s.name}</h3>
            {s.description && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 12 }}>{s.description}</p>}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700 }}>{s.contact_count.toLocaleString()}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.is_dynamic ? 'Dynamic' : 'Static'}</span>
            </div>
          </div>
        ))}
        {segments.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No segments created yet</p>}
      </div>
    </div>
  );
}

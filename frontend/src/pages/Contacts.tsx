import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { useContacts } from '../api/hooks';

interface Contact {
  id: string; email: string; first_name: string | null; last_name: string | null;
  status: string; tags: string[]; engagement_score: number; source: string; created_at: string;
}
interface ContactList { items: Contact[]; total: number; page: number; per_page: number }

export default function Contacts() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const filters: Record<string, string> = {};
  if (search) filters.search = search;
  if (statusFilter) filters.status = statusFilter;

  const { data, isLoading } = useContacts(page, filters) as { data: ContactList | undefined; isLoading: boolean };
  const contacts = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 50);

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.75rem' }}>Contacts <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 400 }}>({total.toLocaleString()})</span></h1>
        <button className="btn-primary" onClick={() => navigate('/contacts/import')}><Upload size={16} style={{ marginRight: 8 }} />Import CSV</button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <input placeholder="Search contacts..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} style={{ maxWidth: 300 }} />
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }} style={{ maxWidth: 160 }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="unsubscribed">Unsubscribed</option>
          <option value="bounced">Bounced</option>
          <option value="cleaned">Cleaned</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Tags</th><th>Score</th><th>Source</th></tr></thead>
          <tbody>
            {isLoading && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</td></tr>}
            {!isLoading && contacts.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No contacts found</td></tr>}
            {contacts.map(c => (
              <tr key={c.id}>
                <td style={{ fontWeight: 500 }}>{[c.first_name, c.last_name].filter(Boolean).join(' ') || '—'}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{c.email}</td>
                <td><StatusBadge status={c.status} /></td>
                <td>{c.tags.length > 0 ? c.tags.slice(0, 3).map(t => <span key={t} style={{ background: 'var(--accent-dim)', color: 'var(--accent)', padding: '2px 8px', borderRadius: 12, fontSize: '0.7rem', marginRight: 4 }}>{t}</span>) : '—'}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{c.engagement_score}</td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{c.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          <button className="btn-secondary btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button>
          <span style={{ padding: '6px 12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Page {page} of {totalPages}</span>
          <button className="btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}

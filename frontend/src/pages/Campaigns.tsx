import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Send } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { useCampaigns, useSendCampaign } from '../api/hooks';

interface Campaign {
  id: string; name: string; subject: string; status: string;
  sent_count: number; open_count: number; click_count: number;
  open_rate: number; click_rate: number; created_at: string; scheduled_at: string | null;
}
interface CampaignList { items: Campaign[]; total: number }

export default function Campaigns() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState('');
  const { data, isLoading } = useCampaigns(1, statusFilter || undefined) as { data: CampaignList | undefined; isLoading: boolean };
  const sendMutation = useSendCampaign();
  const campaigns = data?.items || [];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.75rem' }}>Campaigns</h1>
        <button className="btn-primary" onClick={() => navigate('/campaigns/new')}><Plus size={16} style={{ marginRight: 8 }} />New Campaign</button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['', 'draft', 'scheduled', 'sending', 'sent'].map(s => (
          <button key={s} className={statusFilter === s ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'} onClick={() => setStatusFilter(s)}>
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'auto' }}>
        <table>
          <thead><tr><th>Name</th><th>Subject</th><th>Status</th><th>Sent</th><th>Open Rate</th><th>Click Rate</th><th>Actions</th></tr></thead>
          <tbody>
            {isLoading && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</td></tr>}
            {!isLoading && campaigns.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No campaigns</td></tr>}
            {campaigns.map(c => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.subject}</td>
                <td><StatusBadge status={c.status} /></td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{c.sent_count.toLocaleString()}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--success)' }}>{c.open_rate.toFixed(1)}%</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{c.click_rate.toFixed(1)}%</td>
                <td>
                  {(c.status === 'draft' || c.status === 'scheduled') && (
                    <button className="btn-primary btn-sm" onClick={() => sendMutation.mutate(c.id)} disabled={sendMutation.isPending}>
                      <Send size={12} style={{ marginRight: 4 }} />Send
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

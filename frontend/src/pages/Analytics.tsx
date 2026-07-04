import { useState } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useEngagement, useCampaignComparison } from '../api/hooks';

interface EngagementData { date: string; opens: number; clicks: number; sends: number }
interface CampaignComp { campaign_id: string; name: string; sent: number; opens: number; open_rate: number; click_rate: number }

export default function Analytics() {
  const [days, setDays] = useState(30);
  const { data: engagement } = useEngagement(days) as { data: { data: EngagementData[] } | undefined };
  const { data: campaignComp } = useCampaignComparison() as { data: CampaignComp[] | undefined };

  const chartData = engagement?.data || [];
  const campaigns = campaignComp || [];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.75rem' }}>Analytics</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {[7, 30, 90].map(d => (
            <button key={d} className={days === d ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'} onClick={() => setDays(d)}>{d}d</button>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: '1rem', marginBottom: 20 }}>Engagement Over Time</h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="aOpens" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} /><stop offset="95%" stopColor="#00d4ff" stopOpacity={0} /></linearGradient>
              <linearGradient id="aClicks" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00c853" stopOpacity={0.3} /><stop offset="95%" stopColor="#00c853" stopOpacity={0} /></linearGradient>
            </defs>
            <XAxis dataKey="date" stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
            <YAxis stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 8, color: '#e0e0e0', fontSize: 12 }} />
            <Area type="monotone" dataKey="sends" stroke="#666" fill="none" strokeDasharray="4 4" />
            <Area type="monotone" dataKey="opens" stroke="#00d4ff" fillOpacity={1} fill="url(#aOpens)" />
            <Area type="monotone" dataKey="clicks" stroke="#00c853" fillOpacity={1} fill="url(#aClicks)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 style={{ fontSize: '1rem', marginBottom: 20 }}>Campaign Performance</h2>
        {campaigns.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={campaigns} layout="vertical">
              <XAxis type="number" stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
              <YAxis type="category" dataKey="name" stroke="#333" tick={{ fill: '#888', fontSize: 11 }} width={150} />
              <Tooltip contentStyle={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 8, color: '#e0e0e0', fontSize: 12 }} />
              <Bar dataKey="open_rate" fill="#00d4ff" name="Open Rate %" radius={[0, 4, 4, 0]} />
              <Bar dataKey="click_rate" fill="#00c853" name="Click Rate %" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>No campaign data yet</p>
        )}
      </div>
    </div>
  );
}

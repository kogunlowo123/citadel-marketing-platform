import { Users, Mail, Send, MousePointerClick } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import StatsCard from '../components/StatsCard';
import { useOverview, useEngagement } from '../api/hooks';

export default function Dashboard() {
  const { data: overview } = useOverview() as { data: Record<string, number> | undefined };
  const { data: engagement } = useEngagement(30) as { data: { data: Array<{ date: string; opens: number; clicks: number; sends: number }> } | undefined };

  const stats = overview || { total_contacts: 0, total_campaigns: 0, total_emails_sent: 0, overall_open_rate: 0 };
  const chartData = engagement?.data || [];

  return (
    <div className="fade-in">
      <h1 style={{ fontSize: '1.75rem', marginBottom: 24 }}>Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginBottom: 32 }}>
        <StatsCard title="Total Contacts" value={stats.total_contacts} icon={Users} color="var(--accent)" />
        <StatsCard title="Campaigns" value={stats.total_campaigns} icon={Mail} color="var(--success)" />
        <StatsCard title="Emails Sent" value={stats.total_emails_sent} icon={Send} color="var(--warning)" />
        <StatsCard title="Open Rate" value={`${(stats.overall_open_rate || 0).toFixed(1)}%`} icon={MousePointerClick} color="#a855f7" />
      </div>

      <div className="card" style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: '1rem', marginBottom: 20 }}>Engagement (30 days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="openGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="clickGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00c853" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00c853" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
            <YAxis stroke="#333" tick={{ fill: '#666', fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 8, color: '#e0e0e0', fontSize: 12 }} />
            <Area type="monotone" dataKey="opens" stroke="#00d4ff" fillOpacity={1} fill="url(#openGrad)" />
            <Area type="monotone" dataKey="clicks" stroke="#00c853" fillOpacity={1} fill="url(#clickGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

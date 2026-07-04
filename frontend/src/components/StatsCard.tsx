import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  icon: LucideIcon;
  color?: string;
}

export default function StatsCard({ title, value, change, icon: Icon, color = 'var(--accent)' }: StatsCardProps) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
      <div style={{
        width: 48, height: 48, borderRadius: 'var(--radius-sm)',
        background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: '1.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {change && (
          <div style={{ fontSize: '0.75rem', color: change.startsWith('+') ? 'var(--success)' : change.startsWith('-') ? 'var(--danger)' : 'var(--text-muted)', marginTop: 4 }}>
            {change}
          </div>
        )}
      </div>
    </div>
  );
}

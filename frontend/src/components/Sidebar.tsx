import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Mail, BarChart3, Workflow, Upload, Target } from 'lucide-react';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/contacts', label: 'Contacts', icon: Users },
  { to: '/campaigns', label: 'Campaigns', icon: Mail },
  { to: '/segments', label: 'Segments', icon: Target },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/workflows', label: 'Workflows', icon: Workflow },
  { to: '/contacts/import', label: 'Import', icon: Upload },
];

export default function Sidebar() {
  return (
    <aside style={{
      width: 260, position: 'fixed', top: 0, left: 0, bottom: 0,
      background: 'var(--surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', padding: '24px 0',
    }}>
      <div style={{ padding: '0 24px 32px', fontFamily: 'var(--font-heading)', fontSize: '1.25rem', color: 'var(--accent)', fontWeight: 800 }}>
        Citadel Marketing
      </div>
      <nav style={{ flex: 1 }}>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 24px', fontSize: '0.875rem', fontWeight: 500,
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
              transition: 'all 0.15s',
              textDecoration: 'none',
            })}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '0 24px', fontSize: '0.7rem', color: '#444' }}>v1.0.0</div>
    </aside>
  );
}

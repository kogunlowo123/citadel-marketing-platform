import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import { useAuth } from '../hooks/useAuth';

export default function Layout({ children }: { children: ReactNode }) {
  const { logout } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, marginLeft: 260, padding: '32px 40px', maxWidth: 'calc(100vw - 260px)' }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 24 }}>
          <button className="btn-secondary btn-sm" onClick={logout}>Logout</button>
        </div>
        <div className="fade-in">{children}</div>
      </main>
    </div>
  );
}

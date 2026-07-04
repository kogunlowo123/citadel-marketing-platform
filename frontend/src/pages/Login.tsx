import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useLogin, useSetup } from '../api/hooks';

export default function Login() {
  const { login } = useAuth();
  const loginMutation = useLogin();
  const setupMutation = useSetup();
  const [isSetup, setIsSetup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const result = await loginMutation.mutateAsync({ email, password });
      login(result.access_token);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      if (msg.includes('no users') || msg.includes('not found')) {
        setIsSetup(true);
        setError('No admin account found. Create one below.');
      } else {
        setError(msg);
      }
    }
  };

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await setupMutation.mutateAsync({ email, password, name });
      const result = await loginMutation.mutateAsync({ email, password });
      login(result.access_token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Setup failed');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="card" style={{ width: 400, textAlign: 'center' }}>
        <h1 style={{ color: 'var(--accent)', fontSize: '1.5rem', marginBottom: 8 }}>Citadel Marketing</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: 32 }}>
          {isSetup ? 'Create your admin account' : 'Sign in to your dashboard'}
        </p>
        {error && <div style={{ background: 'rgba(255,23,68,0.1)', color: 'var(--danger)', padding: '10px 16px', borderRadius: 'var(--radius-sm)', marginBottom: 16, fontSize: '0.8rem' }}>{error}</div>}
        <form onSubmit={isSetup ? handleSetup : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {isSetup && <input placeholder="Full name" value={name} onChange={e => setName(e.target.value)} required />}
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
          <button className="btn-primary" type="submit" disabled={loginMutation.isPending || setupMutation.isPending}>
            {isSetup ? 'Create Account' : 'Sign In'}
          </button>
        </form>
        {!isSetup && (
          <button onClick={() => setIsSetup(true)} style={{ background: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 16, border: 'none', cursor: 'pointer' }}>
            First time? Create admin account
          </button>
        )}
      </div>
    </div>
  );
}

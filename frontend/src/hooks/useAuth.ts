import { useState, useCallback } from 'react';

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem('citadel_token'));

  const login = useCallback((newToken: string) => {
    localStorage.setItem('citadel_token', newToken);
    setToken(newToken);
    window.location.reload();
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('citadel_token');
    setToken(null);
  }, []);

  return {
    isAuthenticated: !!token,
    token,
    login,
    logout,
  };
}

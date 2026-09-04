import { useState, useEffect, useCallback } from 'react';
import type { User, TokenResponse } from '../types';
import { api } from '../api/client';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('wisense_user');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('wisense_user');
        localStorage.removeItem('wisense_token');
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await api.post<TokenResponse>('/auth/login', { username, password });
    localStorage.setItem('wisense_token', data.access_token);
    const u: User = { id: data.user_id, username: data.username, email: '' };
    localStorage.setItem('wisense_user', JSON.stringify(u));
    setUser(u);
    return u;
  }, []);

  const register = useCallback(async (username: string, email: string, password: string) => {
    const data = await api.post<TokenResponse>('/auth/register', { username, email, password });
    localStorage.setItem('wisense_token', data.access_token);
    const u: User = { id: data.user_id, username: data.username, email };
    localStorage.setItem('wisense_user', JSON.stringify(u));
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('wisense_token');
    localStorage.removeItem('wisense_user');
    setUser(null);
  }, []);

  return { user, loading, login, register, logout, isAuthenticated: !!user };
}
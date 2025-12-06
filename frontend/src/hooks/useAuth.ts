import { useState, useEffect } from 'react';
import { authService, User } from '@/utils/auth';
import { useNavigate } from 'react-router-dom';

export function useAuth() {
  const [user, setUser] = useState<User | null>(authService.getUser());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const isAuthenticated = await authService.checkAuth();
      if (!isAuthenticated) {
        setUser(null);
      } else {
        setUser(authService.getUser());
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const user = await authService.login(email, password);
      setUser(user);
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Login failed' };
    }
  };

  const register = async (data: {
    email: string;
    password: string;
    user_type: 'candidat' | 'recruteur';
    nom: string;
    prenom: string;
    entreprise?: string;
    telephone?: string;
  }) => {
    try {
      const user = await authService.register(data);
      setUser(user);
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Registration failed' };
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
    navigate('/');
  };

  return {
    user,
    loading,
    isAuthenticated: !!user,
    isCandidate: user?.user_type === 'candidat',
    isRecruiter: user?.user_type === 'recruteur',
    login,
    register,
    logout,
    checkAuth,
  };
}
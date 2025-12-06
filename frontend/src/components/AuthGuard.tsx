import { ReactNode, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface AuthGuardProps {
  children: ReactNode;
  requireAuth?: boolean;
  requireRole?: 'candidat' | 'recruteur';
  redirectTo?: string;
}

export function AuthGuard({ 
  children, 
  requireAuth = true, 
  requireRole,
  redirectTo = '/' 
}: AuthGuardProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;

    if (requireAuth && !isAuthenticated) {
      navigate(redirectTo);
      return;
    }

    if (isAuthenticated && requireRole && user?.user_type !== requireRole) {
      // Rediriger vers le dashboard approprié
      if (user?.user_type === 'candidat') {
        navigate('/candidate/dashboard');
      } else {
        navigate('/recruiter/dashboard');
      }
    }
  }, [loading, isAuthenticated, user, requireAuth, requireRole, navigate, redirectTo]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return null;
  }

  if (requireRole && user?.user_type !== requireRole) {
    return null;
  }

  return <>{children}</>;
}
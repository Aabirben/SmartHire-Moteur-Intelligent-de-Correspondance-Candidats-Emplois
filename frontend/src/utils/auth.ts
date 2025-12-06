import { authApi } from './api';

export interface User {
  id: number;
  email: string;
  user_type: 'candidat' | 'recruteur';
  nom: string;
  prenom: string;
  entreprise?: string;
  telephone?: string;
}

class AuthService {
  private user: User | null = null;
  private token: string | null = null;

  constructor() {
    // Vérifier l'authentification au chargement
    this.checkAuth();
  }

  async login(email: string, password: string): Promise<User> {
    try {
      const response = await authApi.login(email, password);
      this.user = response.user;
      this.saveToStorage();
      return this.user!;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Login failed');
    }
  }

  async register(data: {
    email: string;
    password: string;
    user_type: 'candidat' | 'recruteur';
    nom: string;
    prenom: string;
    entreprise?: string;
    telephone?: string;
  }): Promise<User> {
    try {
      const response = await authApi.register(data);
      this.user = response.user;
      this.saveToStorage();
      return this.user!;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Registration failed');
    }
  }

  async logout(): Promise<void> {
    try {
      await authApi.logout();
      this.clearStorage();
      this.user = null;
      this.token = null;
    } catch (error) {
      console.error('Logout error:', error);
      this.clearStorage();
    }
  }

  async checkAuth(): Promise<boolean> {
    try {
      const response = await authApi.checkAuth();
      if (response.authenticated) {
        this.user = response.user;
        this.saveToStorage();
        return true;
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  getUser(): User | null {
    if (!this.user) {
      const stored = localStorage.getItem('smarthire_user');
      if (stored) {
        this.user = JSON.parse(stored);
      }
    }
    return this.user;
  }

  isAuthenticated(): boolean {
    return !!this.getUser();
  }

  isCandidate(): boolean {
    const user = this.getUser();
    return user?.user_type === 'candidat';
  }

  isRecruiter(): boolean {
    const user = this.getUser();
    return user?.user_type === 'recruteur';
  }

  private saveToStorage(): void {
    if (this.user) {
      localStorage.setItem('smarthire_user', JSON.stringify(this.user));
    }
  }

  private clearStorage(): void {
    localStorage.removeItem('smarthire_user');
    localStorage.removeItem('smarthire_jobs');
    localStorage.removeItem('smarthire_cv_uploaded');
  }
}

export const authService = new AuthService();
import api from './api';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  username: string;
  password: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

class AuthService {
  private tokenKey = 'auth_token';
  private userKey = 'user_data';

  async login(credentials: LoginCredentials): Promise<User> {
    const response = await api.login(credentials);
    this.setToken(response.access_token);
    
    try {
      // Wait a small amount of time to ensure token is set
      await new Promise(resolve => setTimeout(resolve, 100));
      const userData = await this.getCurrentUser();
      this.setUser(userData);
      return userData;
    } catch (error) {
      // If getting user data fails, clean up and throw
      this.logout();
      throw new Error('Failed to get user data after login');
    }
  }

  async register(credentials: RegisterCredentials): Promise<User> {
    await api.register(credentials);  // Register first
    // Return the result of login instead of the registration response
    return await this.login({
        username: credentials.username,
        password: credentials.password
    });
}

  async getCurrentUser(): Promise<User> {
    const user = await api.getCurrentUser();
    return user;
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    api.setToken(null);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  private setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
    api.setToken(token);
  }

  private setUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  getUser(): User | null {
    const userData = localStorage.getItem(this.userKey);
    return userData ? JSON.parse(userData) : null;
  }

  isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getUser();
  }

  initializeAuth(): void {
    const token = this.getToken();
    if (token) {
      api.setToken(token);
    }
  }
}

export const authService = new AuthService();
export default authService;
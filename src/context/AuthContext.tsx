import React, { createContext, useContext, useState, useEffect } from 'react';
import authService, { User } from '../services/authService';
import api from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<User>; // Changed return type to Promise<User>
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = authService.getToken();
      if (token) {
        api.setToken(token); // Immediately set the token in ApiService
        const storedUser = authService.getUser();
        if (storedUser) {
          try {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
          } catch (error) {
            console.error('Error fetching current user:', error);
            authService.logout();
          }
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (username: string, password: string): Promise<User> => {
    const user = await authService.login({ username, password });
    setUser(user);
    return user;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const value = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading
  };

  if (loading) {
    return <div>Loading...</div>; // You can replace this with a proper loading component
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
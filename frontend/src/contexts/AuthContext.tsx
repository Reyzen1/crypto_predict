// File: frontend/src/contexts/AuthContext.tsx
// Authentication Context with useAuthStatus hook fix

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '@/services/api';
import { handleApiError } from '@/lib/utils';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isVerified: boolean;
  createdAt: string;
}

interface PersonalSpaceData {
  portfolio: any[];
  watchlist: string[];
  preferences: Record<string, any>;
}

interface AuthContextType {
  // Authentication state
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Authentication actions
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  
  // Personal space features (only available when logged in)
  personalSpace: PersonalSpaceData;
  
  // Actions for personal space
  updatePortfolio: (portfolio: any[]) => void;
  updateWatchlist: (watchlist: string[]) => void;
  updatePreferences: (preferences: Record<string, any>) => void;
}

interface AuthProviderProps {
  children: ReactNode;
}

// =====================================
// CONTEXT CREATION
// =====================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// =====================================
// CUSTOM HOOKS
// =====================================

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Fix: Add missing useAuthStatus hook
export const useAuthStatus = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  return {
    isAuthenticated,
    isLoading,
    user,
  };
};

// =====================================
// AUTH PROVIDER COMPONENT
// =====================================

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Personal space data (only for logged-in users)
  const [personalSpace, setPersonalSpace] = useState<PersonalSpaceData>({
    portfolio: [],
    watchlist: [],
    preferences: {}
  });

  // Check for existing session on mount
  useEffect(() => {
    checkExistingSession();
  }, []);

  // =====================================
  // AUTHENTICATION FUNCTIONS
  // =====================================

  const checkExistingSession = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      // Verify token with backend
      const userData = await apiService.getMe();
      setUser({
        id: userData.id,
        email: userData.email,
        firstName: userData.first_name,
        lastName: userData.last_name,
        isVerified: userData.is_verified,
        createdAt: userData.created_at
      });
      
      // Load personal space data
      await loadPersonalSpaceData();
    } catch (error) {
      console.error('Session check failed:', error);
      localStorage.removeItem('access_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      const data = await apiService.login(email, password);

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      
      // Set user data
      setUser({
        id: data.user.id,
        email: data.user.email,
        firstName: data.user.first_name,
        lastName: data.user.last_name,
        isVerified: data.user.is_verified,
        createdAt: data.user.created_at
      });

      // Load personal space data
      await loadPersonalSpaceData();

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: handleApiError(error)
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (
    email: string, 
    password: string, 
    firstName?: string, 
    lastName?: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      await apiService.register(email, password, firstName, lastName);
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: handleApiError(error)
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    setPersonalSpace({
      portfolio: [],
      watchlist: [],
      preferences: {}
    });
  };

  // =====================================
  // PERSONAL SPACE FUNCTIONS
  // =====================================

  const loadPersonalSpaceData = async () => {
    if (!user) return;
    
    try {
      // For now, use placeholder data
      // TODO: Implement when backend personal space endpoints are available
      setPersonalSpace({
        portfolio: [],
        watchlist: [],
        preferences: {}
      });
    } catch (error) {
      console.error('Failed to load personal space data:', error);
    }
  };

  const updatePortfolio = (portfolio: any[]) => {
    setPersonalSpace(prev => ({ ...prev, portfolio }));
    // TODO: Sync with backend
  };

  const updateWatchlist = (watchlist: string[]) => {
    setPersonalSpace(prev => ({ ...prev, watchlist }));
    // TODO: Sync with backend
  };

  const updatePreferences = (preferences: Record<string, any>) => {
    setPersonalSpace(prev => ({ ...prev, preferences }));
    // TODO: Sync with backend
  };

  // =====================================
  // CONTEXT VALUE
  // =====================================

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    personalSpace,
    updatePortfolio,
    updateWatchlist,
    updatePreferences,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
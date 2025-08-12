// File: frontend/src/contexts/AuthContext.tsx
// Optional Authentication Context - Personal space only, all features remain public

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
// CUSTOM HOOK
// =====================================

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// =====================================
// AUTH PROVIDER COMPONENT
// =====================================

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Personal space data (only for logged-in users) - Fixed typing
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
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
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
      } else {
        // Token is invalid, remove it
        localStorage.removeItem('access_token');
      }
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
      
      // Use form data for OAuth2 compatibility
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        // Save token
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
      } else {
        return { 
          success: false, 
          error: data.detail || 'Login failed. Please check your credentials.' 
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: 'Network error. Please try again.' 
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

      const registerData = {
        email,
        password,
        confirm_password: password,
        first_name: firstName || '',
        last_name: lastName || ''
      };

      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(registerData)
      });

      const data = await response.json();

      if (response.ok) {
        // Save token
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

        // Initialize empty personal space
        setPersonalSpace({
          portfolio: [],
          watchlist: [],
          preferences: {}
        });

        return { success: true };
      } else {
        return { 
          success: false, 
          error: data.detail || 'Registration failed. Please try again.' 
        };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: 'Network error. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    // Clear all local data
    localStorage.removeItem('access_token');
    setUser(null);
    setPersonalSpace({
      portfolio: [],
      watchlist: [],
      preferences: {}
    });

    // Optional: Call backend logout endpoint
    fetch('/api/v1/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    }).catch(error => {
      console.log('Logout endpoint call failed:', error);
    });
  };

  // =====================================
  // PERSONAL SPACE FUNCTIONS
  // =====================================

  const loadPersonalSpaceData = async () => {
    try {
      // Load personal data from localStorage or API
      const storedPortfolio = localStorage.getItem(`portfolio_${user?.id}`);
      const storedWatchlist = localStorage.getItem(`watchlist_${user?.id}`);
      const storedPreferences = localStorage.getItem(`preferences_${user?.id}`);

      setPersonalSpace({
        portfolio: storedPortfolio ? JSON.parse(storedPortfolio) : [],
        watchlist: storedWatchlist ? JSON.parse(storedWatchlist) : [],
        preferences: storedPreferences ? JSON.parse(storedPreferences) : {}
      });
    } catch (error) {
      console.error('Failed to load personal space data:', error);
      // Reset to default values on error
      setPersonalSpace({
        portfolio: [],
        watchlist: [],
        preferences: {}
      });
    }
  };

  const updatePortfolio = (portfolio: any[]) => {
    setPersonalSpace(prev => ({ ...prev, portfolio }));
    if (user) {
      localStorage.setItem(`portfolio_${user.id}`, JSON.stringify(portfolio));
    }
  };

  const updateWatchlist = (watchlist: string[]) => {
    setPersonalSpace(prev => ({ ...prev, watchlist }));
    if (user) {
      localStorage.setItem(`watchlist_${user.id}`, JSON.stringify(watchlist));
    }
  };

  const updatePreferences = (preferences: Record<string, any>) => {
    setPersonalSpace(prev => ({ ...prev, preferences }));
    if (user) {
      localStorage.setItem(`preferences_${user.id}`, JSON.stringify(preferences));
    }
  };

  // =====================================
  // CONTEXT VALUE
  // =====================================

  const contextValue: AuthContextType = {
    // Authentication state
    user,
    isAuthenticated: !!user,
    isLoading,
    
    // Authentication actions
    login,
    register,
    logout,
    
    // Personal space (only available when logged in)
    personalSpace,
    
    // Personal space actions
    updatePortfolio,
    updateWatchlist,
    updatePreferences
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// =====================================
// UTILITY HOOKS
// =====================================

// Hook to check if user has personal space access
export const usePersonalSpace = () => {
  const { isAuthenticated, personalSpace } = useAuth();
  
  return {
    hasAccess: isAuthenticated,
    data: isAuthenticated ? personalSpace : null
  };
};

// Hook for authentication status only
export const useAuthStatus = () => {
  const { isAuthenticated, isLoading, user } = useAuth();
  
  return {
    isAuthenticated,
    isLoading,
    user: user ? {
      name: user.firstName ? `${user.firstName} ${user.lastName}`.trim() : user.email,
      email: user.email
    } : null
  };
};

export default AuthProvider;
// File: frontend/src/components/auth/DemoLogin.tsx
// Demo login component for easy testing

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ToastProvider';
import { User, Loader2, Play } from 'lucide-react';

// =====================================
// DEMO CREDENTIALS
// =====================================

const DEMO_CREDENTIALS = {
  email: 'testuser2@example.com',
  password: 'TestPassword123!'
};

// =====================================
// DEMO LOGIN COMPONENT
// =====================================

export const DemoLogin: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const toast = useToast();

  const handleDemoLogin = async () => {
    if (isAuthenticated || isLoading) return;

    setIsLoading(true);
    try {
      const result = await login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);
      
      if (result.success) {
        toast.success('Demo login successful!', 'You are now logged in with test account');
      } else {
        toast.error('Demo login failed', result.error || 'Please check if backend is running');
      }
    } catch (error) {
      toast.error('Demo login error', 'Failed to connect to backend service');
    } finally {
      setIsLoading(false);
    }
  };

  if (isAuthenticated) {
    return null; // Hide when user is already logged in
  }

  return (
    <Button
      onClick={handleDemoLogin}
      disabled={isLoading}
      variant="outline"
      size="sm"
      className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10 hover:border-blue-400"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      ) : (
        <Play className="w-4 h-4 mr-2" />
      )}
      Demo Login
    </Button>
  );
};

// =====================================
// DEMO STATUS INDICATOR
// =====================================

interface DemoStatusProps {
  className?: string;
}

export const DemoStatus: React.FC<DemoStatusProps> = ({ className = '' }) => {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated || user?.email !== DEMO_CREDENTIALS.email) {
    return null;
  }

  return (
    <div className={`flex items-center space-x-2 text-sm ${className}`}>
      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
      <span className="text-green-400">Demo Mode</span>
    </div>
  );
};

// =====================================
// DEMO INFO CARD
// =====================================

export const DemoInfoCard: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) return null;

  return (
    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-6">
      <div className="flex items-start space-x-3">
        <User className="w-5 h-5 text-blue-400 mt-0.5" />
        <div>
          <h3 className="text-blue-400 font-medium mb-2">Try Demo Mode</h3>
          <p className="text-gray-300 text-sm mb-3">
            Experience all features with a demo account. Login to access real-time WebSocket updates and personalized features.
          </p>
          <div className="bg-gray-800/50 rounded p-2 text-xs font-mono text-gray-400 mb-3">
            <div>Email: {DEMO_CREDENTIALS.email}</div>
            <div>Password: {DEMO_CREDENTIALS.password}</div>
          </div>
          <DemoLogin />
        </div>
      </div>
    </div>
  );
};
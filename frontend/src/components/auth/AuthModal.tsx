// File: frontend/src/components/auth/AuthModal.tsx
// Authentication modal for login and registration

'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ToastProvider';
import { DemoLogin } from './DemoLogin';
import { 
  Mail, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  Loader2, 
  LogIn,
  UserPlus 
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultMode?: 'login' | 'register';
}

interface FormData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

// =====================================
// MAIN COMPONENT
// =====================================

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  defaultMode = 'login'
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(defaultMode);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  });

  const { login, register } = useAuth();
  const toast = useToast();

  // =====================================
  // FORM HANDLERS
  // =====================================

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.email || !formData.password) {
      toast.warning('Please fill in all required fields');
      return;
    }

    setIsLoading(true);

    try {
      if (mode === 'login') {
        const result = await login(formData.email, formData.password);
        if (result.success) {
          toast.success('Welcome back!', 'You have been successfully logged in');
          onClose();
          resetForm();
        } else {
          toast.error('Login failed', result.error);
        }
      } else {
        const result = await register(
          formData.email, 
          formData.password, 
          formData.firstName, 
          formData.lastName
        );
        if (result.success) {
          toast.success('Registration successful!', 'You can now login with your credentials');
          setMode('login');
          setFormData(prev => ({ ...prev, password: '', firstName: '', lastName: '' }));
        } else {
          toast.error('Registration failed', result.error);
        }
      }
    } catch (error) {
      toast.error('Network error', 'Please check your connection and try again');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      firstName: '',
      lastName: ''
    });
    setShowPassword(false);
  };

  const handleModeSwitch = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    resetForm();
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  // =====================================
  // RENDER
  // =====================================

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-gray-800 border-gray-700 text-white">
        <DialogHeader>
          <DialogTitle className="text-2xl font-semibold text-center">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Demo Login Section */}
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <div className="text-center mb-3">
              <h4 className="text-blue-400 font-medium mb-1">Try Demo Mode</h4>
              <p className="text-gray-400 text-sm mb-3">
                Quick login with test account for full features
              </p>
              <DemoLogin />
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-600" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-gray-800 px-2 text-gray-400">Or continue with email</span>
            </div>
          </div>

          {/* Auth Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-300">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="pl-10 bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                  placeholder="your@email.com"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Name Fields (Register only) */}
            {mode === 'register' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="firstName" className="text-gray-300">First Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="firstName"
                      type="text"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      className="pl-10 bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                      placeholder="First"
                      disabled={isLoading}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName" className="text-gray-300">Last Name</Label>
                  <Input
                    id="lastName"
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                    placeholder="Last"
                    disabled={isLoading}
                  />
                </div>
              </div>
            )}

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-300">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="pl-10 pr-10 bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                  placeholder="Enter your password"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 h-8 w-8 p-0 hover:bg-gray-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </Button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </>
              ) : (
                <>
                  {mode === 'login' ? (
                    <LogIn className="w-4 h-4 mr-2" />
                  ) : (
                    <UserPlus className="w-4 h-4 mr-2" />
                  )}
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                </>
              )}
            </Button>
          </form>

          {/* Mode Switch */}
          <div className="text-center text-sm text-gray-400">
            {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
            <Button
              variant="link"
              className="text-blue-400 hover:text-blue-300 p-0 ml-1 h-auto font-normal"
              onClick={handleModeSwitch}
              disabled={isLoading}
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// =====================================
// AUTH BUTTON COMPONENT
// =====================================

interface AuthButtonProps {
  variant?: 'default' | 'ghost';
  className?: string;
}

export const AuthButton: React.FC<AuthButtonProps> = ({ 
  variant = 'default',
  className = '' 
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) return null;

  return (
    <>
      <Button
        onClick={() => setIsModalOpen(true)}
        variant={variant}
        className={`text-white ${className}`}
      >
        <LogIn className="w-4 h-4 mr-2" />
        Sign In
      </Button>
      
      <AuthModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};
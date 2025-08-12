// File: frontend/src/components/auth/AuthModal.tsx
// Authentication Modal - Login/Register forms with gentle UX

'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from '@/contexts/AuthContext';
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  Heart,
  Gift,
  Shield,
  Sparkles,
  Wallet,
  Star,
  Settings
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'register';
}

interface FormData {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
}

// =====================================
// AUTH MODAL COMPONENT
// =====================================

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialMode = 'login'
}) => {
  const { login, register, isLoading } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: ''
  });

  // =====================================
  // FORM HANDLERS
  // =====================================

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(''); // Clear error when user types
  };

  const validateForm = (): boolean => {
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      return false;
    }

    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return false;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return false;
    }

    if (mode === 'register' && formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) {
      return;
    }

    try {
      let result;
      
      if (mode === 'login') {
        result = await login(formData.email, formData.password);
      } else {
        result = await register(
          formData.email,
          formData.password,
          formData.firstName,
          formData.lastName
        );
      }

      if (result.success) {
        setSuccess(mode === 'login' ? 'Welcome back!' : 'Account created successfully!');
        setTimeout(() => {
          onClose();
          // Reset form
          setFormData({
            email: '',
            password: '',
            confirmPassword: '',
            firstName: '',
            lastName: ''
          });
          setSuccess('');
        }, 1500);
      } else {
        setError(result.error || 'Something went wrong');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setSuccess('');
  };

  // =====================================
  // RENDER
  // =====================================

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-700 text-white">
        <DialogHeader className="text-center space-y-3">
          {/* Free Badge */}
          <div className="flex justify-center">
            <Badge variant="secondary" className="bg-green-600 text-white">
              <Gift className="h-3 w-3 mr-1" />
              100% Free Forever
            </Badge>
          </div>

          <DialogTitle className="text-2xl font-bold">
            {mode === 'login' ? 'Welcome Back!' : 'Join CryptoPredict'}
          </DialogTitle>
          
          <DialogDescription className="text-gray-300">
            {mode === 'login' 
              ? 'Access your personal crypto dashboard' 
              : 'Create your free personal space for portfolio tracking'
            }
          </DialogDescription>

          {/* Benefits Section */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 space-y-2">
            <div className="flex items-center space-x-2 text-blue-400 text-sm">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">Personal Space Benefits:</span>
            </div>
            <div className="grid grid-cols-1 gap-1 text-xs text-gray-300">
              <div className="flex items-center space-x-2">
                <Wallet className="h-3 w-3 text-green-400" />
                <span>Track your portfolio</span>
              </div>
              <div className="flex items-center space-x-2">
                <Star className="h-3 w-3 text-yellow-400" />
                <span>Create custom watchlists</span>
              </div>
              <div className="flex items-center space-x-2">
                <Settings className="h-3 w-3 text-purple-400" />
                <span>Save preferences</span>
              </div>
            </div>
          </div>
        </DialogHeader>

        {/* Form */}
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
                className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-400"
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
                    className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-400"
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
                  className="bg-gray-800 border-gray-600 text-white placeholder-gray-400"
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
                className="pl-10 pr-10 bg-gray-800 border-gray-600 text-white placeholder-gray-400"
                placeholder="Enter your password"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-400 hover:text-white"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Confirm Password (Register only) */}
          {mode === 'register' && (
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-gray-300">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className="pl-10 bg-gray-800 border-gray-600 text-white placeholder-gray-400"
                  placeholder="Confirm your password"
                  disabled={isLoading}
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 p-3 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-500/10 border border-green-500/30 p-3 rounded-lg">
              <p className="text-green-400 text-sm">{success}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {mode === 'login' ? 'Signing In...' : 'Creating Account...'}
              </>
            ) : (
              <>
                {mode === 'login' ? (
                  <>
                    <User className="h-4 w-4 mr-2" />
                    Sign In to Personal Space
                  </>
                ) : (
                  <>
                    <Heart className="h-4 w-4 mr-2" />
                    Create Free Account
                  </>
                )}
              </>
            )}
          </Button>

          {/* Mode Switch */}
          <div className="text-center space-y-2">
            <button
              type="button"
              onClick={switchMode}
              className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
              disabled={isLoading}
            >
              {mode === 'login' 
                ? "Don't have an account? Sign up free" 
                : 'Already have an account? Sign in'
              }
            </button>
          </div>

          {/* Free Platform Reminder */}
          <div className="border-t border-gray-700 pt-4">
            <div className="bg-gray-800/50 p-3 rounded-lg text-center space-y-2">
              <div className="flex items-center justify-center space-x-2 text-green-400">
                <Shield className="h-4 w-4" />
                <span className="text-sm font-medium">Forever Free Platform</span>
              </div>
              <p className="text-xs text-gray-400">
                All analysis tools remain free for everyone. Personal space is just for convenience.
              </p>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// =====================================
// AUTH BUTTON COMPONENT
// =====================================

interface AuthButtonProps {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
  mode?: 'login' | 'register';
  children?: React.ReactNode;
  className?: string;
}

export const AuthButton: React.FC<AuthButtonProps> = ({
  variant = 'outline',
  size = 'sm',
  mode = 'login',
  children,
  className = ''
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const defaultChildren = mode === 'login' 
    ? (
        <>
          <User className="h-4 w-4 mr-2" />
          Personal Space
        </>
      )
    : (
        <>
          <Heart className="h-4 w-4 mr-2" />
          Join Free
        </>
      );

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setIsModalOpen(true)}
        className={className}
      >
        {children || defaultChildren}
      </Button>
      
      <AuthModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialMode={mode}
      />
    </>
  );
};

export default AuthModal;
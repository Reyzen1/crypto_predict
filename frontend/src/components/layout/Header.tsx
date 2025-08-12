// File: frontend/src/components/layout/Header.tsx
// Header component with optional authentication integration

'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth, useAuthStatus } from '@/contexts/AuthContext';
import { AuthButton } from '@/components/auth/AuthModal';
import {
  Bot,
  User,
  Settings,
  LogOut,
  Menu,
  Search,
  Bell,
  Heart,
  Gift,
  Sparkles,
  Shield,
  Wallet,
  Star,
  ChevronDown
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface HeaderProps {
  className?: string;
}

// =====================================
// USER MENU COMPONENT
// =====================================

const UserMenu: React.FC = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const displayName = user.firstName 
    ? `${user.firstName} ${user.lastName}`.trim() 
    : user.email;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center space-x-2 text-white hover:text-blue-400">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-white" />
          </div>
          <span className="hidden sm:inline font-medium">{displayName}</span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-gray-800 border-gray-700">
        <div className="px-3 py-2">
          <p className="text-sm font-medium text-white">{displayName}</p>
          <p className="text-xs text-gray-400">{user.email}</p>
        </div>
        <DropdownMenuSeparator className="bg-gray-700" />
        
        <DropdownMenuItem className="text-gray-300 hover:text-white hover:bg-gray-700 cursor-pointer">
          <Wallet className="h-4 w-4 mr-2" />
          My Portfolio
        </DropdownMenuItem>
        
        <DropdownMenuItem className="text-gray-300 hover:text-white hover:bg-gray-700 cursor-pointer">
          <Star className="h-4 w-4 mr-2" />
          Watchlist
        </DropdownMenuItem>
        
        <DropdownMenuItem className="text-gray-300 hover:text-white hover:bg-gray-700 cursor-pointer">
          <Settings className="h-4 w-4 mr-2" />
          Preferences
        </DropdownMenuItem>
        
        <DropdownMenuSeparator className="bg-gray-700" />
        
        <DropdownMenuItem 
          onClick={logout}
          className="text-red-400 hover:text-red-300 hover:bg-gray-700 cursor-pointer"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

// =====================================
// NAVIGATION COMPONENT
// =====================================

const Navigation: React.FC = () => {
  return (
    <nav className="hidden md:flex space-x-6">
      <a 
        href="#live-analysis" 
        className="text-blue-400 font-medium border-b-2 border-blue-400 pb-1 transition-colors"
      >
        Live Analysis
      </a>
      <a 
        href="#ai-predictions" 
        className="text-gray-400 hover:text-white transition-colors"
      >
        AI Predictions
      </a>
      <a 
        href="#technical-charts" 
        className="text-gray-400 hover:text-white transition-colors"
      >
        Technical Charts
      </a>
      <a 
        href="#market-data" 
        className="text-gray-400 hover:text-white transition-colors"
      >
        Market Data
      </a>
    </nav>
  );
};

// =====================================
// MOBILE MENU COMPONENT
// =====================================

const MobileMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated } = useAuthStatus();

  return (
    <div className="md:hidden">
      <Button 
        variant="ghost" 
        size="sm" 
        onClick={() => setIsOpen(!isOpen)}
        className="text-gray-400 hover:text-white"
      >
        <Menu className="h-5 w-5" />
      </Button>
      
      {isOpen && (
        <div className="absolute top-full left-0 right-0 bg-gray-800 border-t border-gray-700 p-4 space-y-3">
          <a href="#live-analysis" className="block text-blue-400 font-medium">
            Live Analysis
          </a>
          <a href="#ai-predictions" className="block text-gray-400 hover:text-white">
            AI Predictions
          </a>
          <a href="#technical-charts" className="block text-gray-400 hover:text-white">
            Technical Charts
          </a>
          <a href="#market-data" className="block text-gray-400 hover:text-white">
            Market Data
          </a>
          
          {!isAuthenticated && (
            <div className="pt-3 border-t border-gray-700">
              <AuthButton 
                mode="register" 
                variant="default" 
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600"
              >
                <Heart className="h-4 w-4 mr-2" />
                Get Personal Space - FREE
              </AuthButton>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// =====================================
// MAIN HEADER COMPONENT
// =====================================

export const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  const { isAuthenticated, isLoading } = useAuthStatus();

  return (
    <div>
      {/* Free Platform Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center space-x-4 text-center">
            <Gift className="h-5 w-5" />
            <span className="font-medium text-sm sm:text-base">
              🎉 CryptoPredict is 100% FREE - All AI predictions & analysis tools available to everyone!
            </span>
            <Sparkles className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className={`bg-gray-800/50 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50 ${className}`}>
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo & Navigation */}
            <div className="flex items-center space-x-8">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Bot className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">CryptoPredict</h1>
                  <p className="text-xs text-gray-400">Free AI-Powered Analysis</p>
                </div>
              </div>
              
              {/* Navigation Menu */}
              <Navigation />
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              
              {/* Search (Hidden on mobile) */}
              <div className="hidden lg:flex items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search cryptocurrencies..."
                    className="pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 w-64"
                  />
                </div>
              </div>

              {/* Authentication Actions */}
              {!isLoading && (
                <>
                  {isAuthenticated ? (
                    <div className="flex items-center space-x-3">
                      {/* Notifications */}
                      <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white relative">
                        <Bell className="h-5 w-5" />
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs"></span>
                      </Button>
                      
                      {/* User Menu */}
                      <UserMenu />
                    </div>
                  ) : (
                    <div className="flex items-center space-x-3">
                      {/* Personal Space CTA */}
                      <AuthButton
                        mode="register"
                        variant="outline"
                        size="sm"
                        className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white hidden sm:flex"
                      >
                        <User className="h-4 w-4 mr-2" />
                        Get Personal Space - FREE
                      </AuthButton>
                      
                      {/* Sign In Button */}
                      <AuthButton
                        mode="login"
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-white hidden sm:flex"
                      >
                        Sign In
                      </AuthButton>
                    </div>
                  )}
                </>
              )}

              {/* Mobile Menu */}
              <MobileMenu />
            </div>
          </div>
        </div>
      </header>

      {/* Personal Space Benefits Bar (Show only for non-authenticated users) */}
      {!isLoading && !isAuthenticated && (
        <div className="bg-gray-900/80 border-b border-gray-700 py-2">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2 text-green-400">
                <Shield className="h-4 w-4" />
                <span>All analysis tools free</span>
              </div>
              <div className="flex items-center space-x-2 text-blue-400">
                <Wallet className="h-4 w-4" />
                <span>Personal space for portfolio</span>
              </div>
              <div className="flex items-center space-x-2 text-purple-400">
                <Heart className="h-4 w-4" />
                <span>No credit card required</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Header;
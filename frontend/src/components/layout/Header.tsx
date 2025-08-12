// File: frontend/src/components/layout/Header.tsx  
// Header component with authentication and demo features

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
import { useAuth } from '@/contexts/AuthContext';
import { AuthButton } from '@/components/auth/AuthModal';
import { DemoLogin, DemoStatus } from '@/components/auth/DemoLogin';
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

  const isDemo = user.email === 'testuser2@example.com';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center space-x-2 text-white hover:text-blue-400">
          <div className={`w-8 h-8 ${isDemo ? 'bg-gradient-to-r from-green-500 to-green-600' : 'bg-gradient-to-r from-blue-500 to-purple-600'} rounded-full flex items-center justify-center`}>
            <User className="h-4 w-4 text-white" />
          </div>
          <span className="hidden sm:inline font-medium">{displayName}</span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-gray-800 border-gray-700">
        <div className="px-3 py-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-medium text-white">{displayName}</p>
            {isDemo && (
              <Badge variant="secondary" className="bg-green-500/10 text-green-400 text-xs">
                Demo
              </Badge>
            )}
          </div>
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
  const { isAuthenticated } = useAuth();

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
        <div className="absolute top-full left-0 right-0 bg-gray-800 border-t border-gray-700 p-4 space-y-3 z-50">
          <a href="#live-analysis" className="block text-blue-400 font-medium">Live Analysis</a>
          <a href="#ai-predictions" className="block text-gray-400 hover:text-white">AI Predictions</a>
          <a href="#technical-charts" className="block text-gray-400 hover:text-white">Technical Charts</a>
          <a href="#market-data" className="block text-gray-400 hover:text-white">Market Data</a>
          
          {!isAuthenticated && (
            <div className="pt-3 border-t border-gray-600 space-y-3">
              <DemoLogin />
              <AuthButton variant="ghost" className="w-full justify-start" />
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
  const { isAuthenticated } = useAuth();

  return (
    <header className={`bg-gray-800 border-b border-gray-700 sticky top-0 z-40 ${className}`}>
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo Section */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-white">CryptoPredict</h1>
            </div>
            
            <Badge variant="secondary" className="bg-green-500/10 text-green-400 border-green-500/20 text-xs">
              <Sparkles className="h-3 w-3 mr-1" />
              AI-Powered
            </Badge>
            
            <DemoStatus className="hidden sm:flex" />
          </div>

          {/* Navigation */}
          <Navigation />

          {/* Right Section */}
          <div className="flex items-center space-x-3">
            {/* Features for authenticated users */}
            {isAuthenticated && (
              <>
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hidden sm:flex">
                  <Search className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hidden sm:flex relative">
                  <Bell className="h-4 w-4" />
                  <span className="absolute -top-1 -right-1 h-2 w-2 bg-blue-500 rounded-full"></span>
                </Button>
              </>
            )}
            
            {/* Authentication Section */}
            {isAuthenticated ? (
              <UserMenu />
            ) : (
              <div className="hidden sm:flex items-center space-x-3">
                <DemoLogin />
                <AuthButton />
              </div>
            )}

            {/* Mobile Menu */}
            <MobileMenu />
          </div>
        </div>
      </div>
    </header>
  );
};
// File: frontend/app/page.tsx
// Complete Beautiful Dashboard - Professional UI

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  TrendingUp, 
  TrendingDown, 
  Bitcoin, 
  DollarSign, 
  Target, 
  Activity,
  Brain,
  Zap,
  AlertCircle,
  Bell,
  Settings,
  User,
  Menu,
  Search,
  Filter,
  MoreVertical,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  Star,
  Clock,
  Globe,
  Wallet,
  TrendingUpIcon
} from "lucide-react";

// Import our chart component
import PriceChart from '../components/charts/PriceChart';
import { testApiService } from '../lib/api';

export default function Dashboard() {
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState(3);

  // Mock data
  const cryptoList = [
    { symbol: 'BTC', name: 'Bitcoin', price: 43234.56, change: 2.4, icon: '₿' },
    { symbol: 'ETH', name: 'Ethereum', price: 2456.78, change: -1.2, icon: 'Ξ' },
    { symbol: 'ADA', name: 'Cardano', price: 0.45, change: 5.7, icon: '₳' },
    { symbol: 'DOT', name: 'Polkadot', price: 6.23, change: 3.1, icon: '●' }
  ];

  const portfolioStats = {
    totalValue: 125675.89,
    totalPnL: 8234.56,
    totalPnLPercent: 6.97,
    todayPnL: 1245.32,
    todayPnLPercent: 1.02
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      
      {/* Header Navigation */}
      <header className="bg-gray-800/50 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            
            {/* Logo & Navigation */}
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">CP</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">CryptoPredict</h1>
                  <p className="text-xs text-gray-400">AI-Powered Trading</p>
                </div>
              </div>
              
              {/* Navigation Menu */}
              <nav className="hidden md:flex space-x-6">
                <a href="#" className="text-blue-400 font-medium border-b-2 border-blue-400 pb-1">Dashboard</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Predictions</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Portfolio</a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">Analytics</a>
              </nav>
            </div>

            {/* Header Actions */}
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="hidden md:flex items-center space-x-2 bg-gray-700/50 rounded-lg px-3 py-2">
                <Search className="h-4 w-4 text-gray-400" />
                <input 
                  placeholder="Search cryptocurrencies..."
                  className="bg-transparent text-white text-sm w-48 outline-none placeholder-gray-400"
                />
              </div>
              
              {/* Notifications */}
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5 text-gray-400" />
                {notifications > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {notifications}
                  </span>
                )}
              </Button>
              
              {/* Settings */}
              <Button variant="ghost" size="sm">
                <Settings className="h-5 w-5 text-gray-400" />
              </Button>
              
              {/* User Profile */}
              <div className="flex items-center space-x-2 bg-gray-700/50 rounded-lg px-3 py-2">
                <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">U</span>
                </div>
                <div className="hidden md:block">
                  <p className="text-white text-sm font-medium">User</p>
                  <p className="text-gray-400 text-xs">Premium</p>
                </div>
              </div>
              
              {/* Mobile Menu */}
              <Button 
                variant="ghost" 
                size="sm" 
                className="md:hidden"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="h-5 w-5 text-gray-400" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          
          {/* Left Sidebar */}
          <div className="col-span-12 lg:col-span-3 space-y-6">
            
            {/* Portfolio Overview */}
            <Card className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-blue-500/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center gap-2">
                  <Wallet className="h-5 w-5" />
                  Portfolio
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-gray-400 text-sm">Total Value</p>
                  <p className="text-2xl font-bold text-white">
                    ${portfolioStats.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </p>
                </div>
                
                <div className="flex justify-between">
                  <div>
                    <p className="text-gray-400 text-xs">Total P&L</p>
                    <p className={`font-bold ${portfolioStats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {portfolioStats.totalPnL >= 0 ? '+' : ''}${portfolioStats.totalPnL.toLocaleString()}
                    </p>
                    <p className={`text-xs ${portfolioStats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {portfolioStats.totalPnL >= 0 ? '+' : ''}{portfolioStats.totalPnLPercent.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Today</p>
                    <p className={`font-bold ${portfolioStats.todayPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {portfolioStats.todayPnL >= 0 ? '+' : ''}${portfolioStats.todayPnL.toLocaleString()}
                    </p>
                    <p className={`text-xs ${portfolioStats.todayPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {portfolioStats.todayPnL >= 0 ? '+' : ''}{portfolioStats.todayPnLPercent.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Crypto List */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-white flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    Markets
                  </span>
                  <Button variant="ghost" size="sm">
                    <Filter className="h-4 w-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {cryptoList.map((crypto) => (
                  <div 
                    key={crypto.symbol}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedCrypto === crypto.symbol 
                        ? 'bg-blue-500/20 border border-blue-500' 
                        : 'bg-gray-700/30 hover:bg-gray-700/50'
                    }`}
                    onClick={() => setSelectedCrypto(crypto.symbol)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                          {crypto.icon}
                        </div>
                        <div>
                          <p className="font-medium text-white">{crypto.symbol}</p>
                          <p className="text-xs text-gray-400">{crypto.name}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-white">
                          ${crypto.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </p>
                        <div className={`flex items-center text-xs ${
                          crypto.change >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {crypto.change >= 0 ? 
                            <ArrowUpRight className="h-3 w-3 mr-1" /> : 
                            <ArrowDownRight className="h-3 w-3 mr-1" />
                          }
                          {crypto.change >= 0 ? '+' : ''}{crypto.change.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-white">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full bg-green-600 hover:bg-green-700 text-white">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Buy {selectedCrypto}
                </Button>
                <Button variant="outline" className="w-full border-red-500 text-red-400 hover:bg-red-500/10">
                  <TrendingDown className="h-4 w-4 mr-2" />
                  Sell {selectedCrypto}
                </Button>
                <Button variant="outline" className="w-full border-gray-600 text-gray-300">
                  <Star className="h-4 w-4 mr-2" />
                  Add to Watchlist
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="col-span-12 lg:col-span-9 space-y-6">
            
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Bitcoin Price */}
              <Card className="bg-gradient-to-br from-orange-500/10 to-yellow-500/10 border-orange-500/30 hover:shadow-lg hover:shadow-orange-500/20 transition-all duration-300">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Bitcoin className="h-6 w-6 text-orange-500" />
                    <Badge variant="outline" className="text-orange-400 border-orange-400">LIVE</Badge>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Bitcoin Price</p>
                    <p className="text-2xl font-bold text-white">$43,234.56</p>
                    <div className="flex items-center mt-1">
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-green-500 text-sm font-medium">+2.4%</span>
                      <span className="text-gray-400 text-xs ml-1">24h</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Prediction */}
              <Card className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-purple-500/30 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Brain className="h-6 w-6 text-purple-500" />
                    <Badge variant="outline" className="text-purple-400 border-purple-400">AI</Badge>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">24h Prediction</p>
                    <p className="text-2xl font-bold text-white">$44,120</p>
                    <div className="flex items-center mt-1">
                      <Target className="h-4 w-4 text-purple-500 mr-1" />
                      <span className="text-purple-400 text-sm font-medium">87.3% confident</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Market Cap */}
              <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30 hover:shadow-lg hover:shadow-green-500/20 transition-all duration-300">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <DollarSign className="h-6 w-6 text-green-500" />
                    <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Market Cap</p>
                    <p className="text-2xl font-bold text-white">$842.5B</p>
                    <div className="flex items-center mt-1">
                      <Globe className="h-4 w-4 text-green-500 mr-1" />
                      <span className="text-green-400 text-sm font-medium">Dominance: 52.1%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Volume */}
              <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Activity className="h-6 w-6 text-blue-500" />
                    <Button variant="ghost" size="sm"><MoreVertical className="h-4 w-4" /></Button>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">24h Volume</p>
                    <p className="text-2xl font-bold text-white">$28.5B</p>
                    <div className="flex items-center mt-1">
                      <Activity className="h-4 w-4 text-blue-500 mr-1" />
                      <span className="text-blue-400 text-sm font-medium">High activity</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Chart */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Price Analysis</h2>
                  <p className="text-gray-400">Real-time {selectedCrypto} price chart with AI predictions</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-green-400 border-green-400">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                    Live Data
                  </Badge>
                  <Button variant="outline" size="sm" className="border-gray-600">
                    <Settings className="h-4 w-4 mr-2" />
                    Chart Settings
                  </Button>
                </div>
              </div>
              
              <PriceChart className="w-full" />
            </div>

            {/* Additional Insights */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Market Insights */}
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Brain className="h-5 w-5 text-blue-400" />
                    AI Market Insights
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-start gap-3 p-3 bg-green-500/10 rounded-lg">
                      <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                      <div>
                        <p className="text-green-400 font-medium text-sm">Strong Bullish Signal</p>
                        <p className="text-gray-300 text-sm">Technical indicators suggest upward momentum with 85% confidence.</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start gap-3 p-3 bg-yellow-500/10 rounded-lg">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2"></div>
                      <div>
                        <p className="text-yellow-400 font-medium text-sm">Resistance Level Alert</p>
                        <p className="text-gray-300 text-sm">Approaching key resistance at $45,200. Monitor for breakout.</p>
                      </div>
                    </div>
                    
                    <div className="flex items-start gap-3 p-3 bg-blue-500/10 rounded-lg">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
                      <div>
                        <p className="text-blue-400 font-medium text-sm">Volume Analysis</p>
                        <p className="text-gray-300 text-sm">Above-average trading volume indicates strong market interest.</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Clock className="h-5 w-5 text-purple-400" />
                    Recent Activity
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
                          <TrendingUp className="h-4 w-4 text-green-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium">Price Alert Triggered</p>
                          <p className="text-gray-400 text-sm">BTC reached $43,000</p>
                        </div>
                      </div>
                      <span className="text-gray-400 text-xs">2m ago</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center">
                          <Brain className="h-4 w-4 text-purple-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium">New AI Prediction</p>
                          <p className="text-gray-400 text-sm">24h forecast updated</p>
                        </div>
                      </div>
                      <span className="text-gray-400 text-xs">5m ago</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center">
                          <Activity className="h-4 w-4 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium">Volume Spike Detected</p>
                          <p className="text-gray-400 text-sm">+25% above average</p>
                        </div>
                      </div>
                      <span className="text-gray-400 text-xs">12m ago</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
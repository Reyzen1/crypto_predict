// File: frontend/app/page.tsx
// Complete Public Dashboard - Real API Integration

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

// Import components and services
import { Header } from '@/components/layout/Header';
import { PriceChart } from '@/components/charts/PriceChart';
import { DemoInfoCard } from '@/components/auth/DemoLogin';
import { useAuthStatus } from '@/contexts/AuthContext';
import { apiService, useApiStatus, wsService, type CryptoSummary, type DashboardSummary } from '@/services/api';
import { useToast } from '@/components/ToastProvider';
import { getCryptoIcon, getCryptoColor, handleApiError } from '@/lib/utils';

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
  BarChart3,
  PieChart,
  Sparkles,
  Bot,
  Shield,
  Heart,
  Gift,
  RefreshCw,
  WifiOff,
  AlertTriangle
} from "lucide-react";

// =====================================
// TYPE DEFINITIONS
// =====================================

interface MarketStats {
  totalMarketCap: number;
  totalVolume: number;
  btcDominance: number;
  fearGreedIndex: number;
  activeCoins: number;
}

interface ChartDataPoint {
  timestamp: string;
  price: number;
  volume?: number;
  prediction?: number;
}

// =====================================
// UTILITY FUNCTIONS
// =====================================

const formatPrice = (price: number): string => {
  if (price >= 1000) {
    return `$${(price / 1000).toFixed(1)}K`;
  }
  return `$${price.toFixed(2)}`;
};

const formatVolume = (volume: number): string => {
  if (volume >= 1000000000) {
    return `$${(volume / 1000000000).toFixed(1)}B`;
  }
  if (volume >= 1000000) {
    return `$${(volume / 1000000).toFixed(1)}M`;
  }
  return `$${(volume / 1000).toFixed(1)}K`;
};

const formatMarketCap = (cap: number): string => {
  if (cap >= 1000000000000) {
    return `$${(cap / 1000000000000).toFixed(2)}T`;
  }
  if (cap >= 1000000000) {
    return `$${(cap / 1000000000).toFixed(1)}B`;
  }
  return `$${(cap / 1000000).toFixed(1)}M`;
};

const getInitialDays = (timeframe: string): number => {
  switch (timeframe) {
    case '1h': return 1;
    case '4h': return 2;
    case '1d': return 7;  
    case '1w': return 30;
    case '1m': return 30;
    case '1y': return 30;
    default: return 7;
  }
};

// =====================================
// MAIN COMPONENT
// =====================================

export default function CompleteDashboard() {
  // State management
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [timeframe, setTimeframe] = useState('1d');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStats>({
    totalMarketCap: 0,
    totalVolume: 0,
    btcDominance: 0,
    fearGreedIndex: 50,
    activeCoins: 0
  });
  const [error, setError] = useState<string | null>(null);

  // Hooks
  const { isAuthenticated } = useAuthStatus();
  const { isOnline } = useApiStatus();
  const toast = useToast();

  // =====================================
  // DATA FETCHING FUNCTIONS
  // =====================================

  const fetchDashboardData = useCallback(async () => {
    try {
      setError(null);
      const symbols = ['BTC', 'ETH', 'ADA', 'DOT'];
      const data = await apiService.getDashboardSummary(symbols);
      
      setDashboardData(data);
      
      // Calculate market stats from the data
      const totalVolume = data.cryptocurrencies.reduce((sum, crypto) => sum + (crypto.volume_24h || 0), 0);
      const totalMarketCap = data.cryptocurrencies.reduce((sum, crypto) => sum + (crypto.market_cap || 0), 0);
      
      setMarketStats({
        totalMarketCap,
        totalVolume,
        btcDominance: 48.3, // Could be calculated from data
        fearGreedIndex: data.market_overview.average_confidence || 50,
        activeCoins: data.cryptocurrencies.length
      });

    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      toast.error('Failed to load dashboard data', errorMessage);
      console.error('Dashboard data fetch error:', err);
    }
  }, []);


  const fetchChartData = useCallback(async (symbol: string, daysHistory: number = 30) => {
    try {
      const cryptoDetails = await apiService.getCryptoDetails(symbol, daysHistory);handleTimeframeChange 
      const chartPoints: ChartDataPoint[] = cryptoDetails.price_history.map(point => ({
        timestamp: point.timestamp,
        price: point.price,
        volume: point.volume,
        prediction: cryptoDetails.predicted_price // Add prediction line
      }));
      
      setChartData(chartPoints);
    } catch (err) {
      console.error('Chart data fetch error:', err);
      // Don't show error toast for chart data, as dashboard might still work
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchDashboardData(),
        fetchChartData(selectedCrypto)
      ]);
      toast.success('Data refreshed successfully');
    } catch (err) {
      toast.error('Failed to refresh data');
    } finally {
      setIsRefreshing(false);
    }
  }, [fetchDashboardData, fetchChartData, selectedCrypto, isRefreshing]);

  // =====================================
  // EFFECTS
  // =====================================

  // Initial data load
  useEffect(() => {
    const initializeData = async () => {
      setIsLoading(true);
      try {
        if (isOnline) {
          const initialDays = getInitialDays(timeframe);

          await Promise.all([
            fetchDashboardData(),
            fetchChartData(selectedCrypto, initialDays)
          ]);
        } else {
          setError('Backend service is not available');
          toast.error('Backend offline', 'Using mock data for demo purposes');
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeData();
  }, [fetchDashboardData, fetchChartData, selectedCrypto, isOnline]);

  // Update chart when crypto selection changes
  useEffect(() => {
    if (!isLoading && selectedCrypto) {
      fetchChartData(selectedCrypto);
    }
  }, [selectedCrypto, fetchChartData, isLoading]);

  // WebSocket connection for real-time updates (only when authenticated)
  useEffect(() => {
    if (isOnline && isAuthenticated) {
      wsService.connect();

      const unsubscribe = wsService.subscribe('price_update', (data) => {
        // Update dashboard data with real-time prices
        setDashboardData(prev => {
          if (!prev) return prev;
          
          return {
            ...prev,
            cryptocurrencies: prev.cryptocurrencies.map(crypto => 
              crypto.symbol === data.symbol 
                ? { ...crypto, current_price: data.price, last_updated: data.timestamp }
                : crypto
            )
          };
        });
      });

      return () => {
        unsubscribe();
        wsService.disconnect();
      };
    }
  }, [isOnline, isAuthenticated]);

  // Handle timeframe change
  const handleTimeframeChange = useCallback((newTimeframe: string) => {
    setTimeframe(newTimeframe);
    const days = newTimeframe === '1h' ? 1 : 
                 newTimeframe === '4h' ? 4 : 
                 newTimeframe === '1d' ? 7 : 
                 newTimeframe === '1w' ? 30 : 
                 newTimeframe === '1m' ? 90 : 365;
    if (selectedCrypto) {
        fetchChartData(selectedCrypto, days);
    }
  }, [selectedCrypto, fetchChartData]);

  // =====================================
  // LOADING STATE
  // =====================================

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            <RefreshCw className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-spin" />
            <h2 className="text-xl text-white mb-2">Loading Dashboard</h2>
            <p className="text-gray-400">Fetching real-time cryptocurrency data...</p>
          </div>
        </main>
      </div>
    );
  }

  // =====================================
  // ERROR STATE
  // =====================================

  if (error && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center py-12">
            {isOnline ? (
              <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            ) : (
              <WifiOff className="w-12 h-12 text-red-400 mx-auto mb-4" />
            )}
            <h2 className="text-xl text-white mb-2">Unable to Load Data</h2>
            <p className="text-gray-400 mb-6">{error}</p>
            <Button onClick={handleRefresh} disabled={isRefreshing} className="btn-crypto-primary">
              {isRefreshing ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Try Again
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <Header />
      
      {/* Offline Banner */}
      {!isOnline && (
        <div className="bg-red-600/10 border-b border-red-600/20 p-3 text-center">
          <div className="flex items-center justify-center space-x-2 text-red-400">
            <WifiOff className="w-4 h-4" />
            <span className="text-sm">Backend service offline - Some features may be limited</span>
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section with Market Overview */}
        <div className="mb-8">
          {/* Demo Login Info */}
          <DemoInfoCard />
          
          <div className="text-center mb-6">
            <div className="flex items-center justify-center space-x-4 mb-2">
              <h1 className="text-4xl font-bold text-white">
                AI-Powered Crypto Analysis
              </h1>
              <Button
                onClick={handleRefresh}
                disabled={isRefreshing}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white"
              >
                <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
            <p className="text-gray-400 text-lg">
              Real-time predictions, technical analysis, and market insights - completely free
            </p>
            {dashboardData && (
              <p className="text-sm text-gray-500 mt-2">
                Last updated: {new Date(dashboardData.timestamp).toLocaleTimeString()}
              </p>
            )}
          </div>
          
          {/* Market Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-4 text-center">
                <Globe className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">Market Cap</p>
                <p className="text-white font-semibold">{formatMarketCap(marketStats.totalMarketCap)}</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-4 text-center">
                <BarChart3 className="w-6 h-6 text-green-400 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">24h Volume</p>
                <p className="text-white font-semibold">{formatVolume(marketStats.totalVolume)}</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-4 text-center">
                <Bitcoin className="w-6 h-6 text-orange-400 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">BTC Dominance</p>
                <p className="text-white font-semibold">{marketStats.btcDominance}%</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-4 text-center">
                <Activity className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">AI Confidence</p>
                <p className="text-white font-semibold">{marketStats.fearGreedIndex.toFixed(0)}</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-4 text-center">
                <Star className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">Tracked Coins</p>
                <p className="text-white font-semibold">{marketStats.activeCoins}</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Price Chart */}
          <div className="lg:col-span-2">
            <PriceChart
              symbol={selectedCrypto}
              data={chartData}
              isLoading={isLoading}
              showPrediction={true}
              onTimeframeChange={handleTimeframeChange}
              onRefresh={() => fetchChartData(selectedCrypto)}
              height={500}
            />
          </div>
          
          {/* Right Column - Crypto Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">Top Cryptocurrencies</h2>
              {dashboardData && (
                <Badge variant="secondary" className="bg-blue-500/10 text-blue-400 text-xs">
                  {dashboardData.market_overview.market_sentiment}
                </Badge>
              )}
            </div>
            
            {dashboardData?.cryptocurrencies.map((crypto) => (
              <Card 
                key={crypto.symbol}
                className={`bg-gray-800 border-gray-700 cursor-pointer transition-all duration-200 hover:bg-gray-750 ${
                  selectedCrypto === crypto.symbol ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedCrypto(crypto.symbol)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-full bg-gradient-to-r ${getCryptoColor(crypto.symbol)} flex items-center justify-center text-white font-bold`}>
                        {getCryptoIcon(crypto.symbol)}
                      </div>
                      <div>
                        <p className="font-semibold text-white">{crypto.name}</p>
                        <p className="text-gray-400 text-sm">{crypto.symbol}</p>
                      </div>
                    </div>
                    {selectedCrypto === crypto.symbol && (
                      <Eye className="w-5 h-5 text-blue-400" />
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Price</span>
                      <span className="font-semibold text-white">${crypto.current_price.toLocaleString()}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">24h Change</span>
                      <span className={`font-semibold flex items-center ${
                        crypto.price_change_24h_percent >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {crypto.price_change_24h_percent >= 0 ? (
                          <TrendingUp className="w-4 h-4 mr-1" />
                        ) : (
                          <TrendingDown className="w-4 h-4 mr-1" />
                        )}
                        {crypto.price_change_24h_percent.toFixed(2)}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Market Cap</span>
                      <span className="font-semibold text-white">{formatMarketCap(crypto.market_cap)}</span>
                    </div>
                  </div>
                  
                  {/* AI Prediction */}
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Brain className="w-4 h-4 text-blue-400" />
                        <span className="text-gray-400 text-sm">AI Prediction</span>
                      </div>
                      <Badge variant="secondary" className="bg-blue-500/10 text-blue-400 text-xs">
                        {crypto.confidence}% confidence
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">24h target</span>
                      <span className="font-semibold text-blue-400">${crypto.predicted_price.toLocaleString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
        
        {/* Features Section */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold text-white text-center mb-8">
            Why Choose CryptoPredict?
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-gray-800 border-gray-700 text-center">
              <CardContent className="p-6">
                <Brain className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">AI-Powered Analysis</h3>
                <p className="text-gray-400">
                  Advanced LSTM neural networks analyze market patterns to provide accurate predictions
                </p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700 text-center">
              <CardContent className="p-6">
                <Zap className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Real-Time Data</h3>
                <p className="text-gray-400">
                  Live market data from multiple exchanges with instant updates and notifications
                </p>
              </CardContent>
            </Card>
            
            <Card className="bg-gray-800 border-gray-700 text-center">
              <CardContent className="p-6">
                <Gift className="w-12 h-12 text-green-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Completely Free</h3>
                <p className="text-gray-400">
                  All features are 100% free. No hidden fees, no premium plans, just pure value
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
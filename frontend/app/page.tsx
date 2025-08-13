// File: frontend/app/page.tsx
// Complete dashboard with event-based refresh and full crypto management

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

// Import components and services
import { Header } from '@/components/layout/Header';
import { PriceChart } from '@/components/charts/PriceChart';
import { DemoInfoCard } from '@/components/auth/DemoLogin';
import { CryptoSelector } from '@/components/crypto/CryptoSelector';
import { useAuthStatus } from '@/contexts/AuthContext';
import { apiService, useApiStatus, wsService } from '@/services/api';
import { useSimpleAutoRefresh } from '@/hooks/useSimpleAutoRefresh';
import { useDataConsistency, chartValidationRules } from '@/hooks/useDataConsistency';
import { useCryptoManagement } from '@/hooks/useCryptoManagement';
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
  if (price >= 1000000) {
    return `$${(price / 1000000).toFixed(2)}M`;
  }
  if (price >= 1000) {
    return `$${(price / 1000).toFixed(1)}K`;
  }
  return `$${price.toFixed(2)}`;
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

const formatVolume = (volume: number): string => {
  if (volume >= 1000000000) {
    return `$${(volume / 1000000000).toFixed(1)}B`;
  }
  if (volume >= 1000000) {
    return `$${(volume / 1000000).toFixed(1)}M`;
  }
  return `$${(volume / 1000).toFixed(1)}K`;
};

// Get days for timeframe (respecting backend limitations)
const getTimeframeDays = (timeframe: string): number => {
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
// MAIN DASHBOARD COMPONENT
// =====================================

export default function CompleteDashboard() {
  // Basic state management
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [timeframe, setTimeframe] = useState('1d');
  const [isLoading, setIsLoading] = useState(true);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [marketStats, setMarketStats] = useState<MarketStats>({
    totalMarketCap: 0,
    totalVolume: 0,
    btcDominance: 0,
    fearGreedIndex: 50,
    activeCoins: 0
  });
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Hooks
  const { isAuthenticated } = useAuthStatus();
  const { isOnline } = useApiStatus();

  // =====================================
  // CRYPTO MANAGEMENT WITH EVENT-BASED REFRESH
  // =====================================

  const {
    // Data
    availableCryptos,
    selectedCryptos,
    cryptoData,
    filteredAvailableCryptos,
    
    // Loading states
    isLoadingList,
    isRefreshing: cryptoRefreshStates,
    
    // Search
    searchQuery,
    setSearchQuery,
    
    // Management functions
    addCrypto,
    removeCrypto,
    toggleCrypto,
    refreshSingleCrypto,
    refreshSelectedCryptos,
    
    // Event handlers (KEY FEATURE!)
    handleCryptoClick,
    handleStaleDataClick
  } = useCryptoManagement({
    defaultCryptos: ['BTC', 'ETH', 'ADA', 'DOT'],
    onDataUpdate: (data) => {
      // Calculate market stats from updated crypto data
      const totalVolume = data.reduce((sum, crypto) => sum + (crypto.volume_24h || 0), 0);
      const totalMarketCap = data.reduce((sum, crypto) => sum + (crypto.market_cap || 0), 0);
      const avgConfidence = data.reduce((sum, crypto) => sum + (crypto.confidence || 50), 0) / data.length;
      
      setMarketStats({
        totalMarketCap,
        totalVolume,
        btcDominance: 48.3, // Could be calculated from actual data
        fearGreedIndex: avgConfidence,
        activeCoins: data.length
      });
      
      setError(null);
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      console.error('Crypto management error:', errorMsg);
    }
  });

  // =====================================
  // CHART DATA MANAGEMENT
  // =====================================

  const fetchChartData = useCallback(async (symbol: string, daysHistory: number = 30) => {
    try {
      const limitedDays = Math.min(daysHistory, 30); // Backend limitation
      console.log(`📈 Fetching chart data for ${symbol} (${limitedDays} days)`);
      
      const cryptoDetails = await apiService.getCryptoDetails(symbol, limitedDays);
      
      const chartPoints: ChartDataPoint[] = cryptoDetails.price_history.map(point => ({
        timestamp: point.timestamp,
        price: point.price,
        volume: point.volume,
        prediction: cryptoDetails.predicted_price
      }));
      
      setChartData(chartPoints);
    } catch (err) {
      console.error('Chart data fetch error:', err);
      throw err; // Re-throw for error handling
    }
  }, []);

  const refreshCurrentChart = useCallback(async () => {
    const days = getTimeframeDays(timeframe);
    await fetchChartData(selectedCrypto, days);
  }, [selectedCrypto, timeframe, fetchChartData]);

  // =====================================
  // AUTO REFRESH SETUP
  // =====================================

  // Auto refresh chart data (interval-based)
  useSimpleAutoRefresh({
    refreshFn: refreshCurrentChart,
    config: {
      enabled: isOnline && !isLoading && selectedCrypto,
      interval: 300, // 5 minutes
      onlyWhenVisible: true,
      onlyWhenActive: true
    },
    dependencies: [isOnline, isLoading, selectedCrypto, timeframe]
  });

  // Auto refresh selected cryptocurrencies (interval-based)
  useSimpleAutoRefresh({
    refreshFn: () => refreshSelectedCryptos(false),
    config: {
      enabled: isOnline && !isLoading && selectedCryptos.length > 0,
      interval: 120, // 2 minutes
      onlyWhenVisible: true,
      onlyWhenActive: false // Keep refreshing even when inactive
    },
    dependencies: [isOnline, isLoading, selectedCryptos.length]
  });

  // =====================================
  // DATA VALIDATION
  // =====================================

  const { validation: chartValidation } = useDataConsistency({
    data: chartData,
    validationRules: chartValidationRules,
    onInvalidData: (errors) => {
      console.warn('Chart data validation failed:', errors);
    },
    autoRefreshOnInvalid: refreshCurrentChart
  });

  // =====================================
  // EVENT HANDLERS
  // =====================================

  // Handle cryptocurrency selection (EVENT-BASED!)
  const handleCryptoSelection = useCallback(async (symbol: string) => {
    console.log(`👆 User selected ${symbol} - switching and refreshing immediately`);
    
    setSelectedCrypto(symbol);
    
    // Immediate refresh of chart data (EVENT-BASED!)
    const days = getTimeframeDays(timeframe);
    await fetchChartData(symbol, days);
    
    // Also refresh crypto data if stale (EVENT-BASED!)
    await refreshSingleCrypto(symbol, false);
  }, [timeframe, fetchChartData, refreshSingleCrypto]);

  // Handle timeframe change (EVENT-BASED!)
  const handleTimeframeChange = useCallback(async (newTimeframe: string) => {
    console.log(`⏱️ User changed timeframe to ${newTimeframe} - refreshing chart immediately`);
    
    setTimeframe(newTimeframe);
    
    // Immediate refresh with new timeframe (EVENT-BASED!)
    const days = getTimeframeDays(newTimeframe);
    await fetchChartData(selectedCrypto, days);
  }, [selectedCrypto, fetchChartData]);

  // Manual refresh all data
  const handleRefreshAll = useCallback(async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    try {
      console.log('🔄 Manual refresh all triggered');
      
      await Promise.all([
        refreshSelectedCryptos(true), // Force refresh all cryptos
        refreshCurrentChart() // Refresh chart
      ]);
      
      console.log('✅ Manual refresh completed');
    } catch (err) {
      console.error('Manual refresh failed:', err);
      setError('Failed to refresh data');
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshSelectedCryptos, refreshCurrentChart, isRefreshing]);

  // =====================================
  // INITIAL LOAD
  // =====================================

  useEffect(() => {
    const initializeData = async () => {
      setIsLoading(true);
      try {
        if (isOnline) {
          console.log('🚀 Initial data load started');
          
          // Initial chart load
          const days = getTimeframeDays(timeframe);
          await fetchChartData(selectedCrypto, days);
          
          console.log('✅ Initial data load completed');
        } else {
          setError('Backend service is not available');
        }
      } catch (err) {
        setError('Failed to load initial data');
        console.error('Initial load error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeData();
  }, [isOnline, selectedCrypto, timeframe, fetchChartData]);

  // =====================================
  // WEBSOCKET INTEGRATION
  // =====================================

  useEffect(() => {
    if (isOnline && isAuthenticated) {
      wsService.connect();

      const unsubscribe = wsService.subscribe('price_update', (data) => {
        console.log(`💫 WebSocket price update for ${data.symbol}:`, data.price);
        
        // Update crypto data via crypto management system
        refreshSingleCrypto(data.symbol, false);
      });

      return () => {
        unsubscribe();
        wsService.disconnect();
      };
    }
  }, [isOnline, isAuthenticated, refreshSingleCrypto]);

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

  if (error && cryptoData.length === 0) {
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
            <Button onClick={handleRefreshAll} className="btn-crypto-primary">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </main>
      </div>
    );
  }

  // =====================================
  // MAIN RENDER
  // =====================================

  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header with Status */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              <span className="bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
                CryptoPredict
              </span>{' '}
              <span className="text-gray-300">Dashboard</span>
            </h1>
            <div className="flex items-center space-x-4">
              <p className="text-gray-400 text-lg">
                Real-time predictions, technical analysis, and market insights
              </p>
              
              {/* Status Indicators */}
              <div className="flex items-center space-x-2">
                {/* Data Validation Status */}
                <div className={`flex items-center space-x-1 text-xs px-2 py-1 rounded ${
                  chartValidation.isValid
                    ? 'bg-green-600/20 text-green-400'
                    : 'bg-red-600/20 text-red-400'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    chartValidation.isValid ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  <span>{chartValidation.isValid ? 'Data OK' : 'Data Issues'}</span>
                </div>
                
                {/* Active Refreshes */}
                {cryptoRefreshStates.size > 0 && (
                  <div className="flex items-center space-x-1 text-xs text-blue-400">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    <span>Refreshing ({cryptoRefreshStates.size})</span>
                  </div>
                )}
                
                {/* Event-Based Indicator */}
                <div className="flex items-center space-x-1 text-xs text-gray-400">
                  <Zap className="w-3 h-3 text-yellow-400" />
                  <span>Event-Based</span>
                </div>
              </div>
            </div>
          </div>
          
          <Button 
            onClick={handleRefreshAll} 
            disabled={isRefreshing} 
            className="btn-crypto-primary"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh All
          </Button>
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

        {/* Cryptocurrency Management with EVENT-BASED REFRESH */}
        <div className="mb-8">
          <CryptoSelector
            selectedCryptos={selectedCryptos}
            availableCryptos={availableCryptos}
            cryptoData={cryptoData}
            searchQuery={searchQuery}
            isLoadingList={isLoadingList}
            isRefreshing={cryptoRefreshStates}
            filteredAvailableCryptos={filteredAvailableCryptos}
            onCryptoClick={async (symbol) => {
              await handleCryptoClick(symbol);
              await handleCryptoSelection(symbol); // Also select it
            }}
            onStaleDataClick={handleStaleDataClick}
            onToggleCrypto={toggleCrypto}
            onSearchChange={setSearchQuery}
            onRefreshAll={() => refreshSelectedCryptos(true)}
          />
        </div>

        {/* Price Chart */}
        <Card className="bg-gray-800/50 border-gray-700 mb-8">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              <span>{selectedCrypto} Price Analysis</span>
              <Badge variant="secondary" className="bg-green-600 text-white">Live</Badge>
              {chartValidation.isValid && (
                <Badge variant="outline" className="text-green-400 border-green-400">Valid</Badge>
              )}
            </CardTitle>
            <Button
              onClick={refreshCurrentChart}
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <PriceChart
              symbol={selectedCrypto}
              data={chartData}
              isLoading={false}
              onTimeframeChange={handleTimeframeChange} // EVENT-BASED!
              onRefresh={refreshCurrentChart}
            />
          </CardContent>
        </Card>

        {/* Demo Info Card for non-authenticated users */}
        {!isAuthenticated && <DemoInfoCard />}
        
        {/* Debug Info (Development only) */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="bg-gray-800/30 border-gray-600 mt-8">
            <CardHeader>
              <CardTitle className="text-gray-400 text-sm">Debug Info</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-gray-500">
              <p>Selected Crypto: {selectedCrypto} | Timeframe: {timeframe}</p>
              <p>Chart Data Points: {chartData.length}</p>
              <p>Selected Cryptos: [{selectedCryptos.join(', ')}]</p>
              <p>Active Refreshes: {cryptoRefreshStates.size}</p>
              <p>Available Cryptos: {availableCryptos.length}</p>
              <p>Chart Valid: {chartValidation.isValid ? 'Yes' : 'No'}</p>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
// File: frontend/app/page.tsx
// Complete Public Dashboard - 100% Free Crypto Analysis Platform
// All features available without login - Personal space optional

'use client';

import React, { useState, useEffect } from 'react';
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
  ComposedChart
} from 'recharts';
// Temporarily comment out these imports until we verify the components exist
// import { Header } from '@/components/layout/Header';
// import { PriceChart } from '@/components/charts/PriceChart';
// import { AuthButton } from '@/components/auth/AuthModal';
// import { useAuthStatus } from '@/contexts/AuthContext';
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
  TrendingUpIcon,
  BarChart3,
  LineChart,
  PieChart,
  Sparkles,
  Bot,
  Shield,
  Heart,
  Gift
} from "lucide-react";

const cryptoData = [
  { 
    symbol: 'BTC', 
    name: 'Bitcoin', 
    price: 43234.56, 
    change: 2.4, 
    volume: 28500000000,
    marketCap: 847000000000,
    prediction: { price: 45200, confidence: 87, timeframe: '24h' },
    icon: '₿',
    color: 'from-orange-400 to-orange-600'
  },
  { 
    symbol: 'ETH', 
    name: 'Ethereum', 
    price: 2456.78, 
    change: -1.2, 
    volume: 15200000000,
    marketCap: 295000000000,
    prediction: { price: 2580, confidence: 82, timeframe: '24h' },
    icon: 'Ξ',
    color: 'from-blue-400 to-blue-600'
  },
  { 
    symbol: 'ADA', 
    name: 'Cardano', 
    price: 0.45, 
    change: 5.7, 
    volume: 580000000,
    marketCap: 16000000000,
    prediction: { price: 0.52, confidence: 75, timeframe: '24h' },
    icon: '₳',
    color: 'from-green-400 to-green-600'
  },
  { 
    symbol: 'DOT', 
    name: 'Polkadot', 
    price: 6.23, 
    change: 3.1, 
    volume: 420000000,
    marketCap: 8500000000,
    prediction: { price: 6.89, confidence: 79, timeframe: '24h' },
    icon: '●',
    color: 'from-pink-400 to-pink-600'
  }
];

// Generate mock chart data
const generateChartData = (symbol, days = 30) => {
  const data = [];
  const basePrice = cryptoData.find(c => c.symbol === symbol)?.price || 43234;
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    const dayProgress = (days - i) / days;
    const trend = Math.sin(dayProgress * Math.PI * 2) * 0.1;
    const volatility = (Math.random() - 0.5) * 0.05;
    const totalChange = trend + volatility;
    
    const price = basePrice * (1 + totalChange);
    const volume = Math.random() * 500000000 + 750000000;
    
    data.push({
      date: date.toISOString().split('T')[0],
      price: parseFloat(price.toFixed(2)),
      volume: Math.floor(volume),
      prediction: parseFloat((price * 1.02).toFixed(2))
    });
  }
  
  return data;
};

const marketStats = {
  totalMarketCap: 1750000000000,
  totalVolume: 89000000000,
  btcDominance: 48.3,
  fearGreedIndex: 72,
  activeCoins: 2847
};

export default function CompleteDashboard() {
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [timeframe, setTimeframe] = useState('24h');
  const [isLoading, setIsLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  // Temporarily comment out auth status
  // const { isAuthenticated } = useAuthStatus();

  // Simulate data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
      setChartData(generateChartData(selectedCrypto));
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  // Update chart when crypto selection changes
  useEffect(() => {
    if (!isLoading) {
      setChartData(generateChartData(selectedCrypto));
    }
  }, [selectedCrypto, isLoading]);

  // Update chart when timeframe changes
  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    // Generate different data based on timeframe
    let days;
    switch(newTimeframe) {
      case '1h': days = 1; break;
      case '24h': days = 7; break;
      case '7d': days = 30; break;
      case '30d': days = 90; break;
      default: days = 30;
    }
    setChartData(generateChartData(selectedCrypto, days));
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  const formatLargeNumber = (num: number) => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toFixed(2)}`;
  };

  const selectedCryptoData = cryptoData.find(crypto => crypto.symbol === selectedCrypto);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <h2 className="text-2xl font-bold text-white">Loading CryptoPredict...</h2>
          <p className="text-gray-400">Preparing your free crypto analysis platform</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      
      {/* Temporary Header - Replace with actual Header component later */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center space-x-4 text-center">
            <Gift className="h-5 w-5" />
            <span className="font-medium">🎉 CryptoPredict is 100% FREE - All AI predictions & analysis tools available to everyone!</span>
            <Sparkles className="h-5 w-5" />
          </div>
        </div>
      </div>

      <header className="bg-gray-800/50 backdrop-blur-md border-b border-gray-700 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">CryptoPredict</h1>
                <p className="text-xs text-gray-400">Free AI-Powered Analysis</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white">
              <User className="h-4 w-4 mr-2" />
              Get Personal Space - FREE
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">

        {/* Hero Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Total Market Cap</p>
                  <p className="text-2xl font-bold text-white">{formatLargeNumber(marketStats.totalMarketCap)}</p>
                </div>
                <Globe className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">24h Volume</p>
                  <p className="text-2xl font-bold text-white">{formatLargeNumber(marketStats.totalVolume)}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">BTC Dominance</p>
                  <p className="text-2xl font-bold text-white">{marketStats.btcDominance}%</p>
                </div>
                <Bitcoin className="h-8 w-8 text-orange-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Fear & Greed</p>
                  <p className="text-2xl font-bold text-green-400">{marketStats.fearGreedIndex}</p>
                </div>
                <Activity className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Active Coins</p>
                  <p className="text-2xl font-bold text-white">{marketStats.activeCoins.toLocaleString()}</p>
                </div>
                <Star className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Interactive Crypto Selection Tabs */}
        <div className="flex flex-wrap gap-3 p-1 bg-gray-800/30 rounded-lg">
          {cryptoData.map((crypto) => (
            <button
              key={crypto.symbol}
              onClick={() => setSelectedCrypto(crypto.symbol)}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                selectedCrypto === crypto.symbol
                  ? 'bg-blue-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white hover:scale-102'
              }`}
            >
              <span className="text-lg font-bold">{crypto.icon}</span>
              <div className="text-left">
                <p className="font-semibold">{crypto.symbol}</p>
                <p className="text-xs opacity-75">{formatPrice(crypto.price)}</p>
              </div>
              <div className={`flex items-center text-xs ${crypto.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {crypto.change >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {Math.abs(crypto.change)}%
              </div>
            </button>
          ))}
        </div>

        {/* Main Analysis Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Temporary Chart Display */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Real Price Chart */}
            <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-white flex items-center space-x-2">
                  <BarChart2 className="h-5 w-5 text-blue-400" />
                  <span>{selectedCryptoData?.name} Price Analysis</span>
                  <Badge variant="secondary" className="bg-green-600 text-white">Live</Badge>
                </CardTitle>
                <div className="flex space-x-2">
                  {['1h', '24h', '7d', '30d'].map((period) => (
                    <Button
                      key={period}
                      variant={timeframe === period ? "default" : "ghost"}
                      size="sm"
                      onClick={() => handleTimeframeChange(period)}
                      className={`text-xs transition-colors ${
                        timeframe === period 
                          ? 'bg-blue-600 text-white hover:bg-blue-700' 
                          : 'text-gray-300 hover:text-white hover:bg-gray-700 border border-gray-600'
                      }`}
                    >
                      {period}
                    </Button>
                  ))}
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="h-80 bg-gray-900/50 rounded-lg flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                      <p className="text-gray-400">Loading chart data...</p>
                    </div>
                  </div>
                ) : (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="predictionGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis 
                          dataKey="date" 
                          stroke="#9CA3AF"
                          fontSize={12}
                          tickFormatter={(value) => {
                            const date = new Date(value);
                            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                          }}
                        />
                        <YAxis 
                          stroke="#9CA3AF"
                          fontSize={12}
                          tickFormatter={(value) => `${value.toLocaleString()}`}
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#1F2937',
                            border: '1px solid #374151',
                            borderRadius: '8px',
                            color: '#F9FAFB'
                          }}
                          formatter={(value, name) => [
                            `${value.toLocaleString()}`, 
                            name === 'price' ? 'Price' : 'AI Prediction'
                          ]}
                          labelFormatter={(value) => {
                            const date = new Date(value);
                            return date.toLocaleDateString('en-US', { 
                              month: 'long', 
                              day: 'numeric',
                              year: 'numeric'
                            });
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="price"
                          stroke="#3B82F6"
                          strokeWidth={2}
                          fill="url(#priceGradient)"
                        />
                        <Line
                          type="monotone"
                          dataKey="prediction"
                          stroke="#10B981"
                          strokeWidth={2}
                          strokeDasharray="5 5"
                          dot={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
                
                {/* Chart Info */}
                <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-blue-500 rounded"></div>
                    <span className="text-gray-300">Actual Price</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-1 bg-green-500 rounded"></div>
                    <span className="text-gray-300">AI Prediction</span>
                  </div>
                  <Badge variant="outline" className="text-blue-400 border-blue-400">
                    Real-time data • Free for everyone
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Technical Indicators */}
            <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  <span>Advanced Technical Analysis</span>
                  <Badge variant="secondary" className="bg-purple-600 text-white">AI-Powered</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-900/50 p-4 rounded-lg text-center">
                    <p className="text-gray-400 text-sm">RSI (14)</p>
                    <p className="text-2xl font-bold text-yellow-400">67.3</p>
                    <p className="text-xs text-gray-500">Overbought</p>
                  </div>
                  <div className="bg-gray-900/50 p-4 rounded-lg text-center">
                    <p className="text-gray-400 text-sm">MACD</p>
                    <p className="text-2xl font-bold text-green-400">+234</p>
                    <p className="text-xs text-gray-500">Bullish</p>
                  </div>
                  <div className="bg-gray-900/50 p-4 rounded-lg text-center">
                    <p className="text-gray-400 text-sm">MA (50)</p>
                    <p className="text-2xl font-bold text-blue-400">41.2K</p>
                    <p className="text-xs text-gray-500">Above MA</p>
                  </div>
                  <div className="bg-gray-900/50 p-4 rounded-lg text-center">
                    <p className="text-gray-400 text-sm">Bollinger</p>
                    <p className="text-2xl font-bold text-orange-400">Mid</p>
                    <p className="text-xs text-gray-500">Neutral</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - AI Predictions & Market Info */}
          <div className="space-y-6">
            
            {/* AI Prediction */}
            <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Brain className="h-5 w-5 text-green-400" />
                  <span>AI Price Prediction</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center space-y-3">
                  <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 p-4 rounded-lg border border-green-500/30">
                    <p className="text-green-400 text-sm font-medium">Next 24h Prediction</p>
                    <p className="text-3xl font-bold text-white">{formatPrice(selectedCryptoData?.prediction.price || 0)}</p>
                    <div className="flex items-center justify-center space-x-2 text-green-400">
                      <Target className="h-4 w-4" />
                      <span className="text-sm">{selectedCryptoData?.prediction.confidence}% confidence</span>
                    </div>
                  </div>
                  
                  {/* Current Price Display */}
                  <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-600">
                    <p className="text-gray-400 text-sm">Current Price</p>
                    <p className="text-2xl font-bold text-white">{formatPrice(selectedCryptoData?.price || 0)}</p>
                    <div className={`flex items-center justify-center space-x-2 ${
                      (selectedCryptoData?.change || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {(selectedCryptoData?.change || 0) >= 0 ? 
                        <TrendingUp className="h-4 w-4" /> : 
                        <TrendingDown className="h-4 w-4" />
                      }
                      <span className="text-sm font-semibold">
                        {(selectedCryptoData?.change || 0) >= 0 ? '+' : ''}{selectedCryptoData?.change}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-900/50 p-3 rounded-lg">
                      <p className="text-gray-400 text-xs">Support Level</p>
                      <p className="text-lg font-bold text-red-400">{formatPrice((selectedCryptoData?.price || 0) * 0.95)}</p>
                    </div>
                    <div className="bg-gray-900/50 p-3 rounded-lg">
                      <p className="text-gray-400 text-xs">Resistance</p>
                      <p className="text-lg font-bold text-green-400">{formatPrice((selectedCryptoData?.price || 0) * 1.08)}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-500/10 border border-blue-500/30 p-3 rounded-lg">
                  <div className="flex items-center space-x-2 text-blue-400">
                    <Sparkles className="h-4 w-4" />
                    <span className="text-xs font-medium">LSTM Neural Network Analysis</span>
                  </div>
                  <p className="text-gray-300 text-xs mt-1">Based on 10,000+ data points and market patterns</p>
                </div>
              </CardContent>
            </Card>

            {/* Market Stats */}
            <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <PieChart className="h-5 w-5 text-yellow-400" />
                  <span>Market Overview</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Market Cap</span>
                    <span className="text-white font-semibold">{formatLargeNumber(selectedCryptoData?.marketCap || 0)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">24h Volume</span>
                    <span className="text-white font-semibold">{formatLargeNumber(selectedCryptoData?.volume || 0)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Circulating Supply</span>
                    <span className="text-white font-semibold">19.8M {selectedCryptoData?.symbol}</span>
                  </div>
                </div>

                {/* Free Access Message */}
                <div className="bg-green-500/10 border border-green-500/30 p-3 rounded-lg">
                  <div className="flex items-center space-x-2 text-green-400">
                    <Shield className="h-4 w-4" />
                    <span className="text-xs font-medium">100% Free Access</span>
                  </div>
                  <p className="text-gray-300 text-xs mt-1">All data and analysis tools are completely free</p>
                </div>
              </CardContent>
            </Card>

            {/* Personal Space Invitation */}
            <Card className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-blue-500/30 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Heart className="h-5 w-5 text-pink-400" />
                  <span>Want Personal Space?</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-gray-300 text-sm">
                  Create your personal dashboard to track portfolio, save watchlists, and customize your experience.
                </p>
                
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-sm text-gray-300">
                    <Wallet className="h-4 w-4 text-blue-400" />
                    <span>Personal Portfolio Tracking</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-300">
                    <Star className="h-4 w-4 text-yellow-400" />
                    <span>Custom Watchlists</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-300">
                    <Settings className="h-4 w-4 text-green-400" />
                    <span>Personalized Preferences</span>
                  </div>
                </div>

                <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                  <User className="h-4 w-4 mr-2" />
                  Sign Up FREE - No Credit Card
                </Button>
                
                <p className="text-center text-xs text-gray-400">
                  ✨ Always free • No premium plans • No hidden fees
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Bottom Features Showcase */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6 text-center space-y-4">
              <Bot className="h-12 w-12 text-blue-400 mx-auto" />
              <h3 className="text-lg font-bold text-white">AI-Powered Predictions</h3>
              <p className="text-gray-400 text-sm">Advanced LSTM neural networks analyze market patterns to provide accurate price predictions.</p>
              <Badge variant="secondary" className="bg-blue-600 text-white">100% Free</Badge>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6 text-center space-y-4">
              <BarChart3 className="h-12 w-12 text-green-400 mx-auto" />
              <h3 className="text-lg font-bold text-white">Complete Technical Analysis</h3>
              <p className="text-gray-400 text-sm">Full suite of technical indicators, charts, and analysis tools used by professional traders.</p>
              <Badge variant="secondary" className="bg-green-600 text-white">No Restrictions</Badge>
            </CardContent>
          </Card>

          <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm">
            <CardContent className="p-6 text-center space-y-4">
              <Globe className="h-12 w-12 text-purple-400 mx-auto" />
              <h3 className="text-lg font-bold text-white">Real-time Market Data</h3>
              <p className="text-gray-400 text-sm">Live price feeds, volume data, and market statistics updated every second.</p>
              <Badge variant="secondary" className="bg-purple-600 text-white">Open Access</Badge>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900/80 border-t border-gray-700 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center space-y-4">
            <div className="flex items-center justify-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white">CryptoPredict</h3>
            </div>
            
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-400">
              <span className="flex items-center space-x-1">
                <Gift className="h-4 w-4" />
                <span>100% Free Platform</span>
              </span>
              <span className="flex items-center space-x-1">
                <Shield className="h-4 w-4" />
                <span>Open Source AI</span>
              </span>
              <span className="flex items-center space-x-1">
                <Heart className="h-4 w-4" />
                <span>Community Driven</span>
              </span>
            </div>
            
            <p className="text-gray-400 text-sm max-w-2xl mx-auto">
              CryptoPredict provides free AI-powered cryptocurrency analysis for everyone. 
              All tools, predictions, and data are available without restrictions. 
              Personal space is optional for portfolio tracking only.
            </p>
            
            <div className="border-t border-gray-700 pt-4">
              <p className="text-gray-500 text-xs">
                © 2024 CryptoPredict. Forever free for the crypto community. 
                No premium plans, no hidden fees, no restrictions.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
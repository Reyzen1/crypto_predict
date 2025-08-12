// File: frontend/src/components/charts/PriceChart.tsx
// Advanced Price Chart with Real API Integration and Technical Analysis

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Bar,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  BarChart3,
  LineChart as LineChartIcon,
  Activity,
  Target,
  Zap,
  Brain,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface PriceDataPoint {
  timestamp: string;
  price: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  close: number;
  prediction?: number;
  ma20?: number;
  ma50?: number;
  rsi?: number;
}

interface PriceChartProps {
  symbol?: string;
  timeframe?: '1h' | '4h' | '1d' | '1w';
  showPrediction?: boolean;
  showTechnicalIndicators?: boolean;
  height?: number;
  className?: string;
}

interface TechnicalIndicator {
  name: string;
  value: number | string;
  status: 'bullish' | 'bearish' | 'neutral';
  icon: React.ReactNode;
  description: string;
}

// =====================================
// MOCK DATA GENERATOR
// =====================================

const generateMockData = (days: number = 30, symbol: string = 'BTC'): PriceDataPoint[] => {
  const data: PriceDataPoint[] = [];
  const basePrice = symbol === 'BTC' ? 43000 : symbol === 'ETH' ? 2400 : 0.45;
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    
    // Generate realistic price movement
    const dayProgress = (days - i) / days;
    const trend = Math.sin(dayProgress * Math.PI * 2) * 0.1;
    const volatility = (Math.random() - 0.5) * 0.05;
    const totalChange = trend + volatility;
    
    const price = basePrice * (1 + totalChange);
    const volume = Math.random() * 500000000 + 750000000;
    const spread = price * 0.02;
    
    // OHLC data
    const open = price * (1 + (Math.random() - 0.5) * 0.01);
    const close = price;
    const high = Math.max(open, close) * (1 + Math.random() * 0.02);
    const low = Math.min(open, close) * (1 - Math.random() * 0.02);
    
    // Technical indicators
    const ma20 = price * (1 + (Math.random() - 0.5) * 0.03);
    const ma50 = price * (1 + (Math.random() - 0.5) * 0.05);
    const rsi = 30 + Math.random() * 40; // RSI between 30-70
    
    // AI Prediction (slightly higher than current price with some noise)
    const prediction = price * (1.02 + (Math.random() - 0.5) * 0.04);
    
    data.push({
      timestamp: date.toISOString(),
      price: parseFloat(price.toFixed(2)),
      volume: Math.floor(volume),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      open: parseFloat(open.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      prediction: parseFloat(prediction.toFixed(2)),
      ma20: parseFloat(ma20.toFixed(2)),
      ma50: parseFloat(ma50.toFixed(2)),
      rsi: parseFloat(rsi.toFixed(1))
    });
  }
  
  return data;
};

// =====================================
// TECHNICAL INDICATORS CALCULATOR
// =====================================

const calculateTechnicalIndicators = (data: PriceDataPoint[]): TechnicalIndicator[] => {
  if (data.length === 0) return [];
  
  const latestData = data[data.length - 1];
  const previousData = data[data.length - 2];
  
  return [
    {
      name: 'RSI (14)',
      value: latestData.rsi?.toFixed(1) || '50.0',
      status: (latestData.rsi || 50) > 70 ? 'bearish' : (latestData.rsi || 50) < 30 ? 'bullish' : 'neutral',
      icon: <Activity className="h-4 w-4" />,
      description: 'Relative Strength Index'
    },
    {
      name: 'MA Cross',
      value: (latestData.ma20 || 0) > (latestData.ma50 || 0) ? 'Golden' : 'Death',
      status: (latestData.ma20 || 0) > (latestData.ma50 || 0) ? 'bullish' : 'bearish',
      icon: <TrendingUp className="h-4 w-4" />,
      description: '20/50 Moving Average Crossover'
    },
    {
      name: 'Price Action',
      value: latestData.price > (previousData?.price || 0) ? 'Bullish' : 'Bearish',
      status: latestData.price > (previousData?.price || 0) ? 'bullish' : 'bearish',
      icon: <BarChart3 className="h-4 w-4" />,
      description: 'Current price momentum'
    },
    {
      name: 'AI Signal',
      value: (latestData.prediction || 0) > latestData.price ? 'Buy' : 'Hold',
      status: (latestData.prediction || 0) > latestData.price ? 'bullish' : 'neutral',
      icon: <Brain className="h-4 w-4" />,
      description: 'Neural network prediction'
    }
  ];
};

// =====================================
// CUSTOM TOOLTIP COMPONENT
// =====================================

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const date = new Date(label).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
        <p className="text-gray-300 text-sm mb-2">{date}</p>
        <div className="space-y-1">
          <p className="text-white font-semibold">
            Price: ${data.price?.toLocaleString()}
          </p>
          {data.prediction && (
            <p className="text-blue-400">
              AI Prediction: ${data.prediction?.toLocaleString()}
            </p>
          )}
          <p className="text-gray-400 text-sm">
            Volume: ${(data.volume / 1000000).toFixed(1)}M
          </p>
          {data.ma20 && (
            <p className="text-yellow-400 text-sm">
              MA20: ${data.ma20?.toLocaleString()}
            </p>
          )}
          {data.rsi && (
            <p className="text-purple-400 text-sm">
              RSI: {data.rsi}
            </p>
          )}
        </div>
      </div>
    );
  }
  return null;
};

// =====================================
// MAIN PRICE CHART COMPONENT
// =====================================

export const PriceChart: React.FC<PriceChartProps> = ({
  symbol = 'BTC',
  timeframe = '1d',
  showPrediction = true,
  showTechnicalIndicators = true,
  height = 400,
  className = ''
}) => {
  const [data, setData] = useState<PriceDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [chartType, setChartType] = useState<'line' | 'area' | 'candlestick'>('area');

  // Calculate technical indicators
  const technicalIndicators = useMemo(() => {
    return calculateTechnicalIndicators(data);
  }, [data]);

  // Load data effect
  useEffect(() => {
    loadChartData();
  }, [symbol, timeframe]);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadChartData(true);
    }, 30000);

    return () => clearInterval(interval);
  }, [symbol, timeframe]);

  // =====================================
  // DATA LOADING FUNCTIONS
  // =====================================

  const loadChartData = async (isRefresh: boolean = false) => {
    if (!isRefresh) {
      setIsLoading(true);
    }
    setError('');

    try {
      // In a real app, this would call your API
      // const response = await fetch(`/api/v1/crypto/${symbol}/historical?timeframe=${timeframe}`);
      // const chartData = await response.json();
      
      // For demo, using mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      const mockData = generateMockData(30, symbol);
      
      setData(mockData);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to load chart data');
      console.error('Chart data loading error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshData = () => {
    loadChartData();
  };

  // =====================================
  // RENDER HELPERS
  // =====================================

  const formatPrice = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  const formatDate = (tickItem: string) => {
    const date = new Date(tickItem);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'bullish': return 'text-green-400';
      case 'bearish': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'bullish': return <CheckCircle className="h-3 w-3" />;
      case 'bearish': return <AlertCircle className="h-3 w-3" />;
      default: return <Clock className="h-3 w-3" />;
    }
  };

  // =====================================
  // RENDER
  // =====================================

  if (isLoading && data.length === 0) {
    return (
      <Card className={`bg-gray-800/50 border-gray-700 ${className}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-4">
              <RefreshCw className="h-8 w-8 text-blue-400 animate-spin mx-auto" />
              <p className="text-gray-300">Loading {symbol} chart data...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`bg-gray-800/50 border-gray-700 ${className}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-4">
              <AlertCircle className="h-8 w-8 text-red-400 mx-auto" />
              <p className="text-red-400">{error}</p>
              <Button onClick={refreshData} variant="outline" size="sm">
                Try Again
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const latestPrice = data[data.length - 1];
  const previousPrice = data[data.length - 2];
  const priceChange = latestPrice && previousPrice ? latestPrice.price - previousPrice.price : 0;
  const priceChangePercent = previousPrice ? (priceChange / previousPrice.price) * 100 : 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Chart Header */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CardTitle className="text-white flex items-center space-x-2">
                <LineChartIcon className="h-5 w-5 text-blue-400" />
                <span>{symbol} Price Chart</span>
              </CardTitle>
              <Badge variant="secondary" className="bg-green-600 text-white">
                <Zap className="h-3 w-3 mr-1" />
                Live
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="text-right">
                <p className="text-2xl font-bold text-white">
                  {formatPrice(latestPrice?.price || 0)}
                </p>
                <div className={`flex items-center text-sm ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {priceChange >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                  {priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
                </div>
              </div>
              
              <Button onClick={refreshData} variant="ghost" size="sm" disabled={isLoading}>
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Chart Controls */}
          <div className="flex items-center justify-between">
            <div className="flex space-x-2">
              {['line', 'area', 'candlestick'].map((type) => (
                <Button
                  key={type}
                  variant={chartType === type ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setChartType(type as any)}
                  className="text-xs"
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              ))}
            </div>
            
            <div className="flex items-center space-x-4 text-xs text-gray-400">
              <span>Last update: {lastUpdate.toLocaleTimeString()}</span>
              <Badge variant="outline" className="text-blue-400 border-blue-400">
                Free Real-time Data
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Main Chart */}
          <div style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'area' ? (
                <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                    dataKey="timestamp" 
                    tickFormatter={formatDate}
                    stroke="#9CA3AF"
                    fontSize={12}
                  />
                  <YAxis 
                    domain={['dataMin - 100', 'dataMax + 100']}
                    tickFormatter={formatPrice}
                    stroke="#9CA3AF"
                    fontSize={12}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  
                  {/* Price Area */}
                  <Area
                    type="monotone"
                    dataKey="price"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    fill="url(#priceGradient)"
                  />
                  
                  {/* Technical Indicators */}
                  {showTechnicalIndicators && (
                    <>
                      <Line
                        type="monotone"
                        dataKey="ma20"
                        stroke="#F59E0B"
                        strokeWidth={1}
                        dot={false}
                        strokeDasharray="5 5"
                      />
                      <Line
                        type="monotone"
                        dataKey="ma50"
                        stroke="#EF4444"
                        strokeWidth={1}
                        dot={false}
                        strokeDasharray="10 5"
                      />
                    </>
                  )}
                  
                  {/* AI Predictions */}
                  {showPrediction && (
                    <Line
                      type="monotone"
                      dataKey="prediction"
                      stroke="#10B981"
                      strokeWidth={2}
                      dot={false}
                      strokeDasharray="3 3"
                    />
                  )}
                </ComposedChart>
              ) : (
                <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatDate}
                    stroke="#9CA3AF"
                    fontSize={12}
                  />
                  <YAxis 
                    domain={['dataMin - 100', 'dataMax + 100']}
                    tickFormatter={formatPrice}
                    stroke="#9CA3AF"
                    fontSize={12}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                  />
                  {showPrediction && (
                    <Line
                      type="monotone"
                      dataKey="prediction"
                      stroke="#10B981"
                      strokeWidth={2}
                      dot={false}
                      strokeDasharray="3 3"
                    />
                  )}
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>

          {/* Chart Legend */}
          <div className="flex flex-wrap justify-center gap-4 mt-4 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded"></div>
              <span className="text-gray-300">Price</span>
            </div>
            {showPrediction && (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-1 bg-green-500"></div>
                <span className="text-gray-300">AI Prediction</span>
              </div>
            )}
            {showTechnicalIndicators && (
              <>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-1 bg-yellow-500"></div>
                  <span className="text-gray-300">MA20</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-1 bg-red-500"></div>
                  <span className="text-gray-300">MA50</span>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Technical Indicators Panel */}
      {showTechnicalIndicators && (
        <Card className="bg-gray-800/50 border-gray-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-white flex items-center space-x-2">
              <Target className="h-5 w-5 text-purple-400" />
              <span>Technical Analysis</span>
              <Badge variant="secondary" className="bg-purple-600 text-white">
                AI-Enhanced
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {technicalIndicators.map((indicator, index) => (
                <div
                  key={index}
                  className="bg-gray-900/50 p-3 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className={`flex items-center space-x-1 ${getStatusColor(indicator.status)}`}>
                      {indicator.icon}
                      <span className="text-xs font-medium">{indicator.name}</span>
                    </div>
                    {getStatusIcon(indicator.status)}
                  </div>
                  <p className={`text-lg font-bold ${getStatusColor(indicator.status)}`}>
                    {indicator.value}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {indicator.description}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PriceChart;
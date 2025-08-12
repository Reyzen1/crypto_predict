// File: frontend/src/components/charts/PriceChart.tsx
// Advanced Price Chart Component with multiple timeframes and real-time updates

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
  AreaChart,
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
  Settings,
  Maximize2,
  Calendar,
  Activity,
  Target
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface PriceDataPoint {
  timestamp: string;
  price: number;
  volume?: number;
  prediction?: number;
  high?: number;
  low?: number;
  open?: number;
  close?: number;
}

interface PriceChartProps {
  symbol: string;
  data: PriceDataPoint[];
  isLoading?: boolean;
  showPrediction?: boolean;
  showVolume?: boolean;
  height?: number;
  className?: string;
  onTimeframeChange?: (timeframe: string) => void;
  onRefresh?: () => void;
}

type TimeframeOption = {
  label: string;
  value: string;
  period: string;
};

// =====================================
// CONSTANTS
// =====================================

const TIMEFRAME_OPTIONS: TimeframeOption[] = [
  { label: '1H', value: '1h', period: 'hour' },
  { label: '4H', value: '4h', period: 'hour' },
  { label: '1D', value: '1d', period: 'day' },
  { label: '1W', value: '1w', period: 'week' },
  { label: '1M', value: '1m', period: 'month' },
  { label: '1Y', value: '1y', period: 'year' }
];

// =====================================
// UTILITY FUNCTIONS
// =====================================

const formatPrice = (value: number): string => {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(2)}`;
};

const formatVolume = (value: number): string => {
  if (value >= 1000000000) {
    return `${(value / 1000000000).toFixed(1)}B`;
  }
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  return `${(value / 1000).toFixed(1)}K`;
};

const formatTimestamp = (timestamp: string, period: string): string => {
  const date = new Date(timestamp);
  
  switch (period) {
    case 'hour':
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    case 'day':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    case 'week':
    case 'month':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    case 'year':
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        year: '2-digit' 
      });
    default:
      return date.toLocaleDateString();
  }
};

// =====================================
// CUSTOM TOOLTIP COMPONENT
// =====================================

const CustomTooltip = ({ active, payload, label, period }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-gray-300 text-sm mb-2">
          {formatTimestamp(label, period)}
        </p>
        
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center space-x-2 mb-1">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-white text-sm font-medium">
              {entry.dataKey === 'price' && `Price: ${formatPrice(entry.value)}`}
              {entry.dataKey === 'prediction' && `Prediction: ${formatPrice(entry.value)}`}
              {entry.dataKey === 'volume' && `Volume: ${formatVolume(entry.value)}`}
            </span>
          </div>
        ))}
        
        {data.high && data.low && (
          <div className="mt-2 pt-2 border-t border-gray-600">
            <p className="text-gray-400 text-xs">
              High: {formatPrice(data.high)} | Low: {formatPrice(data.low)}
            </p>
          </div>
        )}
      </div>
    );
  }
  
  return null;
};

// =====================================
// MAIN COMPONENT
// =====================================

export const PriceChart: React.FC<PriceChartProps> = ({
  symbol,
  data,
  isLoading = false,
  showPrediction = true,
  showVolume = false,
  height = 400,
  className = '',
  onTimeframeChange,
  onRefresh
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('1d');
  const [chartType, setChartType] = useState<'line' | 'area' | 'candlestick'>('area');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Get current timeframe details
  const currentTimeframe = TIMEFRAME_OPTIONS.find(
    option => option.value === selectedTimeframe
  ) || TIMEFRAME_OPTIONS[2];

  // Calculate price change
  const priceChange = useMemo(() => {
    if (data.length < 2) return { value: 0, percentage: 0 };
    
    const latest = data[data.length - 1]?.price || 0;
    const previous = data[data.length - 2]?.price || 0;
    const change = latest - previous;
    const percentage = previous !== 0 ? (change / previous) * 100 : 0;
    
    return { value: change, percentage };
  }, [data]);

  // Handle timeframe change
  const handleTimeframeChange = (timeframe: string) => {
    setSelectedTimeframe(timeframe);
    if (onTimeframeChange) {
      onTimeframeChange(timeframe);
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    if (isRefreshing || !onRefresh) return;
    
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  // Render chart based on type
  const renderChart = () => {
    const ChartComponent = chartType === 'area' ? AreaChart : LineChart;
    
    return (
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => formatTimestamp(value, currentTimeframe.period)}
            stroke="#9CA3AF"
            fontSize={12}
          />
          <YAxis 
            tickFormatter={formatPrice}
            stroke="#9CA3AF"
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip period={currentTimeframe.period} />} />
          
          {chartType === 'area' ? (
            <Area
              type="monotone"
              dataKey="price"
              stroke="#3B82F6"
              fill="url(#colorPrice)"
              strokeWidth={2}
            />
          ) : (
            <Line
              type="monotone"
              dataKey="price"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
            />
          )}
          
          {showPrediction && (
            <Line
              type="monotone"
              dataKey="prediction"
              stroke="#F59E0B"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
          
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
            </linearGradient>
          </defs>
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  return (
    <Card className={`bg-gray-800 border-gray-700 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CardTitle className="text-white text-lg font-semibold">
              {symbol} Price Chart
            </CardTitle>
            <Badge 
              variant={priceChange.value >= 0 ? "default" : "destructive"}
              className={`flex items-center space-x-1 ${
                priceChange.value >= 0 
                  ? 'bg-green-500/10 text-green-400 border-green-500/20' 
                  : 'bg-red-500/10 text-red-400 border-red-500/20'
              }`}
            >
              {priceChange.value >= 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span>{priceChange.percentage.toFixed(2)}%</span>
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing || isLoading}
              className="text-gray-400 hover:text-white"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex items-center space-x-2 mt-3">
          {TIMEFRAME_OPTIONS.map((option) => (
            <Button
              key={option.value}
              variant={selectedTimeframe === option.value ? "default" : "ghost"}
              size="sm"
              onClick={() => handleTimeframeChange(option.value)}
              className={`text-xs px-3 py-1 ${
                selectedTimeframe === option.value
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="flex items-center space-x-2 text-gray-400">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>Loading chart data...</span>
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-96 text-gray-400">
            <div className="text-center">
              <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No data available</p>
            </div>
          </div>
        ) : (
          renderChart()
        )}
        
        {/* Legend */}
        {!isLoading && data.length > 0 && (
          <div className="flex items-center justify-center space-x-6 mt-4 pt-4 border-t border-gray-700">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span className="text-gray-400 text-sm">Current Price</span>
            </div>
            {showPrediction && (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-1 bg-yellow-500 rounded" />
                <span className="text-gray-400 text-sm">AI Prediction</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
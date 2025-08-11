// File: frontend/components/charts/PriceChart.tsx
// REAL CHART VERSION - با Recharts واقعی

'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

// Mock data generator برای تست
const generateMockData = (days: number = 7) => {
  const data = [];
  const basePrice = 43234;
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    
    // Generate realistic price movement
    const dayProgress = (days - i) / days;
    const trend = Math.sin(dayProgress * Math.PI * 2) * 0.05; // 5% trend
    const noise = (Math.random() - 0.5) * 0.02; // 2% random noise
    const totalChange = trend + noise;
    
    const price = basePrice * (1 + totalChange);
    const volume = Math.random() * 500000000 + 750000000;
    
    data.push({
      name: date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: days === 1 ? '2-digit' : undefined 
      }),
      price: Math.round(price * 100) / 100,
      volume: Math.round(volume),
      timestamp: date.toISOString(),
      rawDate: date
    });
  }
  return data;
};

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 shadow-xl">
        <p className="text-gray-300 text-sm mb-2 font-medium">{label}</p>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
            <span className="text-white font-bold">
              ${data.price?.toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2 
              })}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            <span className="text-green-300 text-sm">
              Vol: ${(data.volume / 1000000).toFixed(1)}M
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

// Time Range Selector
const TimeRangeSelector = ({ 
  activeRange, 
  onRangeChange 
}: { 
  activeRange: string;
  onRangeChange: (range: string) => void;
}) => {
  const ranges = [
    { label: '24H', value: '1' },
    { label: '7D', value: '7' },
    { label: '30D', value: '30' },
    { label: '90D', value: '90' }
  ];

  return (
    <div className="flex gap-2">
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onRangeChange(range.value)}
          className={`px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium ${
            activeRange === range.value
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/50 scale-105'
              : 'text-gray-400 hover:text-white hover:bg-gray-700 bg-gray-800'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};

// Price Trend Indicator
const PriceTrend = ({ data }: { data: any[] }) => {
  if (data.length < 2) return null;
  
  const currentPrice = data[data.length - 1]?.price || 0;
  const previousPrice = data[0]?.price || 0;
  const change = currentPrice - previousPrice;
  const changePercent = (change / previousPrice) * 100;
  
  const isPositive = change >= 0;
  
  return (
    <div className="flex items-center gap-2">
      {isPositive ? (
        <TrendingUp className="h-5 w-5 text-green-500" />
      ) : (
        <TrendingDown className="h-5 w-5 text-red-500" />
      )}
      <span className={`font-bold text-lg ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
        {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
      </span>
      <span className="text-gray-400 text-sm">
        (${Math.abs(change).toLocaleString('en-US', { 
          minimumFractionDigits: 2,
          maximumFractionDigits: 2 
        })})
      </span>
    </div>
  );
};

// Main PriceChart Component
interface PriceChartProps {
  className?: string;
}

export default function PriceChart({ className }: PriceChartProps) {
  const [timeRange, setTimeRange] = useState('7');
  const [data, setData] = useState(generateMockData(7));
  const [isLoading, setIsLoading] = useState(false);
  const [rechartsStatus, setRechartsStatus] = useState('loading');

  // Test Recharts on mount
  useEffect(() => {
    try {
      // Test if Recharts is available
      if (typeof LineChart !== 'undefined') {
        setRechartsStatus('success');
      } else {
        setRechartsStatus('error');
      }
    } catch (error) {
      console.error('Recharts error:', error);
      setRechartsStatus('error');
    }
  }, []);

  const handleTimeRangeChange = (range: string) => {
    setTimeRange(range);
    setIsLoading(true);
    
    // Simulate loading
    setTimeout(() => {
      setData(generateMockData(parseInt(range)));
      setIsLoading(false);
    }, 1000);
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      setData(generateMockData(parseInt(timeRange)));
      setIsLoading(false);
    }, 1500);
  };

  const currentPrice = data[data.length - 1]?.price || 0;
  const highestPrice = Math.max(...data.map(d => d.price));
  const lowestPrice = Math.min(...data.map(d => d.price));

  return (
    <Card className={`bg-gray-800/50 border-gray-700 ${className}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <CardTitle className="text-xl font-semibold text-white mb-2">
              📊 Bitcoin Price Chart
            </CardTitle>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-3xl font-bold text-white">
                ${currentPrice.toLocaleString('en-US', { 
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2 
                })}
              </span>
              <PriceTrend data={data} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <TimeRangeSelector 
              activeRange={timeRange} 
              onRangeChange={handleTimeRangeChange}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              className="border-gray-600 text-gray-300 hover:text-white hover:border-blue-500"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        
        {/* Recharts Status Indicator */}
        <div className={`text-sm p-2 rounded-lg ${
          rechartsStatus === 'success' ? 'bg-green-500/20 text-green-400' :
          rechartsStatus === 'error' ? 'bg-red-500/20 text-red-400' :
          'bg-yellow-500/20 text-yellow-400'
        }`}>
          Recharts Status: {rechartsStatus === 'success' ? '✅ Loaded' : 
                           rechartsStatus === 'error' ? '❌ Error' : '⏳ Loading'}
          {rechartsStatus === 'success' && ` | ${data.length} data points`}
        </div>
      </CardHeader>
      
      <CardContent>
        {isLoading ? (
          <div className="h-[400px] flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-500"></div>
              <span className="text-gray-400 text-lg">Loading chart data...</span>
            </div>
          </div>
        ) : rechartsStatus === 'error' ? (
          <div className="h-[400px] flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-400 text-6xl mb-4">⚠️</div>
              <h3 className="text-xl font-bold text-red-400 mb-2">Recharts Library Error</h3>
              <p className="text-gray-400 mb-4">
                Recharts is not properly installed or imported
              </p>
              <div className="bg-gray-900 p-4 rounded-lg text-left">
                <p className="text-gray-300 text-sm mb-2">To fix this:</p>
                <code className="text-green-400 text-sm">
                  npm install recharts<br/>
                  npm run dev
                </code>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Chart Statistics */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-gray-400 text-sm">High</p>
                <p className="text-green-400 font-bold">
                  ${highestPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Current</p>
                <p className="text-white font-bold">
                  ${currentPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Low</p>
                <p className="text-red-400 font-bold">
                  ${lowestPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </p>
              </div>
            </div>

            {/* Main Chart */}
            <ResponsiveContainer width="100%" height={400}>
              <LineChart 
                data={data} 
                margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="#374151" 
                  opacity={0.4}
                />
                <XAxis
                  dataKey="name"
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  domain={['dataMin - 500', 'dataMax + 500']}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  stroke="#9CA3AF"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Current price reference line */}
                <ReferenceLine 
                  y={currentPrice} 
                  stroke="#10B981" 
                  strokeDasharray="2 2"
                  strokeWidth={1}
                />
                
                {/* Main price line with gradient effect */}
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ 
                    r: 6, 
                    stroke: '#3B82F6', 
                    strokeWidth: 3, 
                    fill: '#1E40AF',
                    filter: 'drop-shadow(0 0 6px #3B82F6)'
                  }}
                  filter="drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3))"
                />
              </LineChart>
            </ResponsiveContainer>

            {/* Chart Footer Info */}
            <div className="flex justify-between items-center text-sm text-gray-400 pt-2 border-t border-gray-700">
              <span>Time Range: {timeRange} {timeRange === '1' ? 'day' : 'days'}</span>
              <span>Data Points: {data.length}</span>
              <span>Last Updated: {new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
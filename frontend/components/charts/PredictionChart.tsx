// File: frontend/src/components/charts/PredictionChart.tsx
// Prediction Chart and Stats Cards Components

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Activity, 
  DollarSign,
  Bitcoin,
  Zap,
  Clock,
  Brain,
  RefreshCw
} from 'lucide-react';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface PredictionDataPoint {
  timestamp: string;
  actual_price?: number;
  predicted_price: number;
  confidence: number;
  lower_bound?: number;
  upper_bound?: number;
}

interface PredictionChartProps {
  data: PredictionDataPoint[];
  currentPrice?: number;
  isLoading?: boolean;
  onRefresh?: () => void;
}

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  isLoading?: boolean;
}

interface PredictionStatsProps {
  currentPrice: number;
  predictedPrice: number;
  confidence: number;
  change24h: number;
  volume24h: number;
  marketCap: number;
  lastUpdate: string;
  isLoading?: boolean;
  onRefresh?: () => void;
}

// =====================================
// PREDICTION CHART COMPONENT
// =====================================

const PredictionTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-gray-300 text-sm mb-2">
          {new Date(label).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
        <div className="space-y-1">
          {data.actual_price && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span className="text-white font-medium">
                Actual: ${data.actual_price?.toLocaleString('en-US', { 
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2 
                })}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
            <span className="text-purple-300 font-medium">
              Predicted: ${data.predicted_price?.toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2 
              })}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {data.confidence}% confidence
            </Badge>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export function PredictionChart({ 
  data, 
  currentPrice, 
  isLoading = false, 
  onRefresh 
}: PredictionChartProps) {
  // Calculate accuracy if we have actual vs predicted data
  const accuracy = React.useMemo(() => {
    const validPoints = data.filter(point => 
      point.actual_price && point.predicted_price
    );
    
    if (validPoints.length === 0) return null;
    
    const totalError = validPoints.reduce((sum, point) => {
      const error = Math.abs(point.actual_price! - point.predicted_price) / point.actual_price!;
      return sum + error;
    }, 0);
    
    return (1 - totalError / validPoints.length) * 100;
  }, [data]);

  const chartData = data.map(point => ({
    ...point,
    timestamp: new Date(point.timestamp).getTime(),
    formattedTime: new Date(point.timestamp).toLocaleDateString()
  }));

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold text-white mb-1">
              Price Predictions
            </CardTitle>
            <div className="flex items-center gap-4">
              {accuracy && (
                <Badge variant="outline" className="text-green-400 border-green-400">
                  {accuracy.toFixed(1)}% accuracy
                </Badge>
              )}
              <span className="text-gray-400 text-sm">
                AI-powered forecasting
              </span>
            </div>
          </div>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              className="border-gray-600 text-gray-300 hover:text-white"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {isLoading ? (
          <div className="h-[300px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="timestamp"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(timestamp) => {
                  const date = new Date(timestamp);
                  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }}
                stroke="#9CA3AF"
                fontSize={12}
              />
              <YAxis
                domain={['dataMin - 500', 'dataMax + 500']}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                stroke="#9CA3AF"
                fontSize={12}
              />
              <Tooltip content={<PredictionTooltip />} />
              
              {/* Current price reference line */}
              {currentPrice && (
                <ReferenceLine 
                  y={currentPrice} 
                  stroke="#10B981" 
                  strokeDasharray="2 2"
                  label={{ value: "Current", position: "insideTopRight" }}
                />
              )}
              
              {/* Confidence area */}
              {data.some(d => d.lower_bound && d.upper_bound) && (
                <Area
                  dataKey="upper_bound"
                  stroke="none"
                  fill="#A855F7"
                  fillOpacity={0.1}
                />
              )}
              
              {/* Actual price line */}
              <Line
                type="monotone"
                dataKey="actual_price"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, stroke: '#3B82F6', strokeWidth: 2, fill: '#1E40AF' }}
              />
              
              {/* Predicted price line */}
              <Line
                type="monotone"
                dataKey="predicted_price"
                stroke="#A855F7"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 4, stroke: '#A855F7', strokeWidth: 2, fill: '#7C3AED' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

// =====================================
// STATS CARD COMPONENT
// =====================================

export function StatsCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  trend = 'neutral',
  isLoading = false
}: StatsCardProps) {
  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      if (val >= 1000000000) return `$${(val / 1000000000).toFixed(2)}B`;
      if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
      if (val >= 1000) return `$${(val / 1000).toFixed(2)}K`;
      return `$${val.toFixed(2)}`;
    }
    return val;
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-green-500';
      case 'down': return 'text-red-500';
      default: return 'text-gray-400';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-3 w-3" />;
      case 'down': return <TrendingDown className="h-3 w-3" />;
      default: return null;
    }
  };

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="text-gray-400">
              {icon}
            </div>
            <span className="text-sm font-medium text-gray-300">
              {title}
            </span>
          </div>
        </div>
        
        <div className="mt-2">
          {isLoading ? (
            <div className="h-8 w-24 bg-gray-700 animate-pulse rounded"></div>
          ) : (
            <div className="text-2xl font-bold text-white">
              {formatValue(value)}
            </div>
          )}
          
          {change !== undefined && !isLoading && (
            <div className={`flex items-center space-x-1 mt-1 ${getTrendColor()}`}>
              {getTrendIcon()}
              <span className="text-sm font-medium">
                {change > 0 ? '+' : ''}{change.toFixed(2)}%
              </span>
              {changeLabel && (
                <span className="text-xs text-gray-500">
                  {changeLabel}
                </span>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// =====================================
// PREDICTION STATS COMPONENT
// =====================================

export function PredictionStats({
  currentPrice,
  predictedPrice,
  confidence,
  change24h,
  volume24h,
  marketCap,
  lastUpdate,
  isLoading = false,
  onRefresh
}: PredictionStatsProps) {
  const predictionChange = ((predictedPrice - currentPrice) / currentPrice) * 100;
  const predictionTrend = predictionChange >= 0 ? 'up' : 'down';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard
        title="Current Price"
        value={currentPrice}
        change={change24h}
        changeLabel="24h"
        icon={<Bitcoin className="h-4 w-4" />}
        trend={change24h >= 0 ? 'up' : 'down'}
        isLoading={isLoading}
      />
      
      <StatsCard
        title="Predicted Price"
        value={predictedPrice}
        change={predictionChange}
        changeLabel="vs current"
        icon={<Target className="h-4 w-4" />}
        trend={predictionTrend}
        isLoading={isLoading}
      />
      
      <StatsCard
        title="Confidence"
        value={`${confidence.toFixed(1)}%`}
        icon={<Brain className="h-4 w-4" />}
        trend={confidence >= 80 ? 'up' : confidence >= 60 ? 'neutral' : 'down'}
        isLoading={isLoading}
      />
      
      <StatsCard
        title="24h Volume"
        value={volume24h}
        icon={<Activity className="h-4 w-4" />}
        isLoading={isLoading}
      />
    </div>
  );
}

// =====================================
// REAL-TIME STATUS INDICATOR
// =====================================

export function RealTimeStatus({ 
  lastUpdate, 
  isConnected = true, 
  onRefresh 
}: {
  lastUpdate: string;
  isConnected?: boolean;
  onRefresh?: () => void;
}) {
  const timeSinceUpdate = React.useMemo(() => {
    const now = new Date();
    const updateTime = new Date(lastUpdate);
    const diffInSeconds = Math.floor((now.getTime() - updateTime.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  }, [lastUpdate]);

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className="text-sm font-medium">
                {isConnected ? 'Live' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center space-x-1 text-gray-400">
              <Clock className="h-3 w-3" />
              <span className="text-xs">
                Updated {timeSinceUpdate}
              </span>
            </div>
          </div>
          
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              className="text-gray-400 hover:text-white"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
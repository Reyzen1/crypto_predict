// File: frontend/src/lib/utils.ts
// Utility functions for CryptoPredict Frontend

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// =====================================
// DATA FORMATTING UTILITIES
// =====================================

export const formatPrice = (price: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);
};

export const formatLargeNumber = (num: number): string => {
  if (num >= 1e9) {
    return `${(num / 1e9).toFixed(2)}B`;
  }
  if (num >= 1e6) {
    return `${(num / 1e6).toFixed(2)}M`;
  }
  if (num >= 1e3) {
    return `${(num / 1e3).toFixed(2)}K`;
  }
  return num.toFixed(2);
};

export const formatPercentage = (percentage: number, showSign: boolean = true): string => {
  const sign = showSign && percentage > 0 ? '+' : '';
  return `${sign}${percentage.toFixed(2)}%`;
};

export const formatTimestamp = (timestamp: string | number): string => {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTimeAgo = (timestamp: string): string => {
  const now = new Date();
  const past = new Date(timestamp);
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000);

  if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
};

// =====================================
// TREND ANALYSIS UTILITIES
// =====================================

export const calculateTrend = (current: number, previous: number): 'up' | 'down' | 'neutral' => {
  if (current > previous) return 'up';
  if (current < previous) return 'down';
  return 'neutral';
};

export const calculatePercentageChange = (current: number, previous: number): number => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

export const getTrendColor = (trend: 'up' | 'down' | 'neutral'): string => {
  switch (trend) {
    case 'up': return 'text-green-500';
    case 'down': return 'text-red-500';
    default: return 'text-gray-400';
  }
};

// =====================================
// CHART UTILITIES
// =====================================

export const generateChartColors = (count: number): string[] => {
  const baseColors = [
    '#3B82F6', // blue
    '#A855F7', // purple
    '#10B981', // green
    '#F59E0B', // yellow
    '#EF4444', // red
    '#8B5CF6', // violet
    '#06B6D4', // cyan
    '#84CC16', // lime
  ];
  
  const colors: string[] = [];
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length]);
  }
  return colors;
};

export const formatChartTooltip = (value: number, name: string): [string, string] => {
  let formattedValue: string;
  
  if (name.toLowerCase().includes('price')) {
    formattedValue = formatPrice(value);
  } else if (name.toLowerCase().includes('volume')) {
    formattedValue = formatLargeNumber(value);
  } else if (name.toLowerCase().includes('percent') || name.toLowerCase().includes('%')) {
    formattedValue = formatPercentage(value);
  } else {
    formattedValue = value.toLocaleString();
  }
  
  return [formattedValue, name];
};

// =====================================
// VALIDATION UTILITIES
// =====================================

export const isValidPrice = (price: any): boolean => {
  return typeof price === 'number' && price > 0 && isFinite(price);
};

export const isValidTimestamp = (timestamp: any): boolean => {
  const date = new Date(timestamp);
  return !isNaN(date.getTime());
};

export const sanitizeApiResponse = (data: any): any => {
  if (Array.isArray(data)) {
    return data.filter(item => item !== null && item !== undefined);
  }
  return data;
};

// =====================================
// LOCAL STORAGE UTILITIES
// =====================================

export const getFromLocalStorage = <T>(key: string, defaultValue: T): T => {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.warn(`Error reading localStorage key "${key}":`, error);
    return defaultValue;
  }
};

export const setToLocalStorage = <T>(key: string, value: T): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Error setting localStorage key "${key}":`, error);
  }
};

export const removeFromLocalStorage = (key: string): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Error removing localStorage key "${key}":`, error);
  }
};

// =====================================
// CONSTANTS AND CONFIGURATIONS
// =====================================

export const CRYPTO_SYMBOLS = {
  BTC: 'Bitcoin',
  ETH: 'Ethereum',
  ADA: 'Cardano',
  DOT: 'Polkadot',
} as const;

export const TIME_RANGES = {
  '24h': { label: '24 Hours', days: 1 },
  '7d': { label: '7 Days', days: 7 },
  '30d': { label: '30 Days', days: 30 },
  '90d': { label: '90 Days', days: 90 },
} as const;

export const CHART_THEMES = {
  dark: {
    background: '#1F2937',
    grid: '#374151',
    text: '#9CA3AF',
    primary: '#3B82F6',
    secondary: '#A855F7',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  },
  light: {
    background: '#FFFFFF',
    grid: '#E5E7EB',
    text: '#374151',
    primary: '#2563EB',
    secondary: '#7C3AED',
    success: '#059669',
    warning: '#D97706',
    error: '#DC2626',
  },
} as const;

export const API_REFRESH_INTERVALS = {
  realtime: 5000,    // 5 seconds
  frequent: 30000,   // 30 seconds
  normal: 60000,     // 1 minute
  slow: 300000,      // 5 minutes
} as const;

// =====================================
// ERROR HANDLING UTILITIES
// =====================================

export const handleApiError = (error: any): string => {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const isNetworkError = (error: any): boolean => {
  return error?.code === 'NETWORK_ERROR' || 
         error?.message?.includes('Network Error') ||
         !navigator.onLine;
};

// =====================================
// PERFORMANCE UTILITIES
// =====================================

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// =====================================
// CRYPTO-SPECIFIC UTILITIES
// =====================================

export const formatCryptoSymbol = (symbol: string): string => {
  return symbol.toUpperCase();
};

export const getCryptoIcon = (symbol: string): string => {
  const icons: Record<string, string> = {
    BTC: '₿',
    ETH: 'Ξ',
    ADA: '₳',
    DOT: '●',
  };
  return icons[symbol.toUpperCase()] || '◦';
};

export const getCryptoColor = (symbol: string): string => {
  const colors: Record<string, string> = {
    BTC: '#F7931A',
    ETH: '#627EEA', 
    ADA: '#0033AD',
    DOT: '#E6007A',
  };
  return colors[symbol.toUpperCase()] || '#6B7280';
};

export const calculateMarketCap = (price: number, circulatingSupply: number): number => {
  return price * circulatingSupply;
};

export const calculatePriceChange = (current: number, previous: number): {
  absolute: number;
  percentage: number;
  trend: 'up' | 'down' | 'neutral';
} => {
  const absolute = current - previous;
  const percentage = calculatePercentageChange(current, previous);
  const trend = calculateTrend(current, previous);
  
  return { absolute, percentage, trend };
};
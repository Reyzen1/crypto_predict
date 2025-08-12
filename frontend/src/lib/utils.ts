// File: frontend/src/lib/utils.ts
// Complete utility functions for CryptoPredict Frontend

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

// =====================================
// STYLING UTILITIES
// =====================================

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
    maximumFractionDigits: 8,
  }).format(price);
};

export const formatLargeNumber = (num: number): string => {
  if (num >= 1e12) {
    return `${(num / 1e12).toFixed(2)}T`;
  }
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
    case 'up': return 'text-green-400';
    case 'down': return 'text-red-400';
    default: return 'text-gray-400';
  }
};

export const getTrendIcon = (trend: 'up' | 'down' | 'neutral'): string => {
  switch (trend) {
    case 'up': return '▲';
    case 'down': return '▼';
    default: return '●';
  }
};

// =====================================
// VALIDATION UTILITIES
// =====================================

export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isStrongPassword = (password: string): boolean => {
  // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
};

export const validateRequired = (value: string, fieldName: string): string | null => {
  if (!value || value.trim().length === 0) {
    return `${fieldName} is required`;
  }
  return null;
};

// =====================================
// LOCAL STORAGE UTILITIES
// =====================================

export const getLocalStorageItem = <T>(key: string, defaultValue: T): T => {
  if (typeof window === 'undefined') {
    return defaultValue;
  }
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.warn(`Error reading localStorage key "${key}":`, error);
    return defaultValue;
  }
};

export const setLocalStorageItem = <T>(key: string, value: T): void => {
  if (typeof window === 'undefined') {
    return;
  }
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Error setting localStorage key "${key}":`, error);
  }
};

export const removeLocalStorageItem = (key: string): void => {
  if (typeof window === 'undefined') {
    return;
  }
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Error removing localStorage key "${key}":`, error);
  }
};

// =====================================
// API UTILITIES
// =====================================

export const createApiUrl = (endpoint: string, params?: Record<string, string>): string => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const url = new URL(`${baseUrl}${endpoint}`);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  
  return url.toString();
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = getLocalStorageItem('access_token', null);
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// =====================================
// CHART UTILITIES
// =====================================

export const generateChartColors = (count: number): string[] => {
  const colors = [
    '#3B82F6', // Blue
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#F97316', // Orange
    '#06B6D4', // Cyan
    '#84CC16', // Lime
    '#EC4899', // Pink
    '#6B7280', // Gray
  ];
  
  return Array.from({ length: count }, (_, i) => colors[i % colors.length]);
};

export const smoothDataPoints = (data: number[], smoothingFactor: number = 0.3): number[] => {
  if (data.length === 0) return data;
  
  const smoothed = [data[0]];
  for (let i = 1; i < data.length; i++) {
    smoothed[i] = smoothingFactor * data[i] + (1 - smoothingFactor) * smoothed[i - 1];
  }
  
  return smoothed;
};

// =====================================
// CRYPTO UTILITIES
// =====================================

export const getCryptoIcon = (symbol: string): string => {
  const icons: Record<string, string> = {
    'BTC': '₿',
    'ETH': 'Ξ',
    'ADA': '₳',
    'DOT': '●',
    'LTC': 'Ł',
    'XRP': '◉',
    'BCH': '⟐',
    'LINK': '⬢',
    'ATOM': '⚛',
    'XLM': '*',
  };
  
  return icons[symbol.toUpperCase()] || '○';
};

export const getCryptoGradient = (symbol: string): string => {
  const gradients: Record<string, string> = {
    'BTC': 'from-orange-400 to-orange-600',
    'ETH': 'from-blue-400 to-blue-600',
    'ADA': 'from-green-400 to-green-600',
    'DOT': 'from-pink-400 to-pink-600',
    'LTC': 'from-gray-400 to-gray-600',
    'XRP': 'from-blue-300 to-blue-500',
    'BCH': 'from-green-500 to-green-700',
    'LINK': 'from-blue-500 to-blue-700',
    'ATOM': 'from-purple-400 to-purple-600',
    'XLM': 'from-cyan-400 to-cyan-600',
  };
  
  return gradients[symbol.toUpperCase()] || 'from-gray-400 to-gray-600';
};

// =====================================
// DEBOUNCE UTILITY
// =====================================

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): T => {
  let timeout: NodeJS.Timeout;
  
  return ((...args: any[]) => {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  }) as T;
};

// =====================================
// ERROR HANDLING
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
  return !error?.response && error?.request;
};

// =====================================
// THEME UTILITIES
// =====================================

export const getStatusColor = (status: 'success' | 'error' | 'warning' | 'info'): string => {
  switch (status) {
    case 'success': return 'text-green-400';
    case 'error': return 'text-red-400';
    case 'warning': return 'text-yellow-400';
    case 'info': return 'text-blue-400';
    default: return 'text-gray-400';
  }
};

export const getStatusBgColor = (status: 'success' | 'error' | 'warning' | 'info'): string => {
  switch (status) {
    case 'success': return 'bg-green-500/10 border-green-500/30';
    case 'error': return 'bg-red-500/10 border-red-500/30';
    case 'warning': return 'bg-yellow-500/10 border-yellow-500/30';
    case 'info': return 'bg-blue-500/10 border-blue-500/30';
    default: return 'bg-gray-500/10 border-gray-500/30';
  }
};
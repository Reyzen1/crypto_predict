// File: frontend/src/lib/utils.ts
// Utility functions for the application

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// =====================================
// STYLING UTILITIES
// =====================================

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// =====================================
// FORMATTING UTILITIES
// =====================================

export const formatCurrency = (
  value: number, 
  currency = 'USD', 
  minimumFractionDigits = 2
): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits,
    maximumFractionDigits: minimumFractionDigits
  }).format(value);
};

export const formatNumber = (value: number, decimals = 2): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

export const formatCompactNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
};

export const formatPercentage = (value: number, decimals = 2): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

// =====================================
// DATE/TIME UTILITIES
// =====================================

export const formatDate = (date: string | Date, options?: Intl.DateTimeFormatOptions): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  };
  
  return dateObj.toLocaleDateString('en-US', { ...defaultOptions, ...options });
};

export const formatTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  return dateObj.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const getRelativeTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);
  
  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  
  return formatDate(dateObj);
};

// =====================================
// API UTILITIES
// =====================================

export const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = localStorage.getItem('access_token');
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(`/api/v1${endpoint}`, config);
    
    // خواندن response یکبار
    let responseData;
    try {
      responseData = await response.json();
    } catch (jsonError) {
      // اگر response JSON نیست
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      throw new Error('Invalid JSON response');
    }
    
    // بررسی success بعد از خواندن data
    if (!response.ok) {
      console.error('API Error Details:', {
        status: response.status,
        statusText: response.statusText,
        endpoint,
        responseData
      });
      
      // پردازش error message
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      if (responseData?.detail) {
        errorMessage = typeof responseData.detail === 'string' 
          ? responseData.detail 
          : JSON.stringify(responseData.detail);
      } else if (responseData?.message) {
        errorMessage = typeof responseData.message === 'string' 
          ? responseData.message 
          : JSON.stringify(responseData.message);
      }
      
      throw new Error(errorMessage);
    }
    
    // برگرداندن data در صورت موفقیت
    return responseData;
    
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

// =====================================
// VALIDATION UTILITIES
// =====================================

export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidPassword = (password: string): boolean => {
  // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
};

// =====================================
// LOCAL STORAGE UTILITIES
// =====================================

export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch (error) {
      console.error(`Error reading from localStorage:`, error);
      return defaultValue || null;
    }
  },

  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error writing to localStorage:`, error);
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing from localStorage:`, error);
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error(`Error clearing localStorage:`, error);
    }
  }
};

// =====================================
// CRYPTO UTILITIES
// =====================================

export const getCryptoIcon = (symbol: string): string => {
  const icons: Record<string, string> = {
    BTC: '₿',
    ETH: 'Ξ',
    ADA: '₳',
    DOT: '●',
    LINK: '⧉',
    UNI: '🦄',
    AAVE: '👻',
    SUSHI: '🍣'
  };
  
  return icons[symbol.toUpperCase()] || '◎';
};

export const getCryptoColor = (symbol: string): string => {
  const colors: Record<string, string> = {
    BTC: 'from-orange-400 to-orange-600',
    ETH: 'from-blue-400 to-blue-600',
    ADA: 'from-green-400 to-green-600',
    DOT: 'from-pink-400 to-pink-600',
    LINK: 'from-blue-500 to-blue-700',
    UNI: 'from-purple-400 to-purple-600',
    AAVE: 'from-purple-500 to-purple-700',
    SUSHI: 'from-pink-500 to-pink-700'
  };
  
  return colors[symbol.toUpperCase()] || 'from-gray-400 to-gray-600';
};

// =====================================
// CHART UTILITIES
// =====================================

export const generateChartData = (
  basePrice: number,
  days: number,
  volatility = 0.05
) => {
  const data = [];
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    const dayProgress = (days - i) / days;
    const trend = Math.sin(dayProgress * Math.PI * 2) * 0.1;
    const randomChange = (Math.random() - 0.5) * volatility;
    const totalChange = trend + randomChange;
    
    const price = basePrice * (1 + totalChange);
    const volume = Math.random() * 500000000 + 750000000;
    
    data.push({
      timestamp: date.toISOString(),
      price: parseFloat(price.toFixed(2)),
      volume: Math.floor(volume),
      prediction: parseFloat((price * (1 + Math.random() * 0.1 - 0.05)).toFixed(2))
    });
  }
  
  return data;
};

// =====================================
// ERROR HANDLING UTILITIES
// =====================================

export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred. Please try again.';
};

export const retryWithExponentialBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> => {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw new Error('Max retries exceeded');
};
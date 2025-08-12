// File: frontend/src/lib/api.ts
// API Service Layer for CryptoPredict Frontend

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Environment configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Type definitions
export interface PriceData {
  id: number;
  crypto_id: number;
  timestamp: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  market_cap?: number;
  created_at: string;
}

export interface Cryptocurrency {
  id: number;
  symbol: string;
  name: string;
  coingecko_id?: string;
  binance_symbol?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface PredictionData {
  id: number;
  crypto_id: number;
  timestamp: string;
  predicted_price: number;
  confidence_score: number;
  model_version: string;
  created_at: string;
}

export interface PriceHistoryResponse {
  crypto_id: number;
  symbol: string;
  name: string;
  start_date: string;
  end_date: string;
  interval: string;
  data_points: number;
  ohlcv_data: OHLCV[];
}

export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PredictionResponse {
  success: boolean;
  data: {
    crypto_symbol: string;
    current_price: number;
    predicted_price: number;
    confidence: number;
    prediction_date: string;
    time_horizon: string;
    model_version: string;
  };
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Create axios instance with default configuration
class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for adding auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for handling errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        
        // Handle token expiration
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          // Redirect to login or refresh token
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Generic request method with error handling
  private async request<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    data?: any,
    params?: any
  ): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request({
        method,
        url,
        data,
        params,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  // =====================================
  // CRYPTOCURRENCY ENDPOINTS
  // =====================================

  async getCryptocurrencies(): Promise<Cryptocurrency[]> {
    return this.request<Cryptocurrency[]>('get', '/crypto');
  }

  async getCryptocurrency(cryptoId: number): Promise<Cryptocurrency> {
    return this.request<Cryptocurrency>('get', `/crypto/${cryptoId}`);
  }

  async getCryptocurrencyBySymbol(symbol: string): Promise<Cryptocurrency> {
    return this.request<Cryptocurrency>('get', `/crypto/symbol/${symbol}`);
  }

  // =====================================
  // PRICE DATA ENDPOINTS  
  // =====================================

  async getCurrentPrice(cryptoId: number): Promise<PriceData> {
    return this.request<PriceData>('get', `/prices/${cryptoId}/current`);
  }

  async getPriceHistory(
    cryptoId: number,
    days: number = 30,
    interval: string = '1d'
  ): Promise<PriceHistoryResponse> {
    return this.request<PriceHistoryResponse>('get', `/prices/${cryptoId}/history`, null, {
      days,
      interval,
    });
  }

  async getPriceStatistics(cryptoId: number, days: number = 30) {
    return this.request('get', `/prices/${cryptoId}/statistics`, null, { days });
  }

  // =====================================
  // PREDICTION ENDPOINTS
  // =====================================

  async getPrediction(
    cryptoSymbol: string,
    days: number = 1
  ): Promise<PredictionResponse> {
    return this.request<PredictionResponse>('post', `/predict/${cryptoSymbol}`, {
      days,
    });
  }

  async getPredictionHistory(cryptoId: number, days: number = 30): Promise<PredictionData[]> {
    return this.request<PredictionData[]>('get', `/predictions/${cryptoId}/history`, null, {
      days,
    });
  }

  // =====================================
  // ML TRAINING ENDPOINTS
  // =====================================

  async getTrainingStatus(cryptoSymbol: string) {
    return this.request('get', `/ml/train/${cryptoSymbol}/status`);
  }

  async startTraining(cryptoSymbol: string, forceRetrain: boolean = false) {
    return this.request('post', `/ml/train/start`, {
      crypto_symbol: cryptoSymbol,
      force_retrain: forceRetrain,
    });
  }

  // =====================================
  // HEALTH & STATUS ENDPOINTS
  // =====================================

  async getHealthStatus() {
    return this.request('get', '/health');
  }

  async getSystemStatus() {
    return this.request('get', '/status');
  }
}

// Create singleton instance
export const apiService = new ApiService();

// =====================================
// REACT HOOKS FOR DATA FETCHING
// =====================================

import { useState, useEffect, useCallback } from 'react';

// Hook for fetching price history with automatic updates
export function usePriceHistory(
  cryptoId: number,
  timeRange: '24h' | '7d' | '30d' | '90d' = '24h',
  refreshInterval: number = 30000 // 30 seconds
) {
  const [data, setData] = useState<OHLCV[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Convert time range to days
  const getDays = (range: string) => {
    switch (range) {
      case '24h': return 1;
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return 1;
    }
  };

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const response = await apiService.getPriceHistory(
        cryptoId,
        getDays(timeRange),
        timeRange === '24h' ? '1h' : '1d'
      );
      setData(response.ohlcv_data);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch price history:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cryptoId, timeRange]);

  useEffect(() => {
    fetchData();

    // Set up polling for real-time updates
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { data, isLoading, error, refetch: fetchData };
}

// Hook for fetching current price with real-time updates
export function useCurrentPrice(cryptoId: number, refreshInterval: number = 10000) {
  const [price, setPrice] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrice = useCallback(async () => {
    try {
      setError(null);
      const response = await apiService.getCurrentPrice(cryptoId);
      setPrice(response.close_price);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch current price:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cryptoId]);

  useEffect(() => {
    fetchPrice();
    
    const interval = setInterval(fetchPrice, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchPrice, refreshInterval]);

  return { price, isLoading, error, refetch: fetchPrice };
}

// Hook for fetching predictions
export function usePrediction(cryptoSymbol: string) {
  const [prediction, setPrediction] = useState<PredictionResponse['data'] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrediction = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiService.getPrediction(cryptoSymbol);
      setPrediction(response.data);
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to fetch prediction:', err);
    } finally {
      setIsLoading(false);
    }
  }, [cryptoSymbol]);

  return { prediction, isLoading, error, fetchPrediction };
}

// Hook for managing cryptocurrencies list
export function useCryptocurrencies() {
  const [cryptos, setCryptos] = useState<Cryptocurrency[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCryptos = async () => {
      try {
        setError(null);
        const response = await apiService.getCryptocurrencies();
        setCryptos(response);
      } catch (err: any) {
        setError(err.message);
        console.error('Failed to fetch cryptocurrencies:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCryptos();
  }, []);

  return { cryptos, isLoading, error };
}

export default apiService;
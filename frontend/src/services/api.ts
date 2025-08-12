// File: frontend/src/services/api.ts
// Complete API service layer for CryptoPredict backend integration

import { apiRequest } from '@/lib/utils';

// =====================================
// TYPE DEFINITIONS
// =====================================

export interface CryptoSummary {
  symbol: string;
  name: string;
  current_price: number;
  predicted_price: number;
  confidence: number;
  price_change_24h: number;
  price_change_24h_percent: number;
  volume_24h: number;
  market_cap: number;
  prediction_target_date: string;
  last_updated: string;
  status: string;
}

export interface DashboardSummary {
  timestamp: string;
  cryptocurrencies: CryptoSummary[];
  market_overview: {
    total_cryptocurrencies: number;
    average_confidence: number;
    bullish_predictions: number;
    bearish_predictions: number;
    market_sentiment: string;
  };
}

export interface PriceHistoryPoint {
  timestamp: string;
  price: number;
  volume?: number;
}

export interface PredictionHistoryPoint {
  timestamp: string;
  predicted_price: number;
  confidence: number;
  model: string;
}

export interface CryptoDetails {
  symbol: string;
  name: string;
  current_price: number;
  predicted_price: number;
  confidence: number;
  price_history: PriceHistoryPoint[];
  prediction_history: PredictionHistoryPoint[];
  technical_indicators: {
    rsi?: number;
    macd?: number;
    moving_average_20?: number;
    [key: string]: number | undefined;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
    is_verified: boolean;
    created_at: string;
  };
}

// =====================================
// API SERVICE CLASS
// =====================================

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = '/api/v1';
  }

  // =====================================
  // AUTHENTICATION METHODS
  // =====================================

  async login(email: string, password: string): Promise<AuthResponse> {
    return apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(
    email: string, 
    password: string, 
    firstName?: string, 
    lastName?: string
  ): Promise<{ message: string }> {
    return apiRequest<{ message: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ 
        email, 
        password, 
        first_name: firstName,
        last_name: lastName 
      }),
    });
  }

  async getMe(): Promise<AuthResponse['user']> {
    return apiRequest<AuthResponse['user']>('/auth/me');
  }

  async refreshToken(): Promise<{ access_token: string }> {
    return apiRequest<{ access_token: string }>('/auth/refresh', {
      method: 'POST',
    });
  }

  // =====================================
  // DASHBOARD METHODS
  // =====================================

  async getDashboardSummary(symbols: string[] = ['BTC', 'ETH', 'ADA', 'DOT']): Promise<DashboardSummary> {
    const symbolsParam = symbols.join(',');
    return apiRequest<DashboardSummary>(`/dashboard/summary?symbols=${symbolsParam}`);
  }

  async getQuickCryptoData(symbol: string): Promise<CryptoSummary> {
    return apiRequest<CryptoSummary>(`/dashboard/quick/${symbol.toUpperCase()}`);
  }

  async getCryptoDetails(symbol: string, daysHistory: number = 30): Promise<CryptoDetails> {
    return apiRequest<CryptoDetails>(`/dashboard/crypto/${symbol.toUpperCase()}?days_history=${daysHistory}`);
  }

  // =====================================
  // CRYPTOCURRENCY METHODS
  // =====================================

  async getCryptocurrencyList(): Promise<{ symbol: string; name: string; status: string }[]> {
    return apiRequest<{ symbol: string; name: string; status: string }[]>('/crypto/list');
  }

  async getCurrentPrice(symbol: string): Promise<{ symbol: string; price: number; timestamp: string }> {
    return apiRequest<{ symbol: string; price: number; timestamp: string }>(`/crypto/${symbol.toUpperCase()}/price`);
  }

  async getHistoricalData(symbol: string, days: number = 30): Promise<PriceHistoryPoint[]> {
    return apiRequest<PriceHistoryPoint[]>(`/crypto/${symbol.toUpperCase()}/historical?days=${days}`);
  }

  // =====================================
  // PREDICTIONS METHODS
  // =====================================

  async makePrediction(symbol: string, days: number = 1): Promise<{
    symbol: string;
    predicted_price: number;
    confidence: number;
    prediction_date: string;
  }> {
    return apiRequest<{
      symbol: string;
      predicted_price: number;
      confidence: number;
      prediction_date: string;
    }>('/ml/predictions/predict', {
      method: 'POST',
      body: JSON.stringify({ symbol: symbol.toUpperCase(), days }),
    });
  }

  async getPredictionHistory(symbol: string, days: number = 30): Promise<PredictionHistoryPoint[]> {
    return apiRequest<PredictionHistoryPoint[]>(`/ml/predictions/history/${symbol.toUpperCase()}?days=${days}`);
  }

  // =====================================
  // SYSTEM HEALTH METHODS
  // =====================================

  async getSystemHealth(): Promise<{
    status: string;
    database: { status: string };
    redis: { status: string };
    ml_service: { status: string };
    timestamp: string;
  }> {
    return apiRequest<{
      status: string;
      database: { status: string };
      redis: { status: string };
      ml_service: { status: string };
      timestamp: string;
    }>('/system/health');
  }

  // =====================================
  // UTILITY METHODS
  // =====================================

  async testConnection(): Promise<boolean> {
    try {
      await this.getSystemHealth();
      return true;
    } catch (error) {
      console.error('API connection test failed:', error);
      return false;
    }
  }

  // Method to check if backend is available
  async isBackendAvailable(): Promise<boolean> {
    try {
      const response = await fetch('/api/v1/health', {
        method: 'GET',
        timeout: 5000
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// =====================================
// SINGLETON INSTANCE
// =====================================

export const apiService = new ApiService();

// =====================================
// HOOK FOR API SERVICE
// =====================================

import { useState, useEffect } from 'react';

export const useApiStatus = () => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkApiStatus = async () => {
      setIsLoading(true);
      try {
        const status = await apiService.isBackendAvailable();
        setIsOnline(status);
      } catch (error) {
        setIsOnline(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkApiStatus();

    // Check every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  return { isOnline, isLoading };
};

// =====================================
// WEBSOCKET SERVICE (for real-time updates)
// =====================================

export class WebSocketService {
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectInterval = 5000;
  private maxReconnectAttempts = 5;
  private reconnectAttempts = 0;

  connect(): void {
    try {
      const token = localStorage.getItem('access_token');
      const wsUrl = process.env.NODE_ENV === 'production' 
        ? `wss://${window.location.host}/api/v1/ws/crypto${token ? `?token=${token}` : ''}`
        : `ws://localhost:8000/api/v1/ws/crypto${token ? `?token=${token}` : ''}`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notifySubscribers(data.type, data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        if (event.code !== 1000) { // Not normal closure
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.attemptReconnect();
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(event: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }
    this.subscribers.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      const eventSubscribers = this.subscribers.get(event);
      if (eventSubscribers) {
        eventSubscribers.delete(callback);
        if (eventSubscribers.size === 0) {
          this.subscribers.delete(event);
        }
      }
    };
  }

  private notifySubscribers(event: string, data: any): void {
    const eventSubscribers = this.subscribers.get(event);
    if (eventSubscribers) {
      eventSubscribers.forEach(callback => callback(data));
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}

export const wsService = new WebSocketService();
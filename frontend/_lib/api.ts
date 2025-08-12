// File: frontend/lib/api.ts
// SIMPLE API SERVICE - Test Version

export const testApiService = {
  getCurrentPrice: () => {
    return {
      price: 43234.56 + (Math.random() - 0.5) * 1000,
      change24h: (Math.random() - 0.5) * 10,
      volume: 28500000000,
      timestamp: new Date().toISOString()
    };
  },

  getPrediction: () => {
    return {
      current_price: 43234.56,
      predicted_price: 44120.00 + (Math.random() - 0.5) * 2000,
      confidence: 75 + Math.random() * 20,
      symbol: 'BTC'
    };
  }
};
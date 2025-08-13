// File: frontend/src/hooks/useCryptoManagement.ts
// Complete cryptocurrency management with event-based refresh and full list

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { apiService } from '@/services/api';

interface CryptoData {
  symbol: string;
  name: string;
  current_price: number;
  predicted_price?: number;
  confidence?: number;
  price_change_24h: number;
  price_change_24h_percent: number;
  volume_24h: number;
  market_cap: number;
  last_updated: string;
  status: string;
  isStale?: boolean; // Indicates if data needs refresh
}

interface UseCryptoManagementProps {
  defaultCryptos?: string[];
  onDataUpdate?: (data: CryptoData[]) => void;
  onError?: (error: string) => void;
}

export const useCryptoManagement = ({
  defaultCryptos = ['BTC', 'ETH', 'ADA', 'DOT'],
  onDataUpdate,
  onError
}: UseCryptoManagementProps = {}) => {
  // State management
  const [availableCryptos, setAvailableCryptos] = useState<Array<{symbol: string, name: string, status: string}>>([]);
  const [selectedCryptos, setSelectedCryptos] = useState<string[]>(defaultCryptos);
  const [cryptoData, setCryptoData] = useState<CryptoData[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  
  // Cache management
  const dataCache = useRef<Map<string, { data: CryptoData; timestamp: number }>>(new Map());
  const refreshTimestamps = useRef<Map<string, number>>(new Map());
  
  // Constants
  const STALE_THRESHOLD = 5 * 60 * 1000; // 5 minutes
  const CACHE_DURATION = 2 * 60 * 1000; // 2 minutes cache

  // =====================================
  // AVAILABLE CRYPTOCURRENCIES MANAGEMENT
  // =====================================

  const loadAvailableCryptos = useCallback(async () => {
    try {
      setIsLoadingList(true);
      const cryptoList = await apiService.getCryptocurrencyList();
      setAvailableCryptos(cryptoList);
      return cryptoList;
    } catch (error) {
      console.error('Failed to load cryptocurrency list:', error);
      if (onError) {
        onError('Failed to load cryptocurrency list');
      }
      return [];
    } finally {
      setIsLoadingList(false);
    }
  }, [onError]);

  // =====================================
  // DATA FRESHNESS MANAGEMENT
  // =====================================

  const isDataStale = useCallback((symbol: string): boolean => {
    const cached = dataCache.current.get(symbol);
    if (!cached) return true;
    
    return (Date.now() - cached.timestamp) > STALE_THRESHOLD;
  }, []);

  const markCryptoAsStale = useCallback((symbol: string) => {
    setCryptoData(prev => 
      prev.map(crypto => 
        crypto.symbol === symbol 
          ? { ...crypto, isStale: true }
          : crypto
      )
    );
  }, []);

  const checkForStaleData = useCallback(() => {
    cryptoData.forEach(crypto => {
      if (isDataStale(crypto.symbol) && !crypto.isStale) {
        markCryptoAsStale(crypto.symbol);
      }
    });
  }, [cryptoData, isDataStale, markCryptoAsStale]);

  // =====================================
  // INDIVIDUAL CRYPTO REFRESH (EVENT-BASED)
  // =====================================

  const refreshSingleCrypto = useCallback(async (symbol: string, force: boolean = false): Promise<CryptoData | null> => {
    // Check cache first (unless forced)
    if (!force) {
      const cached = dataCache.current.get(symbol);
      if (cached && (Date.now() - cached.timestamp) < CACHE_DURATION) {
        return cached.data;
      }
    }

    // Prevent concurrent requests for same symbol
    if (isRefreshing.current.has(symbol) && !force) {
      return null;
    }

    try {
      setIsRefreshing(prev => new Set(prev).add(symbol));
      
      console.log(`🔄 Event-based refresh for ${symbol}${force ? ' (forced)' : ''}`);
      
      const quickData = await apiService.getQuickCryptoData(symbol);
      
      const cryptoData: CryptoData = {
        symbol: quickData.symbol,
        name: quickData.name,
        current_price: quickData.current_price,
        predicted_price: quickData.predicted_price,
        confidence: quickData.confidence,
        price_change_24h: quickData.price_change_24h,
        price_change_24h_percent: quickData.price_change_24h_percent,
        volume_24h: quickData.volume_24h,
        market_cap: quickData.market_cap,
        last_updated: quickData.last_updated,
        status: quickData.status,
        isStale: false
      };

      // Update cache
      dataCache.current.set(symbol, {
        data: cryptoData,
        timestamp: Date.now()
      });

      // Update refresh timestamp
      refreshTimestamps.current.set(symbol, Date.now());

      // Update state
      setCryptoData(prev => {
        const updated = prev.map(crypto => 
          crypto.symbol === symbol ? cryptoData : crypto
        );
        
        // If crypto not in list, add it
        if (!updated.find(c => c.symbol === symbol)) {
          updated.push(cryptoData);
        }
        
        return updated;
      });

      return cryptoData;
      
    } catch (error) {
      console.error(`Failed to refresh ${symbol}:`, error);
      if (onError) {
        onError(`Failed to refresh ${symbol}`);
      }
      return null;
    } finally {
      setIsRefreshing(prev => {
        const newSet = new Set(prev);
        newSet.delete(symbol);
        return newSet;
      });
    }
  }, [onError, isRefreshing]);

  // =====================================
  // BULK CRYPTO REFRESH
  // =====================================

  const refreshSelectedCryptos = useCallback(async (force: boolean = false) => {
    try {
      console.log(`🔄 Bulk refresh for [${selectedCryptos.join(', ')}]${force ? ' (forced)' : ''}`);
      
      const promises = selectedCryptos.map(symbol => 
        refreshSingleCrypto(symbol, force)
          .catch(error => {
            console.error(`Failed to refresh ${symbol}:`, error);
            return null;
          })
      );

      const results = await Promise.allSettled(promises);
      const successfulData = results
        .map(result => result.status === 'fulfilled' ? result.value : null)
        .filter(Boolean) as CryptoData[];

      if (onDataUpdate && successfulData.length > 0) {
        onDataUpdate(successfulData);
      }

      return successfulData;
    } catch (error) {
      console.error('Bulk refresh failed:', error);
      if (onError) {
        onError('Failed to refresh cryptocurrency data');
      }
      return [];
    }
  }, [selectedCryptos, refreshSingleCrypto, onDataUpdate, onError]);

  // =====================================
  // CRYPTO SELECTION MANAGEMENT
  // =====================================

  const addCrypto = useCallback(async (symbol: string) => {
    if (selectedCryptos.includes(symbol)) {
      return;
    }

    setSelectedCryptos(prev => [...prev, symbol]);
    
    // Immediately fetch data for new crypto (EVENT-BASED!)
    await refreshSingleCrypto(symbol, true);
  }, [selectedCryptos, refreshSingleCrypto]);

  const removeCrypto = useCallback((symbol: string) => {
    setSelectedCryptos(prev => prev.filter(s => s !== symbol));
    setCryptoData(prev => prev.filter(crypto => crypto.symbol !== symbol));
    
    // Clean cache
    dataCache.current.delete(symbol);
    refreshTimestamps.current.delete(symbol);
  }, []);

  const toggleCrypto = useCallback(async (symbol: string) => {
    if (selectedCryptos.includes(symbol)) {
      removeCrypto(symbol);
    } else {
      await addCrypto(symbol);
    }
  }, [selectedCryptos, addCrypto, removeCrypto]);

  // =====================================
  // SEARCH FUNCTIONALITY
  // =====================================

  const filteredAvailableCryptos = useCallback(() => {
    if (!searchQuery.trim()) {
      return availableCryptos;
    }

    const query = searchQuery.toLowerCase();
    return availableCryptos.filter(crypto =>
      crypto.symbol.toLowerCase().includes(query) ||
      crypto.name.toLowerCase().includes(query)
    );
  }, [availableCryptos, searchQuery]);

  // =====================================
  // CLICK HANDLERS (EVENT-BASED)
  // =====================================

  const handleCryptoClick = useCallback(async (symbol: string) => {
    console.log(`👆 User clicked ${symbol} - triggering immediate refresh`);
    
    // Force refresh on click (EVENT-BASED!)
    await refreshSingleCrypto(symbol, true);
  }, [refreshSingleCrypto]);

  const handleStaleDataClick = useCallback(async (symbol: string) => {
    console.log(`⚠️ User clicked stale data for ${symbol} - refreshing immediately`);
    
    // Force refresh for stale data (EVENT-BASED!)
    await refreshSingleCrypto(symbol, true);
  }, [refreshSingleCrypto]);

  // =====================================
  // EFFECTS
  // =====================================

  // Load available cryptocurrencies on mount
  useEffect(() => {
    loadAvailableCryptos();
  }, [loadAvailableCryptos]);

  // Initial load of selected cryptocurrencies
  useEffect(() => {
    if (selectedCryptos.length > 0) {
      refreshSelectedCryptos(true); // Force initial load
    }
  }, []); // Only on mount

  // Check for stale data every minute
  useEffect(() => {
    const interval = setInterval(checkForStaleData, 60000);
    return () => clearInterval(interval);
  }, [checkForStaleData]);

  // =====================================
  // RETURN VALUES
  // =====================================

  return {
    // Data
    availableCryptos,
    selectedCryptos,
    cryptoData,
    filteredAvailableCryptos: filteredAvailableCryptos(),
    
    // Loading states
    isLoadingList,
    isRefreshing: isRefreshing,
    
    // Search
    searchQuery,
    setSearchQuery,
    
    // Management functions
    addCrypto,
    removeCrypto,
    toggleCrypto,
    refreshSingleCrypto,
    refreshSelectedCryptos,
    loadAvailableCryptos,
    
    // Event handlers
    handleCryptoClick,
    handleStaleDataClick,
    
    // Utilities
    isDataStale,
    getCachedData: (symbol: string) => dataCache.current.get(symbol),
    getLastRefreshTime: (symbol: string) => refreshTimestamps.current.get(symbol)
  };
};
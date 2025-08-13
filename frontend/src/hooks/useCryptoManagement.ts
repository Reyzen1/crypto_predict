// File: frontend/src/hooks/useCryptoManagement.ts
// FIXED Crypto management hook - eliminates infinite loops

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '@/services/api';

// =====================================
// TYPES
// =====================================

interface CryptoListItem {
  symbol: string;
  name: string;
  status: string;
}

interface CryptoData {
  symbol: string;
  name: string;
  current_price: number;
  predicted_price?: number;
  confidence?: number;
  price_change_24h?: number;
  price_change_24h_percent?: number;
  volume_24h?: number;
  market_cap?: number;
  last_updated: string;
  status: string;
}

interface UseCryptoManagementProps {
  onDataUpdate?: (data: CryptoData[]) => void;
  onError?: (error: string) => void;
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
}

// =====================================
// MAIN HOOK
// =====================================

export const useCryptoManagement = ({
  onDataUpdate,
  onError,
  autoRefresh = false,
  refreshInterval = 300 // 5 minutes
}: UseCryptoManagementProps = {}) => {
  
  // =====================================
  // STATE
  // =====================================
  
  const [availableCryptos, setAvailableCryptos] = useState<CryptoListItem[]>([]);
  const [selectedCryptos, setSelectedCryptos] = useState<string[]>(['BTC', 'ETH', 'ADA', 'DOT']);
  const [cryptoData, setCryptoData] = useState<CryptoData[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState<Set<string>>(new Set());

  // =====================================
  // REFS FOR PREVENTING INFINITE LOOPS
  // =====================================
  
  const dataCache = useRef<Map<string, CryptoData>>(new Map());
  const refreshTimestamps = useRef<Map<string, number>>(new Map());
  const loadingStates = useRef<Set<string>>(new Set());
  const autoRefreshTimer = useRef<NodeJS.Timeout>();
  const mountedRef = useRef(true);

  // =====================================
  // UTILITY FUNCTIONS
  // =====================================
  
  const shouldRefresh = (symbol: string, minIntervalMs: number = 120000): boolean => {
    const now = Date.now();
    const lastTime = refreshTimestamps.current.get(symbol) || 0;
    return (now - lastTime) >= minIntervalMs;
  };

  const markRefreshed = (symbol: string) => {
    refreshTimestamps.current.set(symbol, Date.now());
  };

  const isDataStale = (symbol: string, maxAgeMs: number = 300000): boolean => {
    const lastRefresh = refreshTimestamps.current.get(symbol) || 0;
    return (Date.now() - lastRefresh) > maxAgeMs;
  };

  // =====================================
  // FILTERED CRYPTOS (COMPUTED)
  // =====================================
  
  const filteredAvailableCryptos = useCallback(() => {
    if (!searchQuery) return availableCryptos;
    
    const query = searchQuery.toLowerCase();
    return availableCryptos.filter(crypto =>
      crypto.symbol.toLowerCase().includes(query) ||
      crypto.name.toLowerCase().includes(query)
    );
  }, [availableCryptos, searchQuery]);

  // =====================================
  // LOAD AVAILABLE CRYPTOS (STABLE)
  // =====================================
  
  const loadAvailableCryptos = useCallback(async () => {
    if (isLoadingList || !shouldRefresh('crypto_list', 600000)) { // 10 minutes
      return;
    }

    setIsLoadingList(true);
    
    try {
      console.log('📋 Loading available cryptocurrencies...');
      const cryptos = await apiService.getCryptocurrencyListWithRetry(3);
      
      if (mountedRef.current) {
        setAvailableCryptos(cryptos);
        markRefreshed('crypto_list');
        console.log(`✅ Loaded ${cryptos.length} available cryptocurrencies`);
      }
      
    } catch (error) {
      console.error('Failed to load available cryptos:', error);
      if (onError && mountedRef.current) {
        onError('Failed to load cryptocurrency list');
      }
      
      // Fallback to basic list
      const fallbackCryptos = [
        { symbol: 'BTC', name: 'Bitcoin', status: 'active' },
        { symbol: 'ETH', name: 'Ethereum', status: 'active' },
        { symbol: 'ADA', name: 'Cardano', status: 'active' },
        { symbol: 'DOT', name: 'Polkadot', status: 'active' }
      ];
      
      if (mountedRef.current) {
        setAvailableCryptos(fallbackCryptos);
      }
      
    } finally {
      if (mountedRef.current) {
        setIsLoadingList(false);
      }
    }
  }, [isLoadingList, onError]);

  // =====================================
  // REFRESH SINGLE CRYPTO (STABLE)
  // =====================================
  
  const refreshSingleCrypto = useCallback(async (symbol: string, force: boolean = false): Promise<CryptoData | null> => {
    // Prevent duplicate requests
    if (loadingStates.current.has(symbol)) {
      console.log(`⏳ ${symbol} already loading - skipping`);
      return dataCache.current.get(symbol) || null;
    }

    // Check if refresh is needed
    if (!force && !shouldRefresh(symbol, 90000)) { // 1.5 minutes minimum
      console.log(`⏰ ${symbol} refreshed recently - using cache`);
      return dataCache.current.get(symbol) || null;
    }

    loadingStates.current.add(symbol);
    setIsRefreshing(prev => new Set(prev).add(symbol));

    try {
      console.log(`🔄 Refreshing ${symbol}${force ? ' (forced)' : ''}`);
      
      // Mock data for now - replace with actual API call
      const cryptoData: CryptoData = {
        symbol,
        name: symbol === 'BTC' ? 'Bitcoin' : symbol === 'ETH' ? 'Ethereum' : symbol,
        current_price: 50000 + Math.random() * 10000,
        predicted_price: 51000 + Math.random() * 5000,
        confidence: 75 + Math.random() * 20,
        price_change_24h: (Math.random() - 0.5) * 2000,
        price_change_24h_percent: (Math.random() - 0.5) * 10,
        volume_24h: Math.random() * 1000000,
        market_cap: Math.random() * 1000000000,
        last_updated: new Date().toISOString(),
        status: 'active'
      };

      if (mountedRef.current) {
        // Update cache
        dataCache.current.set(symbol, cryptoData);
        markRefreshed(symbol);

        // Update state
        setCryptoData(prev => {
          const updated = prev.filter(crypto => crypto.symbol !== symbol);
          updated.push(cryptoData);
          return updated;
        });

        console.log(`✅ ${symbol} refreshed successfully`);
        return cryptoData;
      }

      return null;
      
    } catch (error) {
      console.error(`❌ Failed to refresh ${symbol}:`, error);
      if (onError && mountedRef.current) {
        onError(`Failed to refresh ${symbol}`);
      }
      return null;
      
    } finally {
      loadingStates.current.delete(symbol);
      if (mountedRef.current) {
        setIsRefreshing(prev => {
          const newSet = new Set(prev);
          newSet.delete(symbol);
          return newSet;
        });
      }
    }
  }, [onError]);

  // =====================================
  // REFRESH SELECTED CRYPTOS (STABLE)
  // =====================================
  
  const refreshSelectedCryptos = useCallback(async (force: boolean = false): Promise<CryptoData[]> => {
    if (selectedCryptos.length === 0) {
      return [];
    }

    console.log(`🔄 Bulk refresh for [${selectedCryptos.join(', ')}]${force ? ' (forced)' : ''}`);
    
    try {
      const promises = selectedCryptos.map(symbol => 
        refreshSingleCrypto(symbol, force).catch(error => {
          console.error(`Failed to refresh ${symbol}:`, error);
          return null;
        })
      );

      const results = await Promise.allSettled(promises);
      const successfulData = results
        .map(result => result.status === 'fulfilled' ? result.value : null)
        .filter(Boolean) as CryptoData[];

      if (onDataUpdate && mountedRef.current && successfulData.length > 0) {
        onDataUpdate(successfulData);
      }

      console.log(`✅ Bulk refresh completed: ${successfulData.length}/${selectedCryptos.length} successful`);
      return successfulData;
      
    } catch (error) {
      console.error('Bulk refresh failed:', error);
      if (onError && mountedRef.current) {
        onError('Failed to refresh cryptocurrency data');
      }
      return [];
    }
  }, [selectedCryptos, refreshSingleCrypto, onDataUpdate, onError]);

  // =====================================
  // CRYPTO SELECTION MANAGEMENT (STABLE)
  // =====================================
  
  const addCrypto = useCallback((symbol: string) => {
    if (selectedCryptos.includes(symbol)) {
      return;
    }

    setSelectedCryptos(prev => [...prev, symbol]);
    
    // Immediately fetch data for new crypto
    setTimeout(() => {
      refreshSingleCrypto(symbol, true);
    }, 100);
  }, [selectedCryptos, refreshSingleCrypto]);

  const removeCrypto = useCallback((symbol: string) => {
    setSelectedCryptos(prev => prev.filter(s => s !== symbol));
    
    // Remove from data and cache
    setCryptoData(prev => prev.filter(crypto => crypto.symbol !== symbol));
    dataCache.current.delete(symbol);
    refreshTimestamps.current.delete(symbol);
  }, []);

  const toggleCrypto = useCallback(async (symbol: string) => {
    if (selectedCryptos.includes(symbol)) {
      removeCrypto(symbol);
    } else {
      addCrypto(symbol);
    }
  }, [selectedCryptos, addCrypto, removeCrypto]);

  // =====================================
  // EVENT HANDLERS (USER ACTIONS)
  // =====================================
  
  const handleCryptoClick = useCallback(async (symbol: string) => {
    console.log(`👆 User clicked ${symbol} - refreshing immediately`);
    await refreshSingleCrypto(symbol, true);
  }, [refreshSingleCrypto]);

  const handleStaleDataClick = useCallback(async (symbol: string) => {
    console.log(`⚠️ User clicked stale data for ${symbol} - refreshing immediately`);
    await refreshSingleCrypto(symbol, true);
  }, [refreshSingleCrypto]);

  // =====================================
  // INITIAL LOAD (ONCE ONLY)
  // =====================================
  
  useEffect(() => {
    loadAvailableCryptos();
  }, []); // ONLY ON MOUNT

  useEffect(() => {
    if (selectedCryptos.length > 0) {
      // Initial load with delay to prevent immediate firing
      setTimeout(() => {
        refreshSelectedCryptos(true);
      }, 1000);
    }
  }, []); // ONLY ON MOUNT

  // =====================================
  // AUTO REFRESH TIMER (OPTIONAL)
  // =====================================
  
  useEffect(() => {
    if (!autoRefresh || selectedCryptos.length === 0) {
      return;
    }

    console.log(`⏰ Setting up auto refresh every ${refreshInterval} seconds`);

    autoRefreshTimer.current = setInterval(() => {
      // Only refresh if page is visible
      if (!document.hidden) {
        console.log('🔄 Auto refresh timer triggered');
        refreshSelectedCryptos(false);
      }
    }, refreshInterval * 1000);

    return () => {
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
      }
    };
  }, [autoRefresh, refreshInterval]); // MINIMAL DEPENDENCIES

  // =====================================
  // CLEANUP ON UNMOUNT
  // =====================================
  
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
      }
    };
  }, []);

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
    isRefreshing: Array.from(isRefreshing),
    
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
    getLastRefreshTime: (symbol: string) => refreshTimestamps.current.get(symbol),
    
    // Status
    getStatus: () => ({
      cacheSize: dataCache.current.size,
      loadingCount: loadingStates.current.size,
      selectedCount: selectedCryptos.length,
      availableCount: availableCryptos.length
    })
  };
};
// File: frontend/src/components/crypto/CryptoSelector.tsx
// Advanced cryptocurrency selector with search and event-based refresh

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Plus, 
  X, 
  RefreshCw, 
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Star,
  StarOff,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { getCryptoIcon, getCryptoColor } from '@/lib/utils';

// =====================================
// TYPE DEFINITIONS  
// =====================================

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
  isStale?: boolean;
}

interface CryptoSelectorProps {
  selectedCryptos: string[];
  availableCryptos: Array<{symbol: string, name: string, status: string}>;
  cryptoData: CryptoData[];
  searchQuery: string;
  isLoadingList: boolean;
  isRefreshing: Set<string>;
  filteredAvailableCryptos: Array<{symbol: string, name: string, status: string}>;
  onCryptoClick: (symbol: string) => Promise<void>;
  onStaleDataClick: (symbol: string) => Promise<void>;
  onToggleCrypto: (symbol: string) => Promise<void>;
  onSearchChange: (query: string) => void;
  onRefreshAll: () => Promise<void>;
}

// =====================================
// CRYPTO CARD COMPONENT
// =====================================

interface CryptoCardProps {
  crypto: CryptoData;
  isSelected: boolean;
  isRefreshing: boolean;
  onClick: () => Promise<void>;
  onStaleClick: () => Promise<void>;
  onToggle: () => Promise<void>;
}

const CryptoCard: React.FC<CryptoCardProps> = ({
  crypto,
  isSelected,
  isRefreshing,
  onClick,
  onStaleClick,
  onToggle
}) => {
  const formatPrice = (price: number): string => {
    if (price >= 1000000) return `$${(price / 1000000).toFixed(2)}M`;
    if (price >= 1000) return `$${(price / 1000).toFixed(1)}K`;
    return `$${price.toFixed(2)}`;
  };

  const getTimeSinceUpdate = (): string => {
    const updateTime = new Date(crypto.last_updated);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - updateTime.getTime()) / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return `${Math.floor(diffMinutes / 1440)}d ago`;
  };

  return (
    <Card className={`transition-all duration-200 cursor-pointer hover:scale-[1.02] ${
      isSelected
        ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/20'
        : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
    }`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          {/* Header with symbol and toggle */}
          <div className="flex items-center space-x-3">
            <div 
              className="text-2xl cursor-pointer"
              onClick={onClick}
              title="Click to refresh"
            >
              {getCryptoIcon(crypto.symbol)}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-white">{crypto.symbol}</h3>
                
                {/* Refresh indicator */}
                {isRefreshing && (
                  <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                )}
                
                {/* Stale data indicator */}
                {crypto.isStale && !isRefreshing && (
                  <button
                    onClick={onStaleClick}
                    className="flex items-center space-x-1 text-yellow-400 hover:text-yellow-300 transition-colors"
                    title="Data is stale - click to refresh"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-xs">Stale</span>
                  </button>
                )}
              </div>
              
              <p className="text-sm text-gray-400">{crypto.name}</p>
            </div>
            
            {/* Selection toggle */}
            <button
              onClick={onToggle}
              className={`p-1 rounded transition-colors ${
                isSelected
                  ? 'text-yellow-400 hover:text-yellow-300'
                  : 'text-gray-400 hover:text-yellow-400'
              }`}
              title={isSelected ? 'Remove from selection' : 'Add to selection'}
            >
              {isSelected ? <Star className="w-5 h-5 fill-current" /> : <StarOff className="w-5 h-5" />}
            </button>
          </div>
        </div>
        
        {/* Price information */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-white">
              {formatPrice(crypto.current_price)}
            </span>
            
            <div className={`flex items-center space-x-1 ${
              crypto.price_change_24h_percent >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {crypto.price_change_24h_percent >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">
                {Math.abs(crypto.price_change_24h_percent).toFixed(1)}%
              </span>
            </div>
          </div>
          
          {/* Prediction info */}
          {crypto.predicted_price && crypto.confidence && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Prediction:</span>
              <div className="flex items-center space-x-2">
                <span className="text-green-400">{formatPrice(crypto.predicted_price)}</span>
                <Badge variant="outline" className="text-xs border-green-500 text-green-400">
                  {crypto.confidence}% confidence
                </Badge>
              </div>
            </div>
          )}
          
          {/* Last updated */}
          <div className="flex items-center space-x-1 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>{getTimeSinceUpdate()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// =====================================
// SEARCH & ADD COMPONENT
// =====================================

interface CryptoSearchProps {
  searchQuery: string;
  filteredAvailableCryptos: Array<{symbol: string, name: string, status: string}>;
  selectedCryptos: string[];
  isLoadingList: boolean;
  onSearchChange: (query: string) => void;
  onToggleCrypto: (symbol: string) => Promise<void>;
}

const CryptoSearch: React.FC<CryptoSearchProps> = ({
  searchQuery,
  filteredAvailableCryptos,
  selectedCryptos,
  isLoadingList,
  onSearchChange,
  onToggleCrypto
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  return (
    <Card className="bg-gray-800/30 border-gray-700">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-sm font-medium flex items-center space-x-2">
            <Search className="w-4 h-4 text-blue-400" />
            <span>Add Cryptocurrencies</span>
          </CardTitle>
          
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 text-gray-400 hover:text-white"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="pt-0">
          {/* Search input */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search cryptocurrencies..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          
          {/* Results */}
          {isLoadingList ? (
            <div className="text-center py-4">
              <RefreshCw className="w-6 h-6 text-blue-400 mx-auto mb-2 animate-spin" />
              <p className="text-gray-400 text-sm">Loading cryptocurrencies...</p>
            </div>
          ) : (
            <div className="max-h-60 overflow-y-auto space-y-2">
              {filteredAvailableCryptos.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-4">
                  {searchQuery ? 'No cryptocurrencies found' : 'No cryptocurrencies available'}
                </p>
              ) : (
                filteredAvailableCryptos.map((crypto) => {
                  const isSelected = selectedCryptos.includes(crypto.symbol);
                  
                  return (
                    <button
                      key={crypto.symbol}
                      onClick={() => onToggleCrypto(crypto.symbol)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${
                        isSelected
                          ? 'bg-blue-600/20 border-blue-500 text-white'
                          : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:border-gray-500 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{getCryptoIcon(crypto.symbol)}</span>
                        <div className="text-left">
                          <p className="font-medium">{crypto.symbol}</p>
                          <p className="text-xs opacity-75">{crypto.name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {crypto.status === 'active' && (
                          <Badge variant="outline" className="text-xs border-green-500 text-green-400">
                            Active
                          </Badge>
                        )}
                        
                        {isSelected ? (
                          <X className="w-4 h-4 text-red-400" />
                        ) : (
                          <Plus className="w-4 h-4 text-blue-400" />
                        )}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
};

// =====================================
// MAIN SELECTOR COMPONENT
// =====================================

export const CryptoSelector: React.FC<CryptoSelectorProps> = (props) => {
  const {
    cryptoData,
    selectedCryptos,
    isRefreshing,
    onCryptoClick,
    onStaleDataClick,
    onToggleCrypto,
    onRefreshAll
  } = props;

  return (
    <div className="space-y-6">
      {/* Header with refresh all */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">
          Selected Cryptocurrencies ({selectedCryptos.length})
        </h2>
        
        <Button
          onClick={onRefreshAll}
          variant="ghost"
          size="sm"
          className="text-gray-400 hover:text-white"
          disabled={isRefreshing.size > 0}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing.size > 0 ? 'animate-spin' : ''}`} />
          Refresh All
        </Button>
      </div>
      
      {/* Selected cryptocurrencies grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {cryptoData.map((crypto) => (
          <CryptoCard
            key={crypto.symbol}
            crypto={crypto}
            isSelected={selectedCryptos.includes(crypto.symbol)}
            isRefreshing={isRefreshing.has(crypto.symbol)}
            onClick={() => onCryptoClick(crypto.symbol)}
            onStaleClick={() => onStaleDataClick(crypto.symbol)}
            onToggle={() => onToggleCrypto(crypto.symbol)}
          />
        ))}
      </div>
      
      {/* Add new cryptocurrencies */}
      <CryptoSearch
        searchQuery={props.searchQuery}
        filteredAvailableCryptos={props.filteredAvailableCryptos}
        selectedCryptos={selectedCryptos}
        isLoadingList={props.isLoadingList}
        onSearchChange={props.onSearchChange}
        onToggleCrypto={onToggleCrypto}
      />
    </div>
  );
};
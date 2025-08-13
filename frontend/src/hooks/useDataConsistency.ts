// File: frontend/src/hooks/useDataConsistency.ts
// Hook to ensure data consistency and completeness

'use client';

import { useEffect, useCallback, useRef } from 'react';

interface DataValidation {
  isValid: boolean;
  errors: string[];
  lastCheck: Date;
}

interface UseDataConsistencyProps {
  data: any;
  validationRules: ValidationRule[];
  onInvalidData?: (errors: string[]) => void;
  autoRefreshOnInvalid?: () => Promise<void>;
}

interface ValidationRule {
  name: string;
  check: (data: any) => boolean;
  message: string;
}

export const useDataConsistency = ({
  data,
  validationRules,
  onInvalidData,
  autoRefreshOnInvalid
}: UseDataConsistencyProps) => {
  const lastValidationRef = useRef<DataValidation>({
    isValid: true,
    errors: [],
    lastCheck: new Date()
  });

  const validateData = useCallback((data: any): DataValidation => {
    const errors: string[] = [];
    
    // Run all validation rules
    validationRules.forEach(rule => {
      try {
        if (!rule.check(data)) {
          errors.push(`${rule.name}: ${rule.message}`);
        }
      } catch (error) {
        errors.push(`${rule.name}: Validation error - ${error}`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      lastCheck: new Date()
    };
  }, [validationRules]);

  // Validate data whenever it changes
  useEffect(() => {
    if (!data) {
      lastValidationRef.current = {
        isValid: false,
        errors: ['No data available'],
        lastCheck: new Date()
      };
      return;
    }

    const validation = validateData(data);
    lastValidationRef.current = validation;

    // Handle invalid data
    if (!validation.isValid) {
      console.warn('Data validation failed:', validation.errors);
      
      if (onInvalidData) {
        onInvalidData(validation.errors);
      }

      // Auto refresh if function provided
      if (autoRefreshOnInvalid) {
        setTimeout(() => {
          autoRefreshOnInvalid();
        }, 1000); // Wait 1 second before refresh
      }
    }
  }, [data, validateData, onInvalidData, autoRefreshOnInvalid]);

  return {
    validation: lastValidationRef.current,
    validateData
  };
};

// =====================================
// PREDEFINED VALIDATION RULES
// =====================================

export const dashboardValidationRules: ValidationRule[] = [
  {
    name: 'Data Structure',
    check: (data) => data && typeof data === 'object',
    message: 'Dashboard data must be a valid object'
  },
  {
    name: 'Cryptocurrencies Array',
    check: (data) => Array.isArray(data.cryptocurrencies) && data.cryptocurrencies.length > 0,
    message: 'Must have at least one cryptocurrency'
  },
  {
    name: 'Market Overview',
    check: (data) => data.market_overview && typeof data.market_overview === 'object',
    message: 'Market overview data is required'
  },
  {
    name: 'Price Data Validity',
    check: (data) => {
      if (!Array.isArray(data.cryptocurrencies)) return false;
      return data.cryptocurrencies.every((crypto: any) => 
        crypto.current_price && 
        crypto.current_price > 0 &&
        typeof crypto.current_price === 'number'
      );
    },
    message: 'All cryptocurrencies must have valid positive prices'
  },
  {
    name: 'Recent Data',
    check: (data) => {
      if (!data.timestamp) return false;
      const dataTime = new Date(data.timestamp);
      const now = new Date();
      const diffMinutes = (now.getTime() - dataTime.getTime()) / (1000 * 60);
      return diffMinutes < 10; // Data should be less than 10 minutes old
    },
    message: 'Data is too old (more than 10 minutes)'
  }
];

export const chartValidationRules: ValidationRule[] = [
  {
    name: 'Chart Data Array',
    check: (data) => Array.isArray(data) && data.length > 0,
    message: 'Chart data must be a non-empty array'
  },
  {
    name: 'Data Points Structure',
    check: (data) => {
      if (!Array.isArray(data)) return false;
      return data.every((point: any) => 
        point.timestamp && 
        point.price && 
        typeof point.price === 'number' && 
        point.price > 0
      );
    },
    message: 'All data points must have valid timestamp and price'
  },
  {
    name: 'Sufficient Data Points',
    check: (data) => Array.isArray(data) && data.length >= 2,
    message: 'Need at least 2 data points for chart'
  },
  {
    name: 'Chronological Order',
    check: (data) => {
      if (!Array.isArray(data) || data.length < 2) return true;
      for (let i = 1; i < data.length; i++) {
        const prevTime = new Date(data[i-1].timestamp);
        const currTime = new Date(data[i].timestamp);
        if (currTime < prevTime) return false;
      }
      return true;
    },
    message: 'Chart data points must be in chronological order'
  }
];

export const marketStatsValidationRules: ValidationRule[] = [
  {
    name: 'Market Stats Structure',
    check: (data) => data && typeof data === 'object',
    message: 'Market stats must be a valid object'
  },
  {
    name: 'Required Fields',
    check: (data) => {
      const requiredFields = ['totalMarketCap', 'totalVolume', 'btcDominance', 'fearGreedIndex'];
      return requiredFields.every(field => 
        data[field] !== undefined && 
        data[field] !== null &&
        typeof data[field] === 'number'
      );
    },
    message: 'All required market stats fields must be present and numeric'
  },
  {
    name: 'Positive Values',
    check: (data) => {
      return data.totalMarketCap > 0 && data.totalVolume > 0 && data.btcDominance > 0;
    },
    message: 'Market cap, volume, and BTC dominance must be positive'
  },
  {
    name: 'Reasonable Ranges',
    check: (data) => {
      return (
        data.btcDominance <= 100 && 
        data.fearGreedIndex >= 0 && 
        data.fearGreedIndex <= 100
      );
    },
    message: 'BTC dominance and fear/greed index must be in valid ranges'
  }
];
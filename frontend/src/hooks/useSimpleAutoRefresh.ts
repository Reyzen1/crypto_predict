// File: frontend/src/hooks/useSimpleAutoRefresh.ts
// Simple auto refresh hook that enhances existing code

'use client';

import { useEffect, useRef, useCallback } from 'react';

interface AutoRefreshConfig {
  enabled: boolean;
  interval: number; // seconds
  onlyWhenVisible?: boolean;
  onlyWhenActive?: boolean;
}

interface UseAutoRefreshProps {
  refreshFn: () => Promise<void>;
  config: AutoRefreshConfig;
  dependencies?: any[];
}

export const useSimpleAutoRefresh = ({
  refreshFn,
  config,
  dependencies = []
}: UseAutoRefreshProps) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  const lastActivityRef = useRef(Date.now());
  const isVisibleRef = useRef(true);
  const isActiveRef = useRef(true);

  // Track page visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden;
      
      // If page becomes visible after being hidden, refresh immediately
      if (isVisibleRef.current && config.enabled) {
        refreshFn();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [refreshFn, config.enabled]);

  // Track user activity
  useEffect(() => {
    const updateActivity = () => {
      lastActivityRef.current = Date.now();
      isActiveRef.current = true;
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity);
    });

    // Check activity every 30 seconds
    const activityChecker = setInterval(() => {
      const timeSinceActivity = Date.now() - lastActivityRef.current;
      isActiveRef.current = timeSinceActivity < 120000; // 2 minutes
    }, 30000);

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
      clearInterval(activityChecker);
    };
  }, []);

  // Setup auto refresh
  useEffect(() => {
    if (!config.enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      return;
    }

    const doRefresh = async () => {
      // Check conditions
      const shouldRefresh = 
        (!config.onlyWhenVisible || isVisibleRef.current) &&
        (!config.onlyWhenActive || isActiveRef.current);

      if (shouldRefresh) {
        try {
          await refreshFn();
        } catch (error) {
          console.error('Auto refresh failed:', error);
        }
      }
    };

    // Set up interval
    intervalRef.current = setInterval(doRefresh, config.interval * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refreshFn, config, ...dependencies]);

  // Manual refresh function
  const manualRefresh = useCallback(async () => {
    try {
      await refreshFn();
    } catch (error) {
      console.error('Manual refresh failed:', error);
    }
  }, [refreshFn]);

  return {
    manualRefresh,
    isVisible: isVisibleRef.current,
    isActive: isActiveRef.current
  };
};
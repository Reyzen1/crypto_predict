// File: frontend/src/hooks/useSimpleAutoRefresh.ts
// FIXED Auto refresh hook - eliminates infinite loops

'use client';

import { useEffect, useRef, useCallback } from 'react';

interface AutoRefreshConfig {
  enabled: boolean;
  interval: number; // seconds
  onlyWhenVisible?: boolean;
  onlyWhenActive?: boolean;
  maxRetries?: number;
}

interface UseAutoRefreshProps {
  refreshFn: () => Promise<void>;
  config: AutoRefreshConfig;
  debugName?: string; // For debugging
}

export const useSimpleAutoRefresh = ({
  refreshFn,
  config,
  debugName = 'AutoRefresh'
}: UseAutoRefreshProps) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  const lastActivityRef = useRef(Date.now());
  const isVisibleRef = useRef(true);
  const isActiveRef = useRef(true);
  const retryCountRef = useRef(0);
  const lastRefreshRef = useRef(0);
  const isRefreshingRef = useRef(false);

  // =====================================
  // TRACK PAGE VISIBILITY (STABLE)
  // =====================================
  
  useEffect(() => {
    const handleVisibilityChange = () => {
      const wasVisible = isVisibleRef.current;
      isVisibleRef.current = !document.hidden;
      
      console.log(`👁️ [${debugName}] Visibility changed: ${isVisibleRef.current ? 'visible' : 'hidden'}`);
      
      // If page becomes visible after being hidden, consider immediate refresh
      if (isVisibleRef.current && !wasVisible && config.enabled) {
        const timeSinceLastRefresh = Date.now() - lastRefreshRef.current;
        if (timeSinceLastRefresh > config.interval * 1000) {
          console.log(`🔄 [${debugName}] Page visible after being hidden - refreshing`);
          performRefresh('visibility_change');
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [config.enabled, config.interval, debugName]); // STABLE DEPENDENCIES

  // =====================================
  // TRACK USER ACTIVITY (STABLE)
  // =====================================
  
  useEffect(() => {
    const updateActivity = () => {
      lastActivityRef.current = Date.now();
      isActiveRef.current = true;
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity);
    });

    // Check activity periodically
    const activityChecker = setInterval(() => {
      const timeSinceActivity = Date.now() - lastActivityRef.current;
      const wasActive = isActiveRef.current;
      isActiveRef.current = timeSinceActivity < 300000; // 5 minutes
      
      if (wasActive !== isActiveRef.current) {
        console.log(`⚡ [${debugName}] Activity changed: ${isActiveRef.current ? 'active' : 'inactive'}`);
      }
    }, 60000); // Check every minute

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
      clearInterval(activityChecker);
    };
  }, [debugName]); // STABLE DEPENDENCIES

  // =====================================
  // SAFE REFRESH FUNCTION
  // =====================================
  
  const performRefresh = useCallback(async (trigger: string) => {
    // Prevent multiple simultaneous refreshes
    if (isRefreshingRef.current) {
      console.log(`⏳ [${debugName}] Refresh already in progress - skipping ${trigger}`);
      return;
    }

    // Check minimum interval between refreshes
    const timeSinceLastRefresh = Date.now() - lastRefreshRef.current;
    const minInterval = config.interval * 1000;
    
    if (timeSinceLastRefresh < minInterval) {
      console.log(`⏰ [${debugName}] Too soon since last refresh (${Math.round(timeSinceLastRefresh/1000)}s < ${config.interval}s) - skipping ${trigger}`);
      return;
    }

    // Check conditions
    const shouldRefresh = 
      (!config.onlyWhenVisible || isVisibleRef.current) &&
      (!config.onlyWhenActive || isActiveRef.current);

    if (!shouldRefresh) {
      console.log(`🚫 [${debugName}] Conditions not met - skipping ${trigger} (visible: ${isVisibleRef.current}, active: ${isActiveRef.current})`);
      return;
    }

    isRefreshingRef.current = true;
    lastRefreshRef.current = Date.now();

    try {
      console.log(`🔄 [${debugName}] Performing refresh (trigger: ${trigger})`);
      await refreshFn();
      
      // Reset retry count on success
      retryCountRef.current = 0;
      console.log(`✅ [${debugName}] Refresh successful`);
      
    } catch (error) {
      console.error(`❌ [${debugName}] Refresh failed:`, error);
      
      // Increment retry count
      retryCountRef.current++;
      
      // If max retries exceeded, disable for a while
      if (config.maxRetries && retryCountRef.current >= config.maxRetries) {
        console.warn(`🛑 [${debugName}] Max retries (${config.maxRetries}) exceeded - backing off`);
        // Add a longer delay before next attempt
        lastRefreshRef.current = Date.now() + (config.interval * 1000 * 2);
      }
    } finally {
      isRefreshingRef.current = false;
    }
  }, [refreshFn, config, debugName]);

  // =====================================
  // SETUP AUTO REFRESH INTERVAL
  // =====================================
  
  useEffect(() => {
    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }

    if (!config.enabled) {
      console.log(`🔇 [${debugName}] Auto refresh disabled`);
      return;
    }

    console.log(`⏰ [${debugName}] Setting up auto refresh every ${config.interval} seconds`);

    // Set up new interval
    intervalRef.current = setInterval(() => {
      performRefresh('timer');
    }, config.interval * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
    };
  }, [config.enabled, config.interval, debugName, performRefresh]);

  // =====================================
  // MANUAL REFRESH FUNCTION
  // =====================================
  
  const manualRefresh = useCallback(async () => {
    console.log(`👆 [${debugName}] Manual refresh triggered`);
    await performRefresh('manual');
  }, [performRefresh, debugName]);

  // =====================================
  // STATUS GETTERS
  // =====================================
  
  const getStatus = useCallback(() => ({
    isVisible: isVisibleRef.current,
    isActive: isActiveRef.current,
    isRefreshing: isRefreshingRef.current,
    lastRefresh: lastRefreshRef.current,
    retryCount: retryCountRef.current,
    nextRefreshIn: Math.max(0, config.interval * 1000 - (Date.now() - lastRefreshRef.current))
  }), [config.interval]);

  return {
    manualRefresh,
    getStatus,
    isVisible: isVisibleRef.current,
    isActive: isActiveRef.current,
    isRefreshing: isRefreshingRef.current
  };
};

// =====================================
// SIMPLE AUTO REFRESH (MINIMAL VERSION)
// =====================================

export const useMinimalAutoRefresh = (
  refreshFn: () => Promise<void>,
  intervalSeconds: number = 300, // 5 minutes default
  enabled: boolean = true,
  debugName: string = 'MinimalRefresh'
) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  const lastRefreshRef = useRef(0);
  const isRefreshingRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const safeRefresh = async () => {
      // Prevent overlapping refreshes
      if (isRefreshingRef.current) {
        return;
      }

      // Minimum interval check
      const now = Date.now();
      if (now - lastRefreshRef.current < intervalSeconds * 1000) {
        return;
      }

      // Only refresh if page is visible
      if (document.hidden) {
        return;
      }

      isRefreshingRef.current = true;
      lastRefreshRef.current = now;

      try {
        console.log(`🔄 [${debugName}] Auto refresh (${intervalSeconds}s interval)`);
        await refreshFn();
        console.log(`✅ [${debugName}] Success`);
      } catch (error) {
        console.error(`❌ [${debugName}] Failed:`, error);
      } finally {
        isRefreshingRef.current = false;
      }
    };

    intervalRef.current = setInterval(safeRefresh, intervalSeconds * 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, intervalSeconds, debugName]); // MINIMAL DEPENDENCIES

  return {
    manualRefresh: useCallback(async () => {
      if (isRefreshingRef.current) return;
      
      isRefreshingRef.current = true;
      try {
        await refreshFn();
      } finally {
        isRefreshingRef.current = false;
      }
    }, [refreshFn])
  };
};
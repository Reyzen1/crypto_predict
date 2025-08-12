// File: frontend/src/components/ToastProvider.tsx
// Toast notification system provider

'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

// =====================================
// TYPE DEFINITIONS
// =====================================

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  success: (message: string, title?: string) => string;
  error: (message: string, title?: string) => string;
  warning: (message: string, title?: string) => string;
  info: (message: string, title?: string) => string;
}

interface ToastProviderProps {
  children: ReactNode;
}

// =====================================
// CONTEXT CREATION
// =====================================

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// =====================================
// TOAST COMPONENT
// =====================================

interface ToastComponentProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

const ToastComponent: React.FC<ToastComponentProps> = ({ toast, onRemove }) => {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />;
      default:
        return <Info className="w-5 h-5 text-gray-400" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success':
        return 'border-green-500/20';
      case 'error':
        return 'border-red-500/20';
      case 'warning':
        return 'border-yellow-500/20';
      case 'info':
        return 'border-blue-500/20';
      default:
        return 'border-gray-500/20';
    }
  };

  return (
    <div
      className={`
        bg-gray-800 border ${getBorderColor()} rounded-lg shadow-lg p-4 
        max-w-sm w-full transform transition-all duration-300 ease-in-out
        animate-in slide-in-from-right-5 fade-in-0
      `}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        
        <div className="ml-3 flex-1">
          {toast.title && (
            <p className="text-sm font-medium text-white">
              {toast.title}
            </p>
          )}
          <p className={`text-sm ${toast.title ? 'mt-1' : ''} text-gray-300`}>
            {toast.message}
          </p>
          
          {toast.action && (
            <div className="mt-3">
              <Button
                onClick={toast.action.onClick}
                variant="outline"
                size="sm"
                className="text-xs border-gray-600 text-gray-300 hover:text-white hover:border-gray-500"
              >
                {toast.action.label}
              </Button>
            </div>
          )}
        </div>
        
        <div className="ml-4 flex-shrink-0">
          <Button
            onClick={() => onRemove(toast.id)}
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-white h-6 w-6 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

// =====================================
// TOAST CONTAINER
// =====================================

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <ToastComponent
          key={toast.id}
          toast={toast}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
};

// =====================================
// TOAST PROVIDER COMPONENT
// =====================================

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000
    };

    setToasts((current) => [...current, newToast]);

    // Auto remove after duration
    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }

    return id;
  }, [removeToast]);

  // Convenience methods
  const success = useCallback((message: string, title?: string) => {
    return addToast({ type: 'success', message, title });
  }, [addToast]);

  const error = useCallback((message: string, title?: string) => {
    return addToast({ type: 'error', message, title, duration: 7000 });
  }, [addToast]);

  const warning = useCallback((message: string, title?: string) => {
    return addToast({ type: 'warning', message, title });
  }, [addToast]);

  const info = useCallback((message: string, title?: string) => {
    return addToast({ type: 'info', message, title });
  }, [addToast]);

  const value: ToastContextType = {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

// =====================================
// TOAST HOOK WITH GLOBAL ACCESS
// =====================================

// Global toast instance (for use outside React components)
let globalToast: ToastContextType | null = null;

export const setGlobalToast = (toast: ToastContextType) => {
  globalToast = toast;
};

export const toast = {
  success: (message: string, title?: string) => {
    if (globalToast) {
      return globalToast.success(message, title);
    }
    console.warn('Toast called outside of ToastProvider context');
    return '';
  },
  error: (message: string, title?: string) => {
    if (globalToast) {
      return globalToast.error(message, title);
    }
    console.warn('Toast called outside of ToastProvider context');
    return '';
  },
  warning: (message: string, title?: string) => {
    if (globalToast) {
      return globalToast.warning(message, title);
    }
    console.warn('Toast called outside of ToastProvider context');
    return '';
  },
  info: (message: string, title?: string) => {
    if (globalToast) {
      return globalToast.info(message, title);
    }
    console.warn('Toast called outside of ToastProvider context');
    return '';
  }
};
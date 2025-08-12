// File: frontend/src/components/ErrorBoundary.tsx
// Error Boundary Component for handling React errors gracefully

'use client';

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

// =====================================
// TYPE DEFINITIONS
// =====================================

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

// =====================================
// ERROR BOUNDARY CLASS COMPONENT
// =====================================

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });
    
    // Log to error reporting service in production
    if (process.env.NODE_ENV === 'production') {
      // Send to error tracking service (Sentry, Bugsnag, etc.)
      this.logErrorToService(error, errorInfo);
    }
  }

  private logErrorToService(error: Error, errorInfo: React.ErrorInfo) {
    // Placeholder for error tracking service integration
    console.log('Would log to error service:', { error, errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 max-w-md w-full text-center">
            <div className="flex justify-center mb-4">
              <AlertCircle className="w-16 h-16 text-red-400" />
            </div>
            
            <h1 className="text-white text-xl font-semibold mb-2">
              Something went wrong
            </h1>
            
            <p className="text-gray-400 mb-6">
              We're sorry, but something unexpected happened. You can try refreshing the page or go back to the dashboard.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={this.handleReset}
                variant="outline"
                className="flex-1 border-gray-600 text-gray-300 hover:text-white hover:border-gray-500"
              >
                Try Again
              </Button>
              
              <Button
                onClick={this.handleReload}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Page
              </Button>
            </div>
            
            {/* Development error details */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="text-gray-400 cursor-pointer mb-2 font-medium">
                  Error Details (Development Only)
                </summary>
                <div className="bg-gray-900 rounded p-3 text-xs">
                  <div className="text-red-400 font-mono mb-2">
                    {this.state.error.toString()}
                  </div>
                  {this.state.errorInfo?.componentStack && (
                    <div className="text-gray-500 font-mono whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// =====================================
// FUNCTIONAL WRAPPER (for easier usage)
// =====================================

interface ErrorBoundaryWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const ErrorBoundaryWrapper: React.FC<ErrorBoundaryWrapperProps> = ({ 
  children, 
  fallback 
}) => {
  return (
    <ErrorBoundary fallback={fallback}>
      {children}
    </ErrorBoundary>
  );
};
# docs\Design\19_Implementation_Strategy_Complete.md
# 🚀 Implementation Strategy - Week 4 (Days 22-28)
## Complete Development Roadmap & Class Architecture

---

# 🗓️ **روز 22-25: Class Design & Code Architecture**

## 🏗️ **Component Architecture for Frontend (روز 22 - 8 ساعت)**

### **⚛️ Next.js 14 Component Architecture**

```typescript
// =============================================
// FRONTEND COMPONENT ARCHITECTURE
// Next.js 14 + TypeScript + Clean Architecture
// =============================================

// 📁 Project Structure
src/
├── app/                          # Next.js 14 App Router
│   ├── (dashboard)/             # Dashboard route group
│   │   ├── page.tsx            # Main dashboard
│   │   ├── signals/            # Signals pages
│   │   ├── watchlist/          # Watchlist management  
│   │   └── analytics/          # Analytics pages
│   ├── (admin)/               # Admin route group
│   │   ├── page.tsx           # Admin dashboard
│   │   ├── suggestions/       # AI suggestions management
│   │   ├── system/           # System health monitoring
│   │   └── users/            # User management
│   ├── api/                   # API routes (BFF pattern)
│   ├── globals.css           
│   └── layout.tsx            # Root layout
├── components/               # Reusable UI components
│   ├── ui/                  # Base UI components (shadcn/ui)
│   ├── dashboard/           # Dashboard-specific components
│   ├── signals/            # Signal-related components
│   ├── admin/              # Admin-specific components
│   ├── charts/             # Chart components
│   └── layout/             # Layout components
├── hooks/                  # Custom React hooks
├── lib/                   # Utility functions & configurations
├── services/              # API service layer
├── stores/               # State management (Zustand)
├── types/               # TypeScript type definitions
└── utils/               # Helper functions

// =============================================
// BASE COMPONENT ABSTRACTIONS
// =============================================

// components/base/BaseComponent.tsx
import React, { ErrorInfo, ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface BaseComponentProps {
  children?: ReactNode;
  className?: string;
  loading?: boolean;
  error?: string | null;
  testId?: string;
}

export abstract class BaseComponent<P = {}, S = {}> extends React.Component<
  BaseComponentProps & P,
  S
> {
  // Error boundary functionality
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`${this.constructor.name} Error:`, error, errorInfo);
  }
  
  // Loading state renderer
  protected renderLoading(): ReactNode {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }
  
  // Error state renderer
  protected renderError(error: string): ReactNode {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="text-red-400">⚠️</div>
          <div className="ml-2">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }
  
  // Main render method with error/loading handling
  render(): ReactNode {
    const { loading, error, className, testId } = this.props;
    
    if (error) {
      return this.renderError(error);
    }
    
    if (loading) {
      return this.renderLoading();
    }
    
    return (
      <div 
        className={cn("base-component", className)}
        data-testid={testId}
      >
        {this.renderContent()}
      </div>
    );
  }
  
  // Abstract method to be implemented by child components
  protected abstract renderContent(): ReactNode;
}

// =============================================
// LAYER-SPECIFIC COMPONENT ARCHITECTURE
// =============================================

// components/dashboard/layer1/MarketRegimeCard.tsx
import React from 'react';
import { BaseComponent } from '@/components/base/BaseComponent';
import { useMarketRegime } from '@/hooks/useMarketData';
import { MarketRegime } from '@/types/api';
import { TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react';

interface MarketRegimeCardProps {
  refreshInterval?: number;
  onRegimeChange?: (regime: MarketRegime) => void;
}

interface MarketRegimeCardState {
  previousRegime: string | null;
}

export class MarketRegimeCard extends BaseComponent<
  MarketRegimeCardProps, 
  MarketRegimeCardState
> {
  constructor(props: MarketRegimeCardProps) {
    super(props);
    this.state = {
      previousRegime: null
    };
  }
  
  private getRegimeIcon(regime: string) {
    const iconProps = { className: "h-8 w-8" };
    
    switch (regime) {
      case 'bull': return <TrendingUp {...iconProps} className="h-8 w-8 text-green-500" />;
      case 'bear': return <TrendingDown {...iconProps} className="h-8 w-8 text-red-500" />;
      case 'volatile': return <Zap {...iconProps} className="h-8 w-8 text-orange-500" />;
      default: return <Minus {...iconProps} className="h-8 w-8 text-gray-500" />;
    }
  }
  
  private getRegimeColorClass(regime: string): string {
    switch (regime) {
      case 'bull': return 'text-green-600 bg-green-50 border-green-200';
      case 'bear': return 'text-red-600 bg-red-50 border-red-200';
      case 'volatile': return 'text-orange-600 bg-orange-50 border-orange-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  }
  
  private handleRegimeChange = (newRegime: MarketRegime) => {
    const { previousRegime } = this.state;
    const { onRegimeChange } = this.props;
    
    if (previousRegime && previousRegime !== newRegime.regime) {
      // Trigger regime change callback
      onRegimeChange?.(newRegime);
      
      // Show notification for significant changes
      if (this.isSignificantChange(previousRegime, newRegime.regime)) {
        this.showRegimeChangeNotification(previousRegime, newRegime.regime);
      }
    }
    
    this.setState({ previousRegime: newRegime.regime });
  };
  
  private isSignificantChange(oldRegime: string, newRegime: string): boolean {
    const significantPairs = [
      ['bull', 'bear'], ['bear', 'bull'],
      ['bull', 'volatile'], ['bear', 'volatile']
    ];
    
    return significantPairs.some(([from, to]) => 
      oldRegime === from && newRegime === to
    );
  }
  
  private showRegimeChangeNotification(oldRegime: string, newRegime: string) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Market Regime Change', {
        body: `Market changed from ${oldRegime.toUpperCase()} to ${newRegime.toUpperCase()}`,
        icon: '/icon-192x192.png'
      });
    }
  }
  
  protected renderContent(): React.ReactNode {
    const { data: regimeData } = useMarketRegime();
    
    if (!regimeData?.success || !regimeData.data) {
      return this.renderError('Failed to load market regime data');
    }
    
    const regime = regimeData.data;
    
    // Handle regime change
    React.useEffect(() => {
      this.handleRegimeChange(regime);
    }, [regime.regime]);
    
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🌍 Market Regime
          </h3>
          {this.getRegimeIcon(regime.regime)}
        </div>
        
        <div className="space-y-4">
          {/* Regime Status Badge */}
          <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium border ${this.getRegimeColorClass(regime.regime)}`}>
            {regime.regime.toUpperCase()} {Math.round(regime.confidence * 100)}%
          </div>
          
          {/* Risk Level */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Risk Level</span>
            <span className={`text-sm font-medium ${
              regime.risk_level === 'low' ? 'text-green-600' :
              regime.risk_level === 'medium' ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {regime.risk_level.toUpperCase()}
            </span>
          </div>
          
          {/* Confidence Bar */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">Confidence</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${regime.confidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {Math.round(regime.confidence * 100)}%
              </span>
            </div>
          </div>
          
          {/* Last Updated */}
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Updated: {new Date(regime.last_updated).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  }
}

// =============================================
// SIGNAL COMPONENT ARCHITECTURE
// =============================================

// components/signals/SignalCard.tsx
import React from 'react';
import { BaseComponent } from '@/components/base/BaseComponent';
import { TradingSignal } from '@/types/api';
import { ArrowUpRight, ArrowDownRight, Shield, Target, StopCircle } from 'lucide-react';

interface SignalCardProps {
  signal: TradingSignal;
  onExecute: (signalId: number) => Promise<void>;
  onViewDetails: (signalId: number) => void;
  onFavorite?: (signalId: number) => void;
  showExecuteButton?: boolean;
  compact?: boolean;
}

interface SignalCardState {
  executing: boolean;
  favorited: boolean;
}

export class SignalCard extends BaseComponent<SignalCardProps, SignalCardState> {
  constructor(props: SignalCardProps) {
    super(props);
    this.state = {
      executing: false,
      favorited: false
    };
  }
  
  private handleExecute = async () => {
    const { signal, onExecute } = this.props;
    
    this.setState({ executing: true });
    
    try {
      await onExecute(signal.id);
      
      // Show success feedback
      this.showExecutionSuccess();
      
    } catch (error) {
      console.error('Signal execution failed:', error);
      this.showExecutionError();
    } finally {
      this.setState({ executing: false });
    }
  };
  
  private showExecutionSuccess() {
    // Could integrate with toast system
    console.log('Signal executed successfully');
  }
  
  private showExecutionError() {
    console.log('Signal execution failed');
  }
  
  private calculatePotentialReturn(): number {
    const { signal } = this.props;
    return ((signal.target_price - signal.entry_price) / signal.entry_price) * 100;
  }
  
  private getConfidenceColorClass(): string {
    const { signal } = this.props;
    if (signal.confidence_score >= 0.8) return 'bg-green-500';
    if (signal.confidence_score >= 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  }
  
  private getRiskLevelColorClass(): string {
    const { signal } = this.props;
    switch (signal.risk_level) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }
  
  protected renderContent(): React.ReactNode {
    const { signal, onViewDetails, showExecuteButton = true, compact = false } = this.props;
    const { executing } = this.state;
    
    const isLong = signal.signal_type === 'long';
    const potentialReturn = this.calculatePotentialReturn();
    
    if (compact) {
      return this.renderCompactVersion();
    }
    
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border-l-4 border-l-blue-500 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${isLong ? 'bg-green-100' : 'bg-red-100'}`}>
              {isLong ? 
                <ArrowUpRight className="h-5 w-5 text-green-600" /> :
                <ArrowDownRight className="h-5 w-5 text-red-600" />
              }
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white">
                {signal.symbol} {signal.signal_type.toUpperCase()}
              </h4>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">AI:</span>
                <div className="flex items-center">
                  <div className="w-12 bg-gray-200 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full ${this.getConfidenceColorClass()}`}
                      style={{ width: `${signal.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium ml-1">
                    {Math.round(signal.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-lg font-bold ${isLong ? 'text-green-600' : 'text-red-600'}`}>
              +{Math.abs(potentialReturn).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              R/R: {signal.risk_reward_ratio.toFixed(1)}
            </div>
          </div>
        </div>
        
        {/* Price Levels */}
        <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
          <div className="flex items-center space-x-1">
            <Target className="h-4 w-4 text-blue-500" />
            <div>
              <div className="text-gray-600 text-xs">Entry</div>
              <div className="font-medium">${signal.entry_price.toFixed(2)}</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            <ArrowUpRight className="h-4 w-4 text-green-500" />
            <div>
              <div className="text-gray-600 text-xs">Target</div>
              <div className="font-medium">${signal.target_price.toFixed(2)}</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            <StopCircle className="h-4 w-4 text-red-500" />
            <div>
              <div className="text-gray-600 text-xs">Stop</div>
              <div className="font-medium">${signal.stop_loss.toFixed(2)}</div>
            </div>
          </div>
        </div>
        
        {/* Risk Info */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Shield className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-600">Risk:</span>
            <span className={`text-sm font-medium ${this.getRiskLevelColorClass()}`}>
              {signal.risk_level}
            </span>
          </div>
          
          <div className="text-xs text-gray-500">
            Expires: {new Date(signal.expires_at).toLocaleDateString()}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-2">
          {showExecuteButton && (
            <button
              onClick={this.handleExecute}
              disabled={executing}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center justify-center"
            >
              {executing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Executing...
                </>
              ) : (
                '⚡ Execute'
              )}
            </button>
          )}
          <button
            onClick={() => onViewDetails(signal.id)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            📊 Details
          </button>
        </div>
      </div>
    );
  }
  
  private renderCompactVersion(): React.ReactNode {
    const { signal } = this.props;
    const isLong = signal.signal_type === 'long';
    const potentialReturn = this.calculatePotentialReturn();
    
    return (
      <div className="bg-white rounded-lg p-3 shadow-sm border-l-4 border-l-blue-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isLong ? 
              <ArrowUpRight className="h-4 w-4 text-green-600" /> :
              <ArrowDownRight className="h-4 w-4 text-red-600" />
            }
            <span className="font-medium text-gray-900">
              {signal.symbol} {signal.signal_type.toUpperCase()}
            </span>
          </div>
          
          <div className={`text-sm font-bold ${isLong ? 'text-green-600' : 'text-red-600'}`}>
            +{Math.abs(potentialReturn).toFixed(1)}%
          </div>
        </div>
      </div>
    );
  }
}

// =============================================
// ADMIN COMPONENT ARCHITECTURE
// =============================================

// components/admin/AISuggestionsQueue.tsx
import React from 'react';
import { BaseComponent } from '@/components/base/BaseComponent';
import { useAISuggestions } from '@/hooks/useAdminData';
import { AISuggestion, SuggestionReview } from '@/types/api';

interface AISuggestionsQueueProps {
  onReviewSuggestion: (suggestionId: number, review: SuggestionReview) => Promise<void>;
  maxSuggestions?: number;
}

interface AISuggestionsQueueState {
  selectedSuggestions: Set<number>;
  reviewingId: number | null;
}

export class AISuggestionsQueue extends BaseComponent<
  AISuggestionsQueueProps, 
  AISuggestionsQueueState
> {
  constructor(props: AISuggestionsQueueProps) {
    super(props);
    this.state = {
      selectedSuggestions: new Set(),
      reviewingId: null
    };
  }
  
  private handleBulkApprove = async () => {
    const { selectedSuggestions } = this.state;
    const { onReviewSuggestion } = this.props;
    
    for (const suggestionId of selectedSuggestions) {
      try {
        await onReviewSuggestion(suggestionId, {
          decision: 'approve',
          review_notes: 'Bulk approved'
        });
      } catch (error) {
        console.error(`Failed to approve suggestion ${suggestionId}:`, error);
      }
    }
    
    this.setState({ selectedSuggestions: new Set() });
  };
  
  private handleSingleReview = async (
    suggestionId: number, 
    decision: 'approve' | 'reject' | 'defer',
    notes?: string
  ) => {
    const { onReviewSuggestion } = this.props;
    
    this.setState({ reviewingId: suggestionId });
    
    try {
      await onReviewSuggestion(suggestionId, {
        decision,
        review_notes: notes || ''
      });
    } catch (error) {
      console.error('Review failed:', error);
    } finally {
      this.setState({ reviewingId: null });
    }
  };
  
  private toggleSelection = (suggestionId: number) => {
    this.setState(prevState => {
      const newSelected = new Set(prevState.selectedSuggestions);
      if (newSelected.has(suggestionId)) {
        newSelected.delete(suggestionId);
      } else {
        newSelected.add(suggestionId);
      }
      return { selectedSuggestions: newSelected };
    });
  };
  
  private renderSuggestionCard = (suggestion: AISuggestion) => {
    const { selectedSuggestions, reviewingId } = this.state;
    const isSelected = selectedSuggestions.has(suggestion.id);
    const isReviewing = reviewingId === suggestion.id;
    
    return (
      <div 
        key={suggestion.id}
        className={`bg-white rounded-lg p-4 shadow-sm border-2 transition-all ${
          isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => this.toggleSelection(suggestion.id)}
              className="mt-1 h-4 w-4 text-blue-600 rounded"
            />
            
            <div>
              <h4 className="font-semibold text-gray-900">
                {suggestion.crypto_symbol} - {suggestion.suggestion_type.replace('_', ' ').toUpperCase()}
              </h4>
              <div className="flex items-center space-x-2 mt-1">
                <span className="text-sm text-gray-600">AI Confidence:</span>
                <div className="flex items-center">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        suggestion.confidence_score >= 0.8 ? 'bg-green-500' :
                        suggestion.confidence_score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${suggestion.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium ml-2">
                    {Math.round(suggestion.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-xs text-gray-500">
              Suggested: {new Date(suggestion.suggested_at).toLocaleDateString()}
            </div>
            <div className="text-xs text-gray-500">
              Expires: {new Date(suggestion.expires_at).toLocaleDateString()}
            </div>
          </div>
        </div>
        
        {/* AI Reasoning */}
        <div className="mb-4">
          <h5 className="text-sm font-medium text-gray-700 mb-2">💡 AI Reasoning:</h5>
          <div className="bg-gray-50 rounded-md p-3 text-sm">
            {Object.entries(suggestion.ai_reasoning).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600">{key.replace('_', ' ')}:</span>
                <span className="font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-2">
          <button
            onClick={() => this.handleSingleReview(suggestion.id, 'approve')}
            disabled={isReviewing}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-3 py-2 rounded-md text-sm font-medium"
          >
            {isReviewing ? 'Processing...' : '✅ Approve'}
          </button>
          
          <button
            onClick={() => this.handleSingleReview(suggestion.id, 'reject')}
            disabled={isReviewing}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-3 py-2 rounded-md text-sm font-medium"
          >
            {isReviewing ? 'Processing...' : '❌ Reject'}
          </button>
          
          <button
            onClick={() => this.handleSingleReview(suggestion.id, 'defer')}
            disabled={isReviewing}
            className="px-3 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50"
          >
            ⏰ Defer
          </button>
        </div>
      </div>
    );
  };
  
  protected renderContent(): React.ReactNode {
    const { maxSuggestions = 50 } = this.props;
    const { selectedSuggestions } = this.state;
    
    const { data: suggestionsData, isLoading } = useAISuggestions({
      status: 'pending',
      limit: maxSuggestions,
      confidence_min: 0.7
    });
    
    if (isLoading) {
      return this.renderLoading();
    }
    
    if (!suggestionsData?.success || !suggestionsData.data.length) {
      return (
        <div className="text-center py-8 text-gray-500">
          No pending AI suggestions at the moment
        </div>
      );
    }
    
    const suggestions = suggestionsData.data;
    
    return (
      <div className="space-y-4">
        {/* Bulk Actions Header */}
        {selectedSuggestions.size > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-blue-800 font-medium">
                {selectedSuggestions.size} suggestions selected
              </span>
              <div className="space-x-2">
                <button
                  onClick={this.handleBulkApprove}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  ✅ Bulk Approve
                </button>
                <button
                  onClick={() => this.setState({ selectedSuggestions: new Set() })}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Suggestions List */}
        <div className="space-y-3">
          {suggestions.map(this.renderSuggestionCard)}
        </div>
        
        {/* Load More */}
        {suggestions.length === maxSuggestions && (
          <div className="text-center">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md">
              Load More Suggestions
            </button>
          </div>
        )}
      </div>
    );
  }
}

// =============================================
// CHART COMPONENT ARCHITECTURE
// =============================================

// components/charts/BaseChart.tsx
import React from 'react';
import { BaseComponent } from '@/components/base/BaseComponent';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface BaseChartProps {
  data: ChartData<'line'>;
  options?: Partial<ChartOptions<'line'>>;
  height?: number;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
}

export abstract class BaseChart extends BaseComponent<BaseChartProps> {
  protected getDefaultOptions(): ChartOptions<'line'> {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: this.getChartTitle(),
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: this.getXAxisLabel(),
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: this.getYAxisLabel(),
          },
        },
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false,
      },
    };
  }
  
  protected abstract getChartTitle(): string;
  protected abstract getXAxisLabel(): string;
  protected abstract getYAxisLabel(): string;
  
  protected renderContent(): React.ReactNode {
    const { data, options: propOptions, height = 400 } = this.props;
    
    const mergedOptions = {
      ...this.getDefaultOptions(),
      ...propOptions,
    };
    
    return (
      <div style={{ height: `${height}px` }}>
        <Line data={data} options={mergedOptions} />
      </div>
    );
  }
}

// components/charts/PriceChart.tsx
export class PriceChart extends BaseChart {
  protected getChartTitle(): string {
    return 'Price Chart';
  }
  
  protected getXAxisLabel(): string {
    return 'Time';
  }
  
  protected getYAxisLabel(): string {
    return 'Price (USD)';
  }
}

// =============================================
// HOOK ARCHITECTURE
// =============================================

// hooks/useApiData.ts - Generic API data hook
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cryptoAPI } from '@/services/api';

export function useApiData<TData>(
  queryKey: string[],
  queryFn: () => Promise<{ success: boolean; data: TData }>,
  options?: {
    refetchInterval?: number;
    staleTime?: number;
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey,
    queryFn: async () => {
      const response = await queryFn();
      if (!response.success) {
        throw new Error('API request failed');
      }
      return response.data;
    },
    refetchInterval: options?.refetchInterval,
    staleTime: options?.staleTime || 5 * 60 * 1000, // 5 minutes default
    enabled: options?.enabled,
  });
}

export function useApiMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<{ success: boolean; data: TData }>,
  options?: {
    onSuccess?: (data: TData) => void;
    onError?: (error: Error) => void;
  }
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (variables: TVariables) => {
      const response = await mutationFn(variables);
      if (!response.success) {
        throw new Error('API mutation failed');
      }
      return response.data;
    },
    onSuccess: (data) => {
      options?.onSuccess?.(data);
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['api-data'] });
    },
    onError: options?.onError,
  });
}

// hooks/useMarketData.ts - Specific market data hooks
export const useMarketRegime = () => {
  return useApiData(
    ['market-regime'],
    () => cryptoAPI.getMarketRegime(),
    { refetchInterval: 5 * 60 * 1000 }
  );
};

export const useActiveSignals = () => {
  return useApiData(
    ['active-signals'],
    () => cryptoAPI.getActiveSignals(),
    { refetchInterval: 30 * 1000 }
  );
};

export const useExecuteSignal = () => {
  return useApiMutation(
    ({ signalId, executionData }: { signalId: number; executionData: any }) =>
      cryptoAPI.executeSignal(signalId, executionData),
    {
      onSuccess: () => {
        console.log('Signal executed successfully');
      },
      onError: (error) => {
        console.error('Signal execution failed:', error);
      }
    }
  );
};
```

---

# 🗓️ **روز 23-24: Backend Classes for API Support**

## 🐍 **FastAPI Backend Class Architecture**

```python
# =============================================
# BACKEND CLASS ARCHITECTURE
# FastAPI + SQLAlchemy + Clean Architecture
# =============================================

# =============================================
# BASE CLASSES & ABSTRACTIONS
# =============================================

# app/core/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Generic types
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# =============================================
# BASE REPOSITORY PATTERN
# =============================================

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class implementing common CRUD operations
    Follows Repository pattern for data access abstraction
    """
    
    def __init__(self, model: type[ModelType]):
        self.model = model
    
    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get single record by ID"""
        result = await db.get(self.model, id)
        return result
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await query.all()
        return result
    
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """Create new record"""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, 
        db: AsyncSession, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update existing record"""
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, id: int) -> ModelType:
        """Delete record by ID"""
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

# =============================================
# BASE SERVICE PATTERN
# =============================================

class BaseService(ABC):
    """
    Base service class implementing business logic layer
    Follows Service pattern for business rule encapsulation
    """
    
    def __init__(self, repository: BaseRepository):
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get record by ID with business logic validation"""
        obj = await self.repository.get(db, id)
        if obj:
            await self.post_get_processing(obj)
        return obj
    
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """Create record with business logic validation"""
        await self.pre_create_validation(db, obj_in)
        obj = await self.repository.create(db, obj_in)
        await self.post_create_processing(db, obj)
        return obj
    
    async def update(
        self, 
        db: AsyncSession, 
        id: int, 
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """Update record with business logic validation"""
        db_obj = await self.repository.get(db, id)
        if not db_obj:
            return None
            
        await self.pre_update_validation(db, db_obj, obj_in)
        obj = await self.repository.update(db, db_obj, obj_in)
        await self.post_update_processing(db, obj)
        return obj
    
    # Hook methods for business logic (to be overridden)
    async def pre_create_validation(self, db: AsyncSession, obj_in: CreateSchemaType):
        """Override to add pre-create validation"""
        pass
    
    async def post_create_processing(self, db: AsyncSession, obj: ModelType):
        """Override to add post-create processing"""
        pass
    
    async def pre_update_validation(
        self, 
        db: AsyncSession, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ):
        """Override to add pre-update validation"""
        pass
    
    async def post_update_processing(self, db: AsyncSession, obj: ModelType):
        """Override to add post-update processing"""
        pass
    
    async def post_get_processing(self, obj: ModelType):
        """Override to add post-get processing"""
        pass

# =============================================
# LAYER 1: MACRO ANALYSIS CLASSES
# =============================================

# app/services/layer1_service.py
from app.models.layer1 import MarketRegimeAnalysis, MarketSentimentData, DominanceData
from app.schemas.layer1 import (
    MarketRegimeCreate, MarketRegimeUpdate,
    MarketSentimentCreate, MarketSentimentUpdate
)
from app.repositories.layer1_repository import (
    MarketRegimeRepository, 
    MarketSentimentRepository,
    DominanceRepository
)

class Layer1MacroService(BaseService):
    """
    🌍 Layer 1 Macro Analysis Service
    Business logic for market regime detection and sentiment analysis
    """
    
    def __init__(self):
        self.regime_repo = MarketRegimeRepository()
        self.sentiment_repo = MarketSentimentRepository()
        self.dominance_repo = DominanceRepository()
        super().__init__(self.regime_repo)
    
    async def get_current_market_regime(self, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get the most recent market regime analysis"""
        try:
            # Get latest regime analysis
            latest_regime = await self.regime_repo.get_latest(db)
            
            if not latest_regime:
                self.logger.warning("No market regime data found")
                return None
            
            # Enrich with additional context
            regime_data = {
                "regime": latest_regime.market_regime,
                "confidence": float(latest_regime.confidence_score),
                "risk_level": latest_regime.risk_level,
                "trend_strength": float(latest_regime.trend_strength) if latest_regime.trend_strength else 0.0,
                "recommended_exposure": float(latest_regime.recommended_exposure) if latest_regime.recommended_exposure else 0.0,
                "sentiment_breakdown": latest_regime.sentiment_breakdown or {},
                "drivers": latest_regime.regime_drivers or [],
                "last_updated": latest_regime.analysis_time.isoformat(),
                "analysis_id": latest_regime.id
            }
            
            # Add historical context
            regime_data["historical_context"] = await self._get_regime_historical_context(db, latest_regime)
            
            return regime_data
            
        except Exception as e:
            self.logger.error(f"Error fetching market regime: {e}")
            raise
    
    async def get_market_sentiment(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive market sentiment data"""
        try:
            # Get latest sentiment data
            latest_sentiment = await self.sentiment_repo.get_latest(db)
            
            if not latest_sentiment:
                return self._get_default_sentiment()
            
            sentiment_data = {
                "fear_greed_index": float(latest_sentiment.fear_greed_index) if latest_sentiment.fear_greed_index else 50.0,
                "composite_sentiment": float(latest_sentiment.composite_sentiment) if latest_sentiment.composite_sentiment else 0.0,
                "funding_rates": latest_sentiment.funding_rates or {},
                "social_sentiment": latest_sentiment.social_sentiment or {},
                "news_sentiment": latest_sentiment.news_sentiment or {},
                "sentiment_sources": latest_sentiment.sentiment_sources or {},
                "timestamp": latest_sentiment.timestamp.isoformat(),
                "sentiment_grade": self._calculate_sentiment_grade(latest_sentiment)
            }
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Error fetching market sentiment: {e}")
            raise
    
    async def get_dominance_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Get cryptocurrency dominance data"""
        try:
            latest_dominance = await self.dominance_repo.get_latest(db)
            
            if not latest_dominance:
                return self._get_default_dominance()
            
            dominance_data = {
                "btc_dominance": float(latest_dominance.btc_dominance) if latest_dominance.btc_dominance else 0.0,
                "eth_dominance": float(latest_dominance.eth_dominance) if latest_dominance.eth_dominance else 0.0,
                "alt_dominance": float(latest_dominance.alt_dominance) if latest_dominance.alt_dominance else 0.0,
                "stablecoin_dominance": float(latest_dominance.stablecoin_dominance) if latest_dominance.stablecoin_dominance else 0.0,
                "total_market_cap": float(latest_dominance.total_market_cap) if latest_dominance.total_market_cap else 0.0,
                "total_volume": float(latest_dominance.total_volume) if latest_dominance.total_volume else 0.0,
                "dominance_changes": latest_dominance.dominance_changes or {},
                "timestamp": latest_dominance.timestamp.isoformat(),
                "dominance_analysis": self._analyze_dominance_trends(latest_dominance)
            }
            
            return dominance_data
            
        except Exception as e:
            self.logger.error(f"Error fetching dominance data: {e}")
            raise
    
    async def run_regime_analysis(self, db: AsyncSession) -> MarketRegimeAnalysis:
        """Run comprehensive market regime analysis using AI"""
        try:
            # Gather all required data
            market_data = await self._gather_macro_data(db)
            
            # Run AI analysis
            from app.ml.models.layer1 import MacroRegimeDetector
            detector = MacroRegimeDetector()
            analysis_result = detector.analyze_market_regime(market_data)
            
            # Create database record
            regime_data = MarketRegimeCreate(
                market_regime=analysis_result.regime,
                confidence_score=analysis_result.confidence,
                risk_level=analysis_result.risk_level,
                trend_strength=analysis_result.trend_strength,
                recommended_exposure=analysis_result.recommended_exposure,
                sentiment_breakdown=analysis_result.sentiment_breakdown,
                regime_drivers=analysis_result.regime_drivers,
                dominance_data=market_data.get("dominance", {}),
                macro_indicators=market_data.get("macro_indicators", {})
            )
            
            regime_record = await self.regime_repo.create(db, regime_data)
            
            # Trigger real-time updates
            await self._publish_regime_update(regime_record)
            
            # Check for regime changes and send alerts
            await self._check_regime_change_alerts(db, regime_record)
            
            return regime_record
            
        except Exception as e:
            self.logger.error(f"Error in regime analysis: {e}")
            raise
    
    # Private helper methods
    async def _gather_macro_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Gather all macro data required for analysis"""
        # Implementation to gather data from various sources
        pass
    
    async def _get_regime_historical_context(
        self, 
        db: AsyncSession, 
        current_regime: MarketRegimeAnalysis
    ) -> Dict[str, Any]:
        """Get historical context for current regime"""
        # Implementation for historical analysis
        pass
    
    def _calculate_sentiment_grade(self, sentiment: MarketSentimentData) -> str:
        """Calculate letter grade for overall sentiment"""
        if not sentiment.composite_sentiment:
            return "N/A"
        
        score = sentiment.composite_sentiment
        if score >= 0.8: return "A+"
        elif score >= 0.6: return "A"
        elif score >= 0.4: return "B"
        elif score >= 0.2: return "C"
        elif score >= 0: return "D"
        else: return "F"
    
    def _analyze_dominance_trends(self, dominance: DominanceData) -> Dict[str, Any]:
        """Analyze dominance trends and implications"""
        analysis = {
            "btc_trend": "stable",  # Analyze trend
            "eth_trend": "growing",
            "alt_season": False,
            "market_phase": "neutral"
        }
        
        # Add logic to determine trends
        if dominance.btc_dominance and dominance.btc_dominance > 50:
            analysis["market_phase"] = "btc_dominance"
        elif dominance.alt_dominance and dominance.alt_dominance > 30:
            analysis["alt_season"] = True
            analysis["market_phase"] = "alt_season"
        
        return analysis
    
    def _get_default_sentiment(self) -> Dict[str, Any]:
        """Return default sentiment data when no data available"""
        return {
            "fear_greed_index": 50.0,
            "composite_sentiment": 0.0,
            "funding_rates": {},
            "social_sentiment": {},
            "news_sentiment": {},
            "sentiment_sources": {},
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment_grade": "N/A"
        }
    
    def _get_default_dominance(self) -> Dict[str, Any]:
        """Return default dominance data when no data available"""
        return {
            "btc_dominance": 45.0,
            "eth_dominance": 20.0,
            "alt_dominance": 30.0,
            "stablecoin_dominance": 5.0,
            "total_market_cap": 0.0,
            "total_volume": 0.0,
            "dominance_changes": {},
            "timestamp": datetime.utcnow().isoformat(),
            "dominance_analysis": {
                "btc_trend": "unknown",
                "eth_trend": "unknown",
                "alt_season": False,
                "market_phase": "neutral"
            }
        }
    
    async def _publish_regime_update(self, regime: MarketRegimeAnalysis):
        """Publish regime update to real-time systems"""
        from app.core.events import EventPublisher
        
        publisher = EventPublisher()
        await publisher.publish_layer1_update({
            "type": "regime_update",
            "regime": regime.market_regime,
            "confidence": float(regime.confidence_score),
            "risk_level": regime.risk_level,
            "timestamp": regime.analysis_time.isoformat()
        })
    
    async def _check_regime_change_alerts(
        self, 
        db: AsyncSession, 
        new_regime: MarketRegimeAnalysis
    ):
        """Check for significant regime changes and send alerts"""
        previous_regime = await self.regime_repo.get_previous(db, new_regime.analysis_time)
        
        if previous_regime and previous_regime.market_regime != new_regime.market_regime:
            # Significant regime change detected
            from app.core.notifications import NotificationService
            
            notification_service = NotificationService()
            await notification_service.send_regime_change_alert(
                old_regime=previous_regime.market_regime,
                new_regime=new_regime.market_regime,
                confidence=float(new_regime.confidence_score)
            )

# =============================================
# LAYER 3: ASSET SELECTION CLASSES
# =============================================

# app/services/layer3_service.py
class Layer3AssetService(BaseService):
    """
    💰 Layer 3 Asset Selection Service
    Business logic for watchlist management and AI suggestions
    """
    
    def __init__(self):
        from app.repositories.layer3_repository import (
            WatchlistRepository, 
            AISuggestionRepository,
            WatchlistItemRepository
        )
        
        self.watchlist_repo = WatchlistRepository()
        self.suggestion_repo = AISuggestionRepository()
        self.watchlist_item_repo = WatchlistItemRepository()
        super().__init__(self.watchlist_repo)
    
    async def get_user_watchlists(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get all watchlists for a user (including admin watchlists)"""
        try:
            # Get personal watchlists
            personal_watchlists = await self.watchlist_repo.get_by_user(db, user_id)
            
            # Get admin watchlists (accessible to all users)
            admin_watchlists = await self.watchlist_repo.get_admin_watchlists(db)
            
            # Format and combine
            all_watchlists = []
            
            for watchlist in personal_watchlists + admin_watchlists:
                watchlist_data = {
                    "id": watchlist.id,
                    "name": watchlist.name,
                    "type": watchlist.type,
                    "tier": watchlist.tier,
                    "current_items": watchlist.current_items,
                    "max_items": watchlist.max_items,
                    "is_active": watchlist.is_active,
                    "created_at": watchlist.created_at.isoformat(),
                    "updated_at": watchlist.updated_at.isoformat() if watchlist.updated_at else None
                }
                all_watchlists.append(watchlist_data)
            
            return all_watchlists
            
        except Exception as e:
            self.logger.error(f"Error fetching user watchlists: {e}")
            raise
    
    async def get_watchlist_with_performance(
        self, 
        db: AsyncSession, 
        watchlist_id: int, 
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get watchlist with real-time performance data"""
        try:
            # Verify access permissions
            watchlist = await self._verify_watchlist_access(db, watchlist_id, user_id)
            if not watchlist:
                return None
            
            # Get watchlist items with performance data
            items = await self.watchlist_item_repo.get_with_performance(db, watchlist_id)
            
            # Calculate aggregate performance
            performance_summary = await self._calculate_watchlist_performance(items)
            
            watchlist_data = {
                "id": watchlist.id,
                "name": watchlist.name,
                "type": watchlist.type,
                "tier": watchlist.tier,
                "items": [
                    {
                        "id": item.id,
                        "crypto_id": item.crypto_id,
                        "symbol": item.crypto.symbol,
                        "name": item.crypto.name,
                        "current_price": float(item.crypto.current_price) if item.crypto.current_price else 0.0,
                        "performance_24h": item.performance_24h,
                        "ai_confidence": item.ai_confidence,
                        "risk_level": item.risk_level,
                        "tier": item.tier,
                        "priority_order": item.priority_order,
                        "last_analysis": item.last_analysis.isoformat() if item.last_analysis else None,
                        "status": item.status
                    }
                    for item in items
                ],
                "performance_summary": performance_summary,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return watchlist_data
            
        except Exception as e:
            self.logger.error(f"Error fetching watchlist with performance: {e}")
            raise
    
    async def add_to_watchlist(
        self, 
        db: AsyncSession, 
        watchlist_id: int, 
        crypto_id: int, 
        tier: str,
        admin_user_id: int
    ) -> Dict[str, Any]:
        """Add cryptocurrency to watchlist (Admin only)"""
        try:
            # Verify admin permissions
            await self._verify_admin_permissions(db, admin_user_id)
            
            # Verify watchlist exists and has capacity
            watchlist = await self.watchlist_repo.get(db, watchlist_id)
            if not watchlist:
                raise ValueError("Watchlist not found")
            
            if watchlist.current_items >= watchlist.max_items:
                raise ValueError("Watchlist is at maximum capacity")
            
            # Check if crypto already in watchlist
            existing_item = await self.watchlist_item_repo.get_by_crypto(
                db, watchlist_id, crypto_id
            )
            if existing_item:
                raise ValueError("Cryptocurrency already in watchlist")
            
            # Create watchlist item
            from app.schemas.layer3 import WatchlistItemCreate
            item_data = WatchlistItemCreate(
                watchlist_id=watchlist_id,
                crypto_id=crypto_id,
                tier=tier,
                priority_order=watchlist.current_items + 1,
                status="active"
            )
            
            item = await self.watchlist_item_repo.create(db, item_data)
            
            # Update watchlist current_items count
            watchlist.current_items += 1
            await db.commit()
            
            # Log admin action
            await self._log_admin_action(
                db, admin_user_id, "add_to_watchlist", 
                {"watchlist_id": watchlist_id, "crypto_id": crypto_id, "tier": tier}
            )
            
            # Trigger real-time update
            await self._publish_watchlist_update(watchlist_id, "item_added")
            
            return {
                "success": True,
                "item_id": item.id,
                "message": f"Added to {tier} watchlist"
            }
            
        except Exception as e:
            self.logger.error(f"Error adding to watchlist: {e}")
            raise
    
    async def get_ai_suggestions(
        self, 
        db: AsyncSession, 
        status: str = "pending",
        limit: int = 50,
        confidence_min: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get AI suggestions for watchlist management"""
        try:
            filters = {
                "status": status,
                "confidence_min": confidence_min
            }
            
            suggestions = await self.suggestion_repo.get_multi_filtered(
                db, filters=filters, limit=limit
            )
            
            suggestions_data = []
            for suggestion in suggestions:
                suggestion_data = {
                    "id": suggestion.id,
                    "crypto_id": suggestion.crypto_id,
                    "crypto_symbol": suggestion.crypto.symbol if suggestion.crypto else "Unknown",
                    "crypto_name": suggestion.crypto.name if suggestion.crypto else "Unknown",
                    "suggestion_type": suggestion.suggestion_type,
                    "confidence_score": float(suggestion.confidence_score),
                    "ai_reasoning": suggestion.ai_reasoning or {},
                    "supporting_data": suggestion.supporting_data or {},
                    "performance_metrics": suggestion.performance_metrics or {},
                    "status": suggestion.status,
                    "suggested_at": suggestion.suggested_at.isoformat(),
                    "expires_at": suggestion.expires_at.isoformat() if suggestion.expires_at else None,
                    "priority": self._calculate_suggestion_priority(suggestion)
                }
                suggestions_data.append(suggestion_data)
            
            # Sort by priority and confidence
            suggestions_data.sort(
                key=lambda x: (x["priority"], x["confidence_score"]), 
                reverse=True
            )
            
            return suggestions_data
            
        except Exception as e:
            self.logger.error(f"Error fetching AI suggestions: {e}")
            raise
    
    async def review_suggestion(
        self, 
        db: AsyncSession, 
        suggestion_id: int, 
        decision: str, 
        review_notes: str,
        admin_user_id: int
    ) -> Dict[str, Any]:
        """Review AI suggestion (Admin only)"""
        try:
            # Verify admin permissions
            await self._verify_admin_permissions(db, admin_user_id)
            
            # Get suggestion
            suggestion = await self.suggestion_repo.get(db, suggestion_id)
            if not suggestion:
                raise ValueError("Suggestion not found")
            
            if suggestion.status != "pending":
                raise ValueError("Suggestion already reviewed")
            
            # Create review record
            from app.schemas.layer3 import SuggestionReviewCreate
            review_data = SuggestionReviewCreate(
                suggestion_id=suggestion_id,
                reviewer_id=admin_user_id,
                decision=decision,
                review_notes=review_notes
            )
            
            from app.repositories.layer3_repository import SuggestionReviewRepository
            review_repo = SuggestionReviewRepository()
            review = await review_repo.create(db, review_data)
            
            # Update suggestion status
            suggestion.status = "approved" if decision == "approve" else decision
            suggestion.reviewed_by = admin_user_id
            suggestion.reviewed_at = datetime.utcnow()
            
            # If approved, execute the suggestion
            if decision == "approve":
                await self._execute_approved_suggestion(db, suggestion, admin_user_id)
            
            await db.commit()
            
            # Log admin action
            await self._log_admin_action(
                db, admin_user_id, "review_suggestion",
                {
                    "suggestion_id": suggestion_id, 
                    "decision": decision,
                    "crypto_symbol": suggestion.crypto.symbol if suggestion.crypto else "Unknown"
                }
            )
            
            return {
                "success": True,
                "review_id": review.id,
                "decision": decision,
                "executed": decision == "approve"
            }
            
        except Exception as e:
            self.logger.error(f"Error reviewing suggestion: {e}")
            raise
    
    # Private helper methods
    async def _verify_watchlist_access(
        self, 
        db: AsyncSession, 
        watchlist_id: int, 
        user_id: int
    ) -> Optional[Any]:
        """Verify user has access to watchlist"""
        watchlist = await self.watchlist_repo.get(db, watchlist_id)
        if not watchlist:
            return None
        
        # Admin watchlists are accessible to all users
        if watchlist.type == "admin":
            return watchlist
        
        # Personal watchlists only accessible to owner
        if watchlist.user_id == user_id:
            return watchlist
        
        return None
    
    async def _verify_admin_permissions(self, db: AsyncSession, user_id: int):
        """Verify user has admin permissions"""
        from app.repositories.user_repository import UserRepository
        
        user_repo = UserRepository()
        user = await user_repo.get(db, user_id)
        
        if not user or not user.is_superuser:
            raise ValueError("Admin permissions required")
    
    async def _calculate_watchlist_performance(
        self, 
        items: List[Any]
    ) -> Dict[str, Any]:
        """Calculate aggregate watchlist performance metrics"""
        if not items:
            return {
                "total_items": 0,
                "avg_performance_24h": 0.0,
                "best_performer": None,
                "worst_performer": None,
                "high_confidence_count": 0
            }
        
        performances = [item.performance_24h for item in items if item.performance_24h]
        
        best_item = max(items, key=lambda x: x.performance_24h or -100)
        worst_item = min(items, key=lambda x: x.performance_24h or 100)
        
        return {
            "total_items": len(items),
            "avg_performance_24h": sum(performances) / len(performances) if performances else 0.0,
            "best_performer": {
                "symbol": best_item.crypto.symbol,
                "performance": best_item.performance_24h
            } if best_item.performance_24h else None,
            "worst_performer": {
                "symbol": worst_item.crypto.symbol,
                "performance": worst_item.performance_24h
            } if worst_item.performance_24h else None,
            "high_confidence_count": sum(1 for item in items if (item.ai_confidence or 0) >= 0.8)
        }
    
    def _calculate_suggestion_priority(self, suggestion: Any) -> int:
        """Calculate suggestion priority score"""
        priority = 0
        
        # High confidence suggestions get higher priority
        if suggestion.confidence_score >= 0.9:
            priority += 10
        elif suggestion.confidence_score >= 0.8:
            priority += 7
        elif suggestion.confidence_score >= 0.7:
            priority += 5
        
        # Tier 1 additions get higher priority
        if suggestion.suggestion_type == "add_tier1":
            priority += 8
        elif suggestion.suggestion_type == "promote_to_tier1":
            priority += 6
        
        # Time sensitivity
        if suggestion.expires_at:
            time_left = (suggestion.expires_at - datetime.utcnow()).days
            if time_left <= 1:
                priority += 5  # Urgent
            elif time_left <= 3:
                priority += 3
        
        return priority
    
    async def _execute_approved_suggestion(
        self, 
        db: AsyncSession, 
        suggestion: Any, 
        admin_user_id: int
    ):
        """Execute approved suggestion automatically"""
        try:
            if suggestion.suggestion_type == "add_tier1":
                # Add to tier 1 watchlist
                tier1_watchlist = await self.watchlist_repo.get_tier1_admin_watchlist(db)
                if tier1_watchlist:
                    await self.add_to_watchlist(
                        db, tier1_watchlist.id, suggestion.crypto_id, "tier1", admin_user_id
                    )
            
            elif suggestion.suggestion_type == "add_tier2":
                # Add to tier 2 watchlist
                tier2_watchlist = await self.watchlist_repo.get_tier2_admin_watchlist(db)
                if tier2_watchlist:
                    await self.add_to_watchlist(
                        db, tier2_watchlist.id, suggestion.crypto_id, "tier2", admin_user_id
                    )
            
            elif suggestion.suggestion_type == "promote_to_tier1":
                # Move from tier 2 to tier 1
                await self._promote_to_tier1(db, suggestion.crypto_id, admin_user_id)
            
        except Exception as e:
            self.logger.error(f"Error executing approved suggestion: {e}")
            # Don't re-raise as the review was successful
    
    async def _log_admin_action(
        self, 
        db: AsyncSession, 
        admin_user_id: int, 
        action: str, 
        details: Dict[str, Any]
    ):
        """Log admin action for audit trail"""
        from app.repositories.admin_repository import AdminActionLogRepository
        from app.schemas.admin import AdminActionLogCreate
        
        log_repo = AdminActionLogRepository()
        log_data = AdminActionLogCreate(
            admin_user_id=admin_user_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        await log_repo.create(db, log_data)
    
    async def _publish_watchlist_update(self, watchlist_id: int, update_type: str):
        """Publish watchlist update to real-time systems"""
        from app.core.events import EventPublisher
        
        publisher = EventPublisher()
        await publisher.publish_layer3_update({
            "type": "watchlist_update",
            "watchlist_id": watchlist_id,
            "update_type": update_type,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

# 🗓️ **روز 25: State Management Strategy**

## 🗄️ **Frontend State Management with Zustand**

```typescript
// =============================================
// STATE MANAGEMENT ARCHITECTURE
// Zustand + TypeScript + Persistent Storage
// =============================================

// stores/types.ts - State type definitions
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'professional' | 'casual';
  is_active: boolean;
  is_superuser: boolean;
}

export interface MarketRegime {
  regime: 'bull' | 'bear' | 'neutral' | 'volatile';
  confidence: number;
  risk_level: 'low' | 'medium' | 'high' | 'extreme';
  last_updated: string;
}

export interface TradingSignal {
  id: number;
  crypto_id: number;
  symbol: string;
  signal_type: 'long' | 'short';
  entry_price: number;
  target_price: number;
  stop_loss: number;
  confidence_score: number;
  risk_level: string;
  generated_at: string;
  expires_at: string;
}

export interface AISuggestion {
  id: number;
  crypto_id: number;
  crypto_symbol: string;
  suggestion_type: string;
  confidence_score: number;
  ai_reasoning: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected';
  suggested_at: string;
}

export interface Watchlist {
  id: number;
  name: string;
  type: 'admin' | 'personal';
  tier: 'tier1' | 'tier2';
  current_items: number;
  max_items: number;
  items?: WatchlistItem[];
}

export interface WatchlistItem {
  id: number;
  crypto_id: number;
  symbol: string;
  name: string;
  current_price: number;
  performance_24h: number;
  ai_confidence: number;
  risk_level: string;
  tier: string;
}

// =============================================
// AUTHENTICATION STORE
// =============================================

// stores/authStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { cryptoAPI } from '@/services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        
        login: async (email: string, password: string) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await cryptoAPI.login({ email, password });
            
            if (response.success) {
              const { user, access_token } = response.data;
              
              set({
                user,
                token: access_token,
                isAuthenticated: true,
                isLoading: false
              });
              
              // Store token for API requests
              localStorage.setItem('auth_token', access_token);
              
              return true;
            }
            
            set({ 
              error: 'Login failed', 
              isLoading: false 
            });
            return false;
            
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Login failed',
              isLoading: false 
            });
            return false;
          }
        },
        
        logout: () => {
          localStorage.removeItem('auth_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            error: null
          });
        },
        
        checkAuthStatus: async () => {
          const token = localStorage.getItem('auth_token');
          
          if (!token) {
            set({ isAuthenticated: false });
            return;
          }
          
          try {
            const response = await cryptoAPI.getCurrentUser();
            
            if (response.success) {
              set({
                user: response.data,
                token,
                isAuthenticated: true
              });
            } else {
              // Token is invalid
              get().logout();
            }
          } catch (error) {
            get().logout();
          }
        },
        
        updateUser: (userData: Partial<User>) => {
          set(state => ({
            user: state.user ? { ...state.user, ...userData } : null
          }));
        },
        
        clearError: () => set({ error: null })
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          token: state.token,
          isAuthenticated: state.isAuthenticated
        })
      }
    ),
    {
      name: 'auth-store'
    }
  )
);

// =============================================
// MARKET DATA STORE
// =============================================

// stores/marketStore.ts
interface MarketState {
  // Market regime data
  marketRegime: MarketRegime | null;
  marketSentiment: any | null;
  dominanceData: any | null;
  
  // Sector data
  sectors: any[] | null;
  sectorRotation: any | null;
  
  // Loading states
  isLoadingRegime: boolean;
  isLoadingSentiment: boolean;
  isLoadingSectors: boolean;
  
  // Error states
  regimeError: string | null;
  sentimentError: string | null;
  sectorsError: string | null;
  
  // Actions
  fetchMarketRegime: () => Promise<void>;
  fetchMarketSentiment: () => Promise<void>;
  fetchSectors: () => Promise<void>;
  updateMarketRegime: (regime: MarketRegime) => void;
  clearErrors: () => void;
  
  // Real-time updates
  handleRealtimeUpdate: (update: any) => void;
}

export const useMarketStore = create<MarketState>()(
  devtools(
    (set, get) => ({
      marketRegime: null,
      marketSentiment: null,
      dominanceData: null,
      sectors: null,
      sectorRotation: null,
      
      isLoadingRegime: false,
      isLoadingSentiment: false,
      isLoadingSectors: false,
      
      regimeError: null,
      sentimentError: null,
      sectorsError: null,
      
      fetchMarketRegime: async () => {
        set({ isLoadingRegime: true, regimeError: null });
        
        try {
          const response = await cryptoAPI.getMarketRegime();
          
          if (response.success) {
            set({
              marketRegime: response.data,
              isLoadingRegime: false
            });
          } else {
            set({
              regimeError: 'Failed to fetch market regime',
              isLoadingRegime: false
            });
          }
        } catch (error) {
          set({
            regimeError: error instanceof Error ? error.message : 'Unknown error',
            isLoadingRegime: false
          });
        }
      },
      
      fetchMarketSentiment: async () => {
        set({ isLoadingSentiment: true, sentimentError: null });
        
        try {
          const response = await cryptoAPI.getMarketSentiment();
          
          if (response.success) {
            set({
              marketSentiment: response.data,
              isLoadingSentiment: false
            });
          }
        } catch (error) {
          set({
            sentimentError: error instanceof Error ? error.message : 'Unknown error',
            isLoadingSentiment: false
          });
        }
      },
      
      fetchSectors: async () => {
        set({ isLoadingSectors: true, sectorsError: null });
        
        try {
          const [sectorsResponse, rotationResponse] = await Promise.all([
            cryptoAPI.getAllSectors(),
            cryptoAPI.getSectorRotation()
          ]);
          
          set({
            sectors: sectorsResponse.success ? sectorsResponse.data : null,
            sectorRotation: rotationResponse.success ? rotationResponse.data : null,
            isLoadingSectors: false
          });
        } catch (error) {
          set({
            sectorsError: error instanceof Error ? error.message : 'Unknown error',
            isLoadingSectors: false
          });
        }
      },
      
      updateMarketRegime: (regime: MarketRegime) => {
        set({ marketRegime: regime });
      },
      
      clearErrors: () => {
        set({
          regimeError: null,
          sentimentError: null,
          sectorsError: null
        });
      },
      
      handleRealtimeUpdate: (update: any) => {
        switch (update.type) {
          case 'regime_update':
            set({
              marketRegime: {
                regime: update.regime,
                confidence: update.confidence,
                risk_level: update.risk_level,
                last_updated: update.timestamp
              }
            });
            break;
            
          case 'sentiment_update':
            set({ marketSentiment: update.data });
            break;
            
          case 'sector_update':
            set(state => ({
              sectors: state.sectors?.map(sector => 
                sector.id === update.sector_id 
                  ? { ...sector, ...update.data }
                  : sector
              )
            }));
            break;
        }
      }
    }),
    {
      name: 'market-store'
    }
  )
);

// =============================================
// SIGNALS STORE
// =============================================

// stores/signalsStore.ts
interface SignalsState {
  activeSignals: TradingSignal[];
  signalHistory: TradingSignal[];
  executedSignals: any[];
  
  isLoadingSignals: boolean;
  isExecuting: Record<number, boolean>;
  
  signalsError: string | null;
  executionErrors: Record<number, string>;
  
  // New signal notifications
  newSignalAlert: TradingSignal | null;
  
  // Actions
  fetchActiveSignals: () => Promise<void>;
  executeSignal: (signalId: number, executionData: any) => Promise<boolean>;
  dismissSignalAlert: () => void;
  handleNewSignal: (signal: TradingSignal) => void;
  updateSignalStatus: (signalId: number, status: string) => void;
  clearExecutionError: (signalId: number) => void;
}

export const useSignalsStore = create<SignalsState>()(
  devtools(
    (set, get) => ({
      activeSignals: [],
      signalHistory: [],
      executedSignals: [],
      
      isLoadingSignals: false,
      isExecuting: {},
      
      signalsError: null,
      executionErrors: {},
      
      newSignalAlert: null,
      
      fetchActiveSignals: async () => {
        set({ isLoadingSignals: true, signalsError: null });
        
        try {
          const response = await cryptoAPI.getActiveSignals();
          
          if (response.success) {
            set({
              activeSignals: response.data,
              isLoadingSignals: false
            });
          }
        } catch (error) {
          set({
            signalsError: error instanceof Error ? error.message : 'Unknown error',
            isLoadingSignals: false
          });
        }
      },
      
      executeSignal: async (signalId: number, executionData: any) => {
        set(state => ({
          isExecuting: { ...state.isExecuting, [signalId]: true },
          executionErrors: { ...state.executionErrors, [signalId]: '' }
        }));
        
        try {
          const response = await cryptoAPI.executeSignal(signalId, executionData);
          
          if (response.success) {
            // Update signal status
            set(state => ({
              activeSignals: state.activeSignals.map(signal =>
                signal.id === signalId 
                  ? { ...signal, status: 'executed' }
                  : signal
              ),
              executedSignals: [...state.executedSignals, response.data],
              isExecuting: { ...state.isExecuting, [signalId]: false }
            }));
            
            // Show success notification
            if ('Notification' in window && Notification.permission === 'granted') {
              new Notification('Signal Executed', {
                body: `Successfully executed signal for ${executionData.symbol}`,
                icon: '/icon-192x192.png'
              });
            }
            
            return true;
          }
          
          return false;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Execution failed';
          
          set(state => ({
            executionErrors: { ...state.executionErrors, [signalId]: errorMessage },
            isExecuting: { ...state.isExecuting, [signalId]: false }
          }));
          
          return false;
        }
      },
      
      dismissSignalAlert: () => {
        set({ newSignalAlert: null });
      },
      
      handleNewSignal: (signal: TradingSignal) => {
        set(state => ({
          activeSignals: [...state.activeSignals, signal],
          newSignalAlert: signal
        }));
        
        // Auto-dismiss alert after 5 seconds
        setTimeout(() => {
          get().dismissSignalAlert();
        }, 5000);
      },
      
      updateSignalStatus: (signalId: number, status: string) => {
        set(state => ({
          activeSignals: state.activeSignals.map(signal =>
            signal.id === signalId ? { ...signal, status } : signal
          )
        }));
      },
      
      clearExecutionError: (signalId: number) => {
        set(state => ({
          executionErrors: { ...state.executionErrors, [signalId]: '' }
        }));
      }
    }),
    {
      name: 'signals-store'
    }
  )
);

// =============================================
// ADMIN STORE (Admin-only functionality)
// =============================================

// stores/adminStore.ts
interface AdminState {
  // AI Suggestions management
  aiSuggestions: AISuggestion[];
  suggestionsLoading: boolean;
  suggestionsError: string | null;
  
  // System health monitoring
  systemHealth: any | null;
  healthLoading: boolean;
  
  // Watchlist management
  adminWatchlists: Watchlist[];
  watchlistsLoading: boolean;
  
  // Actions
  fetchAISuggestions: () => Promise<void>;
  reviewSuggestion: (suggestionId: number, decision: string, notes?: string) => Promise<boolean>;
  fetchSystemHealth: () => Promise<void>;
  fetchAdminWatchlists: () => Promise<void>;
  addToWatchlist: (watchlistId: number, cryptoId: number, tier: string) => Promise<boolean>;
  
  // Bulk actions
  bulkApproveSuggestions: (suggestionIds: number[]) => Promise<void>;
  
  // Real-time updates
  handleAdminUpdate: (update: any) => void;
}

export const useAdminStore = create<AdminState>()(
  devtools(
    (set, get) => ({
      aiSuggestions: [],
      suggestionsLoading: false,
      suggestionsError: null,
      
      systemHealth: null,
      healthLoading: false,
      
      adminWatchlists: [],
      watchlistsLoading: false,
      
      fetchAISuggestions: async () => {
        set({ suggestionsLoading: true, suggestionsError: null });
        
        try {
          const response = await cryptoAPI.getAISuggestions();
          
          if (response.success) {
            set({
              aiSuggestions: response.data,
              suggestionsLoading: false
            });
          }
        } catch (error) {
          set({
            suggestionsError: error instanceof Error ? error.message : 'Unknown error',
            suggestionsLoading: false
          });
        }
      },
      
      reviewSuggestion: async (suggestionId: number, decision: string, notes = '') => {
        try {
          const response = await cryptoAPI.reviewSuggestion(suggestionId, {
            decision,
            review_notes: notes
          });
          
          if (response.success) {
            // Update suggestion in store
            set(state => ({
              aiSuggestions: state.aiSuggestions.map(suggestion =>
                suggestion.id === suggestionId
                  ? { ...suggestion, status: decision === 'approve' ? 'approved' : decision }
                  : suggestion
              )
            }));
            
            return true;
          }
          
          return false;
        } catch (error) {
          console.error('Review failed:', error);
          return false;
        }
      },
      
      fetchSystemHealth: async () => {
        set({ healthLoading: true });
        
        try {
          const response = await cryptoAPI.getSystemHealth();
          
          if (response.success) {
            set({
              systemHealth: response.data,
              healthLoading: false
            });
          }
        } catch (error) {
          set({ healthLoading: false });
        }
      },
      
      fetchAdminWatchlists: async () => {
        set({ watchlistsLoading: true });
        
        try {
          const response = await cryptoAPI.getAdminWatchlists();
          
          if (response.success) {
            set({
              adminWatchlists: response.data,
              watchlistsLoading: false
            });
          }
        } catch (error) {
          set({ watchlistsLoading: false });
        }
      },
      
      addToWatchlist: async (watchlistId: number, cryptoId: number, tier: string) => {
        try {
          const response = await cryptoAPI.addToWatchlist(watchlistId, {
            crypto_id: cryptoId,
            tier
          });
          
          if (response.success) {
            // Refresh watchlists
            await get().fetchAdminWatchlists();
            return true;
          }
          
          return false;
        } catch (error) {
          console.error('Add to watchlist failed:', error);
          return false;
        }
      },
      
      bulkApproveSuggestions: async (suggestionIds: number[]) => {
        for (const suggestionId of suggestionIds) {
          await get().reviewSuggestion(suggestionId, 'approve', 'Bulk approved');
        }
      },
      
      handleAdminUpdate: (update: any) => {
        switch (update.type) {
          case 'new_suggestion':
            set(state => ({
              aiSuggestions: [...state.aiSuggestions, update.data]
            }));
            break;
            
          case 'suggestion_reviewed':
            set(state => ({
              aiSuggestions: state.aiSuggestions.filter(
                suggestion => suggestion.id !== update.suggestion_id
              )
            }));
            break;
            
          case 'system_health_update':
            set({ systemHealth: update.data });
            break;
        }
      }
    }),
    {
      name: 'admin-store'
    }
  )
);

// =============================================
// UI STATE STORE
// =============================================

// stores/uiStore.ts
interface UIState {
  // Theme
  theme: 'light' | 'dark' | 'system';
  
  // Navigation
  sidebarOpen: boolean;
  currentPage: string;
  
  // Modals & Overlays
  activeModal: string | null;
  modalProps: Record<string, any>;
  
  // Notifications
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: number;
    duration?: number;
  }>;
  
  // Loading states
  globalLoading: boolean;
  loadingMessage: string;
  
  // Mobile
  isMobile: boolean;
  
  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleSidebar: () => void;
  openModal: (modalId: string, props?: Record<string, any>) => void;
  closeModal: () => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  setGlobalLoading: (loading: boolean, message?: string) => void;
  setMobile: (isMobile: boolean) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        theme: 'system',
        sidebarOpen: false,
        currentPage: 'dashboard',
        activeModal: null,
        modalProps: {},
        notifications: [],
        globalLoading: false,
        loadingMessage: '',
        isMobile: false,
        
        setTheme: (theme) => {
          set({ theme });
          
          // Apply theme to document
          const root = document.documentElement;
          if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            root.classList.add('dark');
          } else {
            root.classList.remove('dark');
          }
        },
        
        toggleSidebar: () => {
          set(state => ({ sidebarOpen: !state.sidebarOpen }));
        },
        
        openModal: (modalId: string, props = {}) => {
          set({ 
            activeModal: modalId, 
            modalProps: props 
          });
        },
        
        closeModal: () => {
          set({ 
            activeModal: null, 
            modalProps: {} 
          });
        },
        
        addNotification: (notification) => {
          const id = Math.random
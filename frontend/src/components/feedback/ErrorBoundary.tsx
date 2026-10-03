import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '../buttons/Button';

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  incidentId: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      incidentId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const incidentId = `ERR_${Date.now().toString(36).toUpperCase()}_${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
    return {
      hasError: true,
      error,
      incidentId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // In production, send to structured telemetry / logging collector
    if (typeof console !== 'undefined' && console.error) {
      console.error(
        `[CAREFLOW_ERROR_BOUNDARY] Caught uncaught render exception [Incident: ${this.state.incidentId}]:`,
        error,
        errorInfo
      );
    }
  }

  handleReload = (): void => {
    if (this.props.onReset) {
      this.props.onReset();
    }
    this.setState({ hasError: false, error: null, incidentId: '' });
  };

  handleHardRefresh = (): void => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--text-primary)] flex items-center justify-center p-6 selection:bg-[var(--coral-500)] selection:text-white">
          <div className="max-w-md w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xl text-center flex flex-col items-center">
            {/* Pulsing Alert Icon */}
            <div className="w-14 h-14 rounded-2xl bg-[var(--coral-50)] text-[var(--coral-600)] border border-[var(--coral-100)] flex items-center justify-center mb-6 shadow-xs">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--coral-100)] text-[var(--coral-800)] mb-3">
              Application Resilience Notice
            </span>

            <h2 className="font-display text-xl font-bold text-[var(--text-primary)] mb-2">
              Something Unexpected Occurred
            </h2>

            <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
              CAREFlow encountered an unexpected client runtime issue while rendering this view. Your session data and operational records remain intact.
            </p>

            {this.state.incidentId && (
              <div className="w-full mb-6 py-2 px-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-xs font-mono text-[var(--text-muted)] flex items-center justify-between">
                <span>Incident Reference:</span>
                <span className="font-semibold text-[var(--text-primary)] select-all">{this.state.incidentId}</span>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 w-full">
              <Button
                variant="primary"
                size="md"
                className="flex-1 justify-center"
                onClick={this.handleReload}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                Recover View
              </Button>

              <Button
                variant="secondary"
                size="md"
                className="flex-1 justify-center"
                onClick={this.handleHardRefresh}
                leftIcon={<Home className="w-4 h-4" />}
              >
                Return Home
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

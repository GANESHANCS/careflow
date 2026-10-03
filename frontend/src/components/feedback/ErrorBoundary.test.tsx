import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

describe('ErrorBoundary Component', () => {
  // Suppress console.error during expected crash test
  const originalConsoleError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalConsoleError;
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Healthy Application Content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Healthy Application Content')).toBeInTheDocument();
  });

  it('catches render error and displays safe fallback UI with incident reference', () => {
    const ThrowingComponent = () => {
      throw new Error('Simulated React render crash');
    };

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something Unexpected Occurred')).toBeInTheDocument();
    expect(screen.getByText('Application Resilience Notice')).toBeInTheDocument();
    expect(screen.getByText(/Incident Reference:/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /recover view/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /return home/i })).toBeInTheDocument();

    // Ensure raw stack trace or simulated error message is suppressed from user
    expect(screen.queryByText('Simulated React render crash')).not.toBeInTheDocument();
  });

  it('invokes onReset and attempts recovery when clicking Recover View', () => {
    const handleReset = vi.fn();
    let shouldCrash = true;

    const DynamicComponent = () => {
      if (shouldCrash) {
        throw new Error('Render failure');
      }
      return <div>Recovered Application Content</div>;
    };

    render(
      <ErrorBoundary onReset={handleReset}>
        <DynamicComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something Unexpected Occurred')).toBeInTheDocument();

    // Fix the error condition so that on reload it succeeds
    shouldCrash = false;

    const recoverBtn = screen.getByRole('button', { name: /recover view/i });
    fireEvent.click(recoverBtn);

    expect(handleReset).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Recovered Application Content')).toBeInTheDocument();
  });
});

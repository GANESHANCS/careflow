import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';

describe('Feedback Components', () => {
  it('renders EmptyState with custom title and action button', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="NO DATA FOUND"
        description="No test records exist."
        actionText="Reload"
        onAction={handleAction}
      />
    );
    expect(screen.getByText('NO DATA FOUND')).toBeInTheDocument();
    expect(screen.getByText('No test records exist.')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Reload'));
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('renders ErrorState with retry trigger', () => {
    const handleRetry = vi.fn();
    render(<ErrorState title="API Error" message="Failed to load." onRetry={handleRetry} />);
    expect(screen.getByText('API Error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load.')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Try Again'));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';

describe('Feedback Components', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

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

  it('renders ErrorState with incident reference ID and handles copy action', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(
      <ErrorState
        title="Server Error"
        message="Internal issue"
        requestId="req-test-uuid-99"
      />
    );

    expect(screen.getByText('req-test-uuid-99')).toBeInTheDocument();
    expect(screen.getByText('Ref:')).toBeInTheDocument();

    const copyBtn = screen.getByRole('button', { name: /copy incident id/i });
    expect(copyBtn).toBeInTheDocument();

    fireEvent.click(copyBtn);
    expect(writeTextMock).toHaveBeenCalledWith('req-test-uuid-99');

    await waitFor(() => {
      // Button switches from copy icon to check icon
      expect(copyBtn).toBeInTheDocument();
    });
  });
});

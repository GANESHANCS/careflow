import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from './LoginPage';
import { AuthProvider } from '../auth/AuthContext';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    login: vi.fn(),
    getMe: vi.fn(),
    logout: vi.fn(),
  },
  getStoredToken: vi.fn(() => null),
  setStoredToken: vi.fn(),
  removeStoredToken: vi.fn(),
}));

describe('LoginPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form elements correctly', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('CAREFlow Terminal')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your username or email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Terminal/i })).toBeInTheDocument();
  });

  it('displays error message when login fails', async () => {
    (api.login as any).mockRejectedValueOnce(new Error('Incorrect username/email or password'));

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('Enter your username or email'), {
      target: { value: 'wrong_user' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••••••'), {
      target: { value: 'wrong_pass' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign In to Terminal/i }));

    await waitFor(() => {
      expect(screen.getByText('Incorrect username/email or password')).toBeInTheDocument();
    });
  });

  it('calls api.login and succeeds on valid credentials', async () => {
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@careflow.gov.in',
      role: 'ADMIN',
      is_active: true,
      created_at: '2026-08-31T00:00:00Z',
      updated_at: '2026-08-31T00:00:00Z',
    };

    (api.login as any).mockResolvedValueOnce({
      access_token: 'mock_jwt_token',
      token_type: 'bearer',
      user: mockUser,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('Enter your username or email'), {
      target: { value: 'admin' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••••••'), {
      target: { value: 'careflow_admin_dev_2026' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign In to Terminal/i }));

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'careflow_admin_dev_2026',
      });
    });
  });
});

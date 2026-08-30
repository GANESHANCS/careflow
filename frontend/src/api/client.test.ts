import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from './client';

describe('API Client Layer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches health check successfully', async () => {
    const mockHealth = {
      status: 'healthy',
      app_name: 'CAREFlow India',
      version: '0.1.0',
      environment: 'development',
      python_version: '3.12.7',
      database_status: 'healthy',
      timestamp: '2026-08-30T19:40:00+00:00',
      database: { status: 'healthy', engine: 'sqlite', error: null }
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const res = await api.getHealth();
    expect(res.status).toBe('healthy');
    expect(res.app_name).toBe('CAREFlow India');
  });

  it('throws ApiError on failed response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Facility FC_999 not found' }),
    } as Response);

    await expect(api.getFacilityById('FC_999')).rejects.toThrow(ApiError);
  });
});

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

  it('uploads import file successfully with FormData', async () => {
    const mockJob = {
      id: 1,
      job_code: 'JOB_20261003_120000_abc123',
      original_filename: 'hmis_delhi.csv',
      status: 'COMPLETED',
      total_records: 100,
      records_imported: 100,
      records_rejected: 0,
      quality_score: 96.5,
      created_at: '2026-10-03T12:00:00Z',
      updated_at: '2026-10-03T12:00:05Z',
      completed_at: '2026-10-03T12:00:05Z',
      file_size_bytes: 2048,
      mime_type: 'text/csv',
      file_hash: 'hash123',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockJob,
    } as Response);

    const file = new File(['header\nrow1'], 'hmis_delhi.csv', { type: 'text/csv' });
    const res = await api.uploadImportFile(file);

    expect(res.job_code).toBe('JOB_20261003_120000_abc123');
    expect(res.status).toBe('COMPLETED');
    expect(global.fetch).toHaveBeenCalledWith('/api/imports', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData),
    }));
  });

  it('fetches import jobs list and error logs', async () => {
    const mockList = {
      total: 1,
      items: [{
        id: 1,
        job_code: 'JOB_1',
        original_filename: 'test.csv',
        status: 'COMPLETED',
        total_records: 10,
        records_imported: 10,
        records_rejected: 0,
        quality_score: 100,
        created_at: '2026-10-03T12:00:00Z',
        updated_at: '2026-10-03T12:00:00Z',
        completed_at: '2026-10-03T12:00:00Z',
        file_size_bytes: 500,
        mime_type: 'text/csv',
        file_hash: null,
      }],
      page: 1,
      page_size: 50,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockList,
    } as Response);

    const res = await api.getImports({ skip: 0, limit: 10, search: 'test' });
    expect(res.total).toBe(1);
    expect(res.items[0].job_code).toBe('JOB_1');
  });
});


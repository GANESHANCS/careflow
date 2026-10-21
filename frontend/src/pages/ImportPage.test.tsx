import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ImportPage } from './ImportPage';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { ImportJob, ImportJobListResponse, ImportJobQualityResponse, ImportErrorLogListResponse } from '../api/types';

vi.mock('../api/client', () => ({
  api: {
    getImports: vi.fn(),
    uploadImportFile: vi.fn(),
    getImportDetail: vi.fn(),
    getImportQuality: vi.fn(),
    getImportErrors: vi.fn(),
    rollbackImport: vi.fn(),
    getImportJobStatus: vi.fn(),
    retryImport: vi.fn(),
    cancelImport: vi.fn(),
    getImportBatches: vi.fn(),
    getImportBatchDetail: vi.fn(),
    triggerDirectoryScan: vi.fn(),
    retryImportBatch: vi.fn(),
    cancelImportBatch: vi.fn(),
  },
}));

vi.mock('../auth/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('ImportPage & Phase 7G Workspace', () => {
  const mockJobs: ImportJob[] = [
    {
      id: 1,
      job_code: 'JOB_20261003_100000_111111',
      original_filename: 'mohfw_delhi_2024.csv',
      file_size_bytes: 1048576,
      mime_type: 'text/csv',
      file_hash: 'hash_abc',
      status: 'COMPLETED',
      total_records: 500,
      records_imported: 500,
      records_rejected: 0,
      quality_score: 98.4,
      created_at: '2026-10-03T10:00:00Z',
      updated_at: '2026-10-03T10:00:05Z',
      completed_at: '2026-10-03T10:00:05Z',
    },
    {
      id: 2,
      job_code: 'JOB_20261003_110000_222222',
      original_filename: 'mohfw_bihar_warnings.xlsx',
      file_size_bytes: 2097152,
      mime_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      file_hash: 'hash_def',
      status: 'COMPLETED_WITH_WARNINGS',
      total_records: 300,
      records_imported: 280,
      records_rejected: 20,
      quality_score: 82.0,
      created_at: '2026-10-03T11:00:00Z',
      updated_at: '2026-10-03T11:00:08Z',
      completed_at: '2026-10-03T11:00:08Z',
    },
    {
      id: 3,
      job_code: 'JOB_20261003_120000_333333',
      original_filename: 'corrupted_format.csv',
      file_size_bytes: 512,
      mime_type: 'text/csv',
      file_hash: 'hash_bad',
      status: 'FAILED',
      total_records: 0,
      records_imported: 0,
      records_rejected: 0,
      quality_score: null,
      created_at: '2026-10-03T12:00:00Z',
      updated_at: '2026-10-03T12:00:02Z',
      completed_at: null,
    },
  ];

  const mockListResponse: ImportJobListResponse = {
    total: 3,
    items: mockJobs,
    page: 1,
    page_size: 10,
  };

  const mockQualityResponse: ImportJobQualityResponse = {
    job_code: 'JOB_20261003_100000_111111',
    overall_quality_score: 98.4,
    total_issues: 2,
    severity_counts: {
      CRITICAL: 0,
      ERROR: 0,
      WARNING: 1,
      INFO: 1,
    },
    category_scores: {
      completeness: 99.0,
      validity: 98.0,
      consistency: 98.5,
      timeliness: 100.0,
      accuracy: 97.5,
    },
    findings: [
      {
        code: 'TIMELINESS_WARN',
        severity: 'WARNING',
        message: 'Reporting delay of 2 days past monthly cutoff.',
        row: 14,
        sheet: 'Monthly Summary',
      },
      {
        code: 'INFO_ZERO_PRESERVED',
        severity: 'INFO',
        message: 'Explicit 0 preserved as valid count.',
        row: 45,
        sheet: 'OPD Attendances',
      },
    ],
  };

  const mockErrorLogResponse: ImportErrorLogListResponse = {
    total: 2,
    items: [
      {
        id: 101,
        import_job_id: 2,
        source_row: 12,
        source_sheet: 'Data_Sheet',
        error_code: 'OUTLIER_OBSERVATION',
        severity: 'WARNING',
        message: 'Inpatient admission value 950 exceeds 3x standard deviation.',
        created_at: '2026-10-03T11:00:05Z',
      },
      {
        id: 102,
        import_job_id: 2,
        source_row: 44,
        source_sheet: 'Data_Sheet',
        error_code: 'INVALID_FACILITY_CODE',
        severity: 'ERROR',
        message: 'Facility code FAC_INVALID does not map to master directory.',
        created_at: '2026-10-03T11:00:06Z',
      },
    ],
    page: 1,
    page_size: 20,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({
      user: {
        id: 1,
        username: 'admin_user',
        email: 'admin@careflow.gov.in',
        role: 'ADMIN',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
    });
    (api.getImports as any).mockResolvedValue(mockListResponse);
    (api.getImportQuality as any).mockResolvedValue(mockQualityResponse);
    (api.getImportErrors as any).mockResolvedValue(mockErrorLogResponse);
    (api.getImportBatches as any).mockResolvedValue({
      total: 1,
      items: [
        {
          id: 1,
          batch_code: 'BATCH_TEST_001',
          source: 'DIRECTORY_WATCHER',
          status: 'COMPLETED',
          total_files: 2,
          processed_files: 2,
          successful_files: 2,
          failed_files: 0,
          total_records: 100,
          imported_records: 100,
          rejected_records: 0,
          created_at: '2026-10-21T10:00:00Z',
          updated_at: '2026-10-21T10:01:00Z',
          completed_at: '2026-10-21T10:01:00Z',
          progress_percent: 100,
        },
      ],
      page: 1,
      page_size: 50,
    });
    (api.getImportBatchDetail as any).mockResolvedValue({
      id: 1,
      batch_code: 'BATCH_TEST_001',
      source: 'DIRECTORY_WATCHER',
      status: 'COMPLETED',
      total_files: 1,
      processed_files: 1,
      successful_files: 1,
      failed_files: 0,
      total_records: 50,
      imported_records: 50,
      rejected_records: 0,
      created_at: '2026-10-21T10:00:00Z',
      updated_at: '2026-10-21T10:01:00Z',
      progress_percent: 100,
      import_jobs: [mockJobs[0]],
    });
    (api.triggerDirectoryScan as any).mockResolvedValue({
      files_discovered: 2,
      jobs_created: 2,
      batch_code: 'BATCH_NEW_002',
      message: 'Directory scan completed: 2 file(s) evaluated, 2 job(s) created.',
    });
  });

  // 1. Render check
  it('renders the ImportPage header and workspace components', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    expect(screen.getByText('HMIS Ingestion & Quality Audit Workspace')).toBeInTheDocument();
    expect(screen.getByText('HMIS Spreadsheet Ingestion')).toBeInTheDocument();
    expect(screen.getByText('Ingestion History & Audit Registry')).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getImports).toHaveBeenCalled();
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });
  });

  // 2. Upload control available to ADMIN
  it('enables file upload controls for ADMIN role', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 1, username: 'admin', role: 'ADMIN', is_active: true },
      isAuthenticated: true,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Drag & drop your HMIS file here, or click to browse')).toBeInTheDocument();
      expect(screen.queryByText(/Read-Only Access Restricted/i)).not.toBeInTheDocument();
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });
  });

  // 3. Upload control available to ANALYST
  it('enables file upload controls for ANALYST role', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 2, username: 'analyst', role: 'ANALYST', is_active: true },
      isAuthenticated: true,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Drag & drop your HMIS file here, or click to browse')).toBeInTheDocument();
      expect(screen.queryByText(/Read-Only Access Restricted/i)).not.toBeInTheDocument();
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });
  });

  // 4. Upload control unavailable to VIEWER
  it('disables file upload controls and displays explanation for VIEWER role', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 3, username: 'viewer', role: 'VIEWER', is_active: true },
      isAuthenticated: true,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Read-Only Access Restricted/i)).toBeInTheDocument();
      expect(screen.getByText(/File upload disabled for your role/i)).toBeInTheDocument();
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });
  });

  // 5. Invalid file type rejected
  it('rejects unsupported file formats client-side', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    const input = screen.getByTestId('hmis-file-input');
    const invalidFile = new File(['%PDF fake'], 'report.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    await waitFor(() => {
      expect(screen.getByText(/Unsupported file format/i)).toBeInTheDocument();
    });
    expect(api.uploadImportFile).not.toHaveBeenCalled();
  });

  // 6. Oversized file rejected
  it('rejects oversized files (> 50 MB) client-side', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    const input = screen.getByTestId('hmis-file-input');
    const oversizedFile = new File(['data'], 'huge_file.csv', { type: 'text/csv' });
    Object.defineProperty(oversizedFile, 'size', { value: 55 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [oversizedFile] } });

    await waitFor(() => {
      expect(screen.getByText(/File exceeds maximum allowed limit of 50 MB/i)).toBeInTheDocument();
    });
    expect(api.uploadImportFile).not.toHaveBeenCalled();
  });

  // 7. Successful upload invokes API client
  it('invokes api.uploadImportFile upon submitting a valid spreadsheet', async () => {
    const newJob: ImportJob = {
      id: 4,
      job_code: 'JOB_NEW_999',
      original_filename: 'fresh_data.csv',
      file_size_bytes: 4096,
      mime_type: 'text/csv',
      file_hash: 'new_hash',
      status: 'COMPLETED',
      total_records: 120,
      records_imported: 120,
      records_rejected: 0,
      quality_score: 95.0,
      created_at: '2026-10-03T14:00:00Z',
      updated_at: '2026-10-03T14:00:05Z',
      completed_at: '2026-10-03T14:00:05Z',
    };
    (api.uploadImportFile as any).mockResolvedValueOnce(newJob);

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    const input = screen.getByTestId('hmis-file-input');
    const validFile = new File(['header1,header2\nval1,val2'], 'fresh_data.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [validFile] } });

    await waitFor(() => {
      expect(screen.getByText('fresh_data.csv')).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole('button', { name: /Begin Ingestion/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.uploadImportFile).toHaveBeenCalledWith(validFile);
      expect(screen.getByText(/Ingestion Successful/i)).toBeInTheDocument();
      expect(screen.getByText('JOB_NEW_999')).toBeInTheDocument();
    });
  });

  // 8. Import history renders
  it('renders paginated import history with file names and record metrics', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
      expect(screen.getByText('mohfw_bihar_warnings.xlsx')).toBeInTheDocument();
      expect(screen.getByText('corrupted_format.csv')).toBeInTheDocument();
      expect(screen.getByText('JOB_20261003_100000_111111')).toBeInTheDocument();
    });
  });

  // 9. Status badges render correctly
  it('renders correct status badges (COMPLETED, WARNINGS, FAILED)', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('WARNINGS')).toBeInTheDocument();
      expect(screen.getByText('FAILED')).toBeInTheDocument();
    });
  });

  // 10. Quality view renders backend values
  it('opens quality modal and renders backend quality score and findings', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });

    const qualityButtons = screen.getAllByRole('button', { name: /Quality/i });
    fireEvent.click(qualityButtons[0]);

    await waitFor(() => {
      expect(api.getImportQuality).toHaveBeenCalledWith('JOB_20261003_100000_111111');
      const dialog = screen.getByRole('dialog');
      expect(within(dialog).getByText('Data Quality Audit Report')).toBeInTheDocument();
      expect(within(dialog).getByText('98.4%')).toBeInTheDocument();
      expect(within(dialog).getByText('High Confidence Dataset')).toBeInTheDocument();
      expect(within(dialog).getByText('TIMELINESS_WARN')).toBeInTheDocument();
      expect(within(dialog).getByText(/Reporting delay of 2 days/i)).toBeInTheDocument();
    });

    // Dismiss modal
    const dismissBtn = screen.getByRole('button', { name: /Dismiss/i });
    fireEvent.click(dismissBtn);

    await waitFor(() => {
      expect(screen.queryByText('Data Quality Audit Report')).not.toBeInTheDocument();
    });
  });

  // 11. Error viewer renders backend errors
  it('opens diagnostic error log viewer and renders backend error records', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_bihar_warnings.xlsx')).toBeInTheDocument();
    });

    const logButtons = screen.getAllByRole('button', { name: /Logs/i });
    fireEvent.click(logButtons[1]); // second job

    await waitFor(() => {
      expect(api.getImportErrors).toHaveBeenCalledWith('JOB_20261003_110000_222222', expect.any(Object));
      expect(screen.getByText('Import Diagnostic & Audit Error Logs')).toBeInTheDocument();
      expect(screen.getByText('OUTLIER_OBSERVATION')).toBeInTheDocument();
      expect(screen.getByText(/Inpatient admission value 950/i)).toBeInTheDocument();
      expect(screen.getByText('INVALID_FACILITY_CODE')).toBeInTheDocument();
    });
  });

  // 12. Loading / Empty / Error states render appropriately
  it('renders empty state when no import jobs exist', async () => {
    (api.getImports as any).mockResolvedValueOnce({
      total: 0,
      items: [],
      page: 1,
      page_size: 10,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No HMIS Import Jobs Found')).toBeInTheDocument();
    });
  });

  it('renders error state when api fails', async () => {
    (api.getImports as any).mockRejectedValueOnce(new Error('Internal network outage'));

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Unable to Retrieve Import History')).toBeInTheDocument();
      expect(screen.getByText('Internal network outage')).toBeInTheDocument();
    });
  });

  // 13. Safe Rollback integration tests (Phase 8.2)
  it('shows Rollback action button for ADMIN role on completed jobs and hides it for non-admin', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    });

    const { unmount } = render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });

    // Admin should see Rollback button for completed jobs
    const rollbackButtons = screen.getAllByRole('button', { name: /Rollback/i });
    expect(rollbackButtons.length).toBeGreaterThan(0);

    unmount();

    // Re-render as ANALYST
    (useAuth as any).mockReturnValue({
      user: { id: 2, username: 'analyst', role: 'ANALYST' },
      isAuthenticated: true,
      isLoading: false,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });

    // Analyst should NOT see Rollback button
    expect(screen.queryByRole('button', { name: /Rollback/i })).not.toBeInTheDocument();
  });

  it('opens confirmation modal and executes rollbackImport successfully on confirm', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    });

    (api.rollbackImport as any).mockResolvedValueOnce({
      job_code: 'JOB_20261003_100000_111111',
      status: 'ROLLED_BACK',
      records_deleted: 500,
      records_restored: 0,
      records_unchanged: 0,
      rolled_back_at: '2026-10-10T12:00:00Z',
      rolled_back_by: 'admin',
      message: 'Successfully rolled back import job.',
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });

    const rollbackButtons = screen.getAllByRole('button', { name: /Rollback/i });
    fireEvent.click(rollbackButtons[0]);

    // Confirmation modal should be visible
    expect(screen.getByText('Roll Back HMIS Import Dataset')).toBeInTheDocument();
    expect(screen.getByText(/Important: This operation modifies database records/i)).toBeInTheDocument();

    // Type optional reason
    const reasonInput = screen.getByPlaceholderText(/Ingested incorrect facility reporting month/i);
    fireEvent.change(reasonInput, { target: { value: 'Erroneous reporting period' } });

    // Click confirm
    const confirmBtn = screen.getByRole('button', { name: /Confirm Rollback/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.rollbackImport).toHaveBeenCalledWith('JOB_20261003_100000_111111', 'Erroneous reporting period');
      expect(api.getImports).toHaveBeenCalledTimes(2); // Initial load + refresh after rollback
    });
  });

  it('displays conflict error message in modal when subsequent imports depend on target job', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    });

    const conflictErr = new Error('Cannot roll back import job because subsequent active import job(s) [JOB_LATER] modified the same observation(s). Roll back subsequent dependent imports first.');
    (conflictErr as any).status = 409;
    (api.rollbackImport as any).mockRejectedValueOnce(conflictErr);

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('mohfw_delhi_2024.csv')).toBeInTheDocument();
    });

    const rollbackButtons = screen.getAllByRole('button', { name: /Rollback/i });
    fireEvent.click(rollbackButtons[0]);

    const confirmBtn = screen.getByRole('button', { name: /Confirm Rollback/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText('Cannot Roll Back: Dependent Imports Detected')).toBeInTheDocument();
      expect(screen.getByText(/To preserve continuous data provenance/i)).toBeInTheDocument();
    });
  });

  // 14. Phase 9A Active Ingestion Progress Banner & Retries
  it('displays active batch progress banner when a job is PROCESSING or QUEUED', async () => {
    const processingJob: ImportJob = {
      id: 99,
      job_code: 'JOB_ACTIVE_PROC',
      original_filename: 'live_batch.csv',
      file_size_bytes: 8192,
      mime_type: 'text/csv',
      file_hash: 'hash_live',
      status: 'PROCESSING',
      total_records: 1000,
      processed_records: 450,
      records_imported: 440,
      records_rejected: 10,
      progress_percent: 45.0,
      schema_profile: 'mohfw_standard_v2',
      quality_score: null,
      created_at: '2026-10-20T10:00:00Z',
      updated_at: '2026-10-20T10:00:02Z',
      completed_at: null,
    };

    (api.getImports as any).mockResolvedValue({
      total: 1,
      items: [processingJob],
      page: 1,
      page_size: 10,
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Batch Ingestion in Progress')).toBeInTheDocument();
      expect(screen.getAllByText('JOB_ACTIVE_PROC').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('mohfw_standard_v2')).toBeInTheDocument();
    });
  });

  it('renders Retry button on FAILED jobs for ADMIN and calls api.retryImport on click', async () => {
    (useAuth as any).mockReturnValue({
      user: { id: 1, username: 'admin', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    });

    (api.retryImport as any).mockResolvedValueOnce({
      job_code: 'JOB_20261003_120000_333333',
      status: 'QUEUED',
      retry_count: 1,
      message: 'Job re-queued successfully.',
    });

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('corrupted_format.csv')).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole('button', { name: /Retry/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(api.retryImport).toHaveBeenCalledWith('JOB_20261003_120000_333333');
    });
  });

  it('shows queued feedback when an uploaded file returns QUEUED status', async () => {
    const queuedJob: ImportJob = {
      id: 5,
      job_code: 'JOB_ASYNC_QUEUED',
      original_filename: 'async_batch.csv',
      file_size_bytes: 2048,
      mime_type: 'text/csv',
      file_hash: 'hash_q',
      status: 'QUEUED',
      total_records: 0,
      records_imported: 0,
      records_rejected: 0,
      quality_score: null,
      created_at: '2026-10-20T10:00:00Z',
      updated_at: '2026-10-20T10:00:00Z',
      completed_at: null,
    };
    (api.uploadImportFile as any).mockResolvedValueOnce(queuedJob);

    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    const input = screen.getByTestId('hmis-file-input');
    const validFile = new File(['header1,header2\n1,2'], 'async_batch.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [validFile] } });

    await waitFor(() => {
      expect(screen.getByText('async_batch.csv')).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole('button', { name: /Begin Ingestion/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.uploadImportFile).toHaveBeenCalledWith(validFile);
      expect(screen.getByText('Dataset Queued for Processing')).toBeInTheDocument();
      expect(screen.getByText('JOB_ASYNC_QUEUED')).toBeInTheDocument();
    });
  });

  it('switches between individual jobs tab and automated batches tab', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    // Initial state shows individual jobs table
    expect(screen.getByTestId('tab-individual-jobs')).toBeInTheDocument();
    expect(screen.getByTestId('tab-automated-batches')).toBeInTheDocument();

    // Click automated batches tab
    fireEvent.click(screen.getByTestId('tab-automated-batches'));

    await waitFor(() => {
      expect(screen.getByText('Automated Batch Ingestion & Incoming Directory')).toBeInTheDocument();
      expect(screen.getByText('BATCH_TEST_001')).toBeInTheDocument();
    });

    // Switch back to individual jobs
    fireEvent.click(screen.getByTestId('tab-individual-jobs'));

    await waitFor(() => {
      expect(screen.getByText('Ingestion History & Audit Registry')).toBeInTheDocument();
    });
  });

  it('triggers on-demand directory scan from batch panel', async () => {
    render(
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByTestId('tab-automated-batches'));

    await waitFor(() => {
      expect(screen.getByTestId('scan-incoming-directory-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('scan-incoming-directory-btn'));

    await waitFor(() => {
      expect(api.triggerDirectoryScan).toHaveBeenCalled();
      expect(screen.getByText(/Directory scan completed/i)).toBeInTheDocument();
    });
  });
});

import type {
  SystemHealth,
  Facility,
  FacilityListResponse,
  Indicator,
  AnalyticsSummary,
  AnalyticsTrendsResponse,
  RegionalAnalyticsResponse,
  FacilityAnalyticsResponse,
  DataQualityAnalyticsResponse,
  ForecastResponse,
  ModelMetrics,
  User,
  TokenResponse,
  LoginPayload,
  ImportJob,
  ImportJobListResponse,
  ImportJobQualityResponse,
  ImportErrorLogListResponse,
  ImportRollbackResponse,
  ImportJobProgressResponse,
  ImportJobRetryResponse,
  ImportBatch,
  ImportBatchDetail,
  ImportBatchListResponse,
  DirectoryScanTriggerResponse,
  ImportBatchRetryResponse,
  DistrictCatalogResponse,
  DistrictIndicatorCatalogResponse,
  DistrictMonthlyTrendsResponse,
  DistrictComparisonResponse,
  DistrictDataQualitySummaryResponse,
  DistrictTrendsExportParams,
  DistrictComparisonExportParams,
  IndicatorRegistryResponse,
  IndicatorAuditReportResponse,
} from './types';

const API_BASE_URL = '/api';
const TOKEN_KEY = 'careflow_access_token';

export class ApiError extends Error {
  status: number;
  data: unknown;
  requestId?: string;
  code?: string;

  constructor(message: string, status: number, data?: unknown, requestId?: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.requestId = requestId;
    this.code = code;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getStoredToken();

  const isFormData = typeof FormData !== 'undefined' && options?.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    const requestIdHeader = res.headers.get('X-Request-ID') || res.headers.get('x-request-id') || undefined;

    if (res.status === 401 && endpoint !== '/auth/login') {
      removeStoredToken();
    }

    if (!res.ok) {
      let errorMsg = `API Error (${res.status} ${res.statusText})`;
      let errorData: any = null;
      let parsedRequestId = requestIdHeader;
      let parsedCode: string | undefined = undefined;

      try {
        errorData = await res.json();
        if (errorData?.detail) {
          errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
        if (errorData?.error?.message) {
          errorMsg = errorData.error.message;
        }
        if (errorData?.error?.request_id) {
          parsedRequestId = errorData.error.request_id;
        }
        if (errorData?.error?.code) {
          parsedCode = errorData.error.code;
        }
      } catch {
        // Fallback
      }
      throw new ApiError(errorMsg, res.status, errorData, parsedRequestId, parsedCode);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      err instanceof Error ? err.message : 'Unable to connect to CAREFlow backend API server.',
      0
    );
  }
}

export const api = {
  // Authentication
  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const response = await fetchJson<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (response.access_token) {
      setStoredToken(response.access_token);
    }
    return response;
  },

  getMe: (): Promise<User> => fetchJson<User>('/auth/me'),

  logout: async (): Promise<{ message: string }> => {
    try {
      const res = await fetchJson<{ message: string }>('/auth/logout', { method: 'POST' });
      removeStoredToken();
      return res;
    } catch {
      removeStoredToken();
      return { message: 'Logged out' };
    }
  },

  // Health
  getHealth: () => fetchJson<SystemHealth>('/health'),

  // Facilities
  getFacilities: (params?: { state?: string; district?: string; facility_type?: string; skip?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.state) query.append('state', params.state);
    if (params?.district) query.append('district', params.district);
    if (params?.facility_type) query.append('facility_type', params.facility_type);
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const qStr = query.toString();
    return fetchJson<FacilityListResponse | Facility[]>(`/facilities${qStr ? `?${qStr}` : ''}`);
  },

  getFacilityById: (id: string) => fetchJson<Facility>(`/facilities/${id}`),

  // Indicators
  getIndicators: () => fetchJson<Indicator[]>('/indicators'),

  // Analytics Engine
  getAnalyticsSummary: (params?: { state?: string; district?: string }) => {
    const query = new URLSearchParams();
    if (params?.state) query.append('state', params.state);
    if (params?.district) query.append('district', params.district);
    const qStr = query.toString();
    return fetchJson<AnalyticsSummary>(`/analytics/summary${qStr ? `?${qStr}` : ''}`);
  },

  getAnalyticsTrends: (params?: { indicator_code?: string; state?: string; district?: string; facility_id?: string; start_month?: string; end_month?: string }) => {
    const query = new URLSearchParams();
    if (params?.indicator_code) query.append('indicator_code', params.indicator_code);
    if (params?.state) query.append('state', params.state);
    if (params?.district) query.append('district', params.district);
    if (params?.facility_id) query.append('facility_id', params.facility_id);
    if (params?.start_month) query.append('start_month', params.start_month);
    if (params?.end_month) query.append('end_month', params.end_month);
    const qStr = query.toString();
    return fetchJson<AnalyticsTrendsResponse>(`/analytics/trends${qStr ? `?${qStr}` : ''}`);
  },

  getRegionalAnalytics: (params?: { level?: 'state' | 'district'; indicator_code?: string; state?: string; district?: string; reporting_month?: string }) => {
    const query = new URLSearchParams();
    if (params?.level) query.append('level', params.level);
    if (params?.indicator_code) query.append('indicator_code', params.indicator_code);
    if (params?.state) query.append('state', params.state);
    if (params?.district) query.append('district', params.district);
    if (params?.reporting_month) query.append('reporting_month', params.reporting_month);
    const qStr = query.toString();
    return fetchJson<RegionalAnalyticsResponse>(`/analytics/regional${qStr ? `?${qStr}` : ''}`);
  },

  getFacilityAnalytics: (facilityId: string, indicatorCode?: string) => {
    const query = new URLSearchParams({ facility_id: facilityId });
    if (indicatorCode) query.append('indicator_code', indicatorCode);
    return fetchJson<FacilityAnalyticsResponse>(`/analytics/facilities?${query.toString()}`);
  },

  getDataQualityAnalytics: () => fetchJson<DataQualityAnalyticsResponse>('/analytics/data-quality'),

  // Forecasting Engine
  getForecast: (facilityId: string, indicatorCode: string = 'opd_attendance', horizon: number = 12) => {
    const query = new URLSearchParams({
      facility_id: facilityId,
      indicator_code: indicatorCode,
      horizon: String(horizon)
    });
    return fetchJson<ForecastResponse>(`/forecast?${query.toString()}`);
  },

  getModelMetrics: (targetIndicator?: string) => {
    const query = new URLSearchParams();
    if (targetIndicator) query.append('target_indicator', targetIndicator);
    const qStr = query.toString();
    return fetchJson<ModelMetrics[]>(`/model/metrics${qStr ? `?${qStr}` : ''}`);
  },

  // HMIS Data Ingestion & Import Workspace (Phase 7G)
  uploadImportFile: (file: File): Promise<ImportJob> => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchJson<ImportJob>('/imports', {
      method: 'POST',
      body: formData,
    });
  },

  getImports: (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    search?: string;
  }): Promise<ImportJobListResponse> => {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    if (params?.status) query.append('status', params.status);
    if (params?.search) query.append('search', params.search);
    const qStr = query.toString();
    return fetchJson<ImportJobListResponse>(`/imports${qStr ? `?${qStr}` : ''}`);
  },

  getImportDetail: (jobCode: string): Promise<ImportJob> => {
    return fetchJson<ImportJob>(`/imports/${jobCode}`);
  },

  getImportQuality: (jobCode: string): Promise<ImportJobQualityResponse> => {
    return fetchJson<ImportJobQualityResponse>(`/imports/${jobCode}/quality`);
  },

  getImportErrors: (
    jobCode: string,
    params?: {
      skip?: number;
      limit?: number;
    }
  ): Promise<ImportErrorLogListResponse> => {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const qStr = query.toString();
    return fetchJson<ImportErrorLogListResponse>(`/imports/${jobCode}/errors${qStr ? `?${qStr}` : ''}`);
  },

  rollbackImport: (jobCode: string, reason?: string): Promise<ImportRollbackResponse> => {
    return fetchJson<ImportRollbackResponse>(`/imports/${jobCode}/rollback`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || null }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  getImportJobStatus: (jobCode: string): Promise<ImportJobProgressResponse> => {
    return fetchJson<ImportJobProgressResponse>(`/imports/${jobCode}/status`);
  },

  retryImport: (jobCode: string): Promise<ImportJobRetryResponse> => {
    return fetchJson<ImportJobRetryResponse>(`/imports/${jobCode}/retry`, {
      method: 'POST',
    });
  },

  cancelImport: (jobCode: string): Promise<{ job_code: string; status: string; message: string }> => {
    return fetchJson<{ job_code: string; status: string; message: string }>(`/imports/${jobCode}/cancel`, {
      method: 'POST',
    });
  },

  // Batch Monitoring & Directory Orchestration (Phase 9B)
  getImportBatches: (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    source?: string;
  }): Promise<ImportBatchListResponse> => {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    if (params?.status) query.append('status', params.status);
    if (params?.source) query.append('source', params.source);
    const qStr = query.toString();
    return fetchJson<ImportBatchListResponse>(`/imports/batches${qStr ? `?${qStr}` : ''}`);
  },

  getImportBatchDetail: (batchCode: string): Promise<ImportBatchDetail> => {
    return fetchJson<ImportBatchDetail>(`/imports/batches/${batchCode}`);
  },

  triggerDirectoryScan: (): Promise<DirectoryScanTriggerResponse> => {
    return fetchJson<DirectoryScanTriggerResponse>('/imports/batches/scan', {
      method: 'POST',
    });
  },

  retryImportBatch: (batchCode: string): Promise<ImportBatchRetryResponse> => {
    return fetchJson<ImportBatchRetryResponse>(`/imports/batches/${batchCode}/retry`, {
      method: 'POST',
    });
  },

  cancelImportBatch: (batchCode: string, reason?: string): Promise<ImportBatch> => {
    return fetchJson<ImportBatch>(`/imports/batches/${batchCode}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || null }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  // District HMIS Analytics (Phases 11D-11G & Phase 12)
  getDistrictCatalog: (): Promise<DistrictCatalogResponse> => {
    return fetchJson<DistrictCatalogResponse>('/analytics/district/catalog');
  },

  getDistrictIndicators: (): Promise<DistrictIndicatorCatalogResponse> => {
    return fetchJson<DistrictIndicatorCatalogResponse>('/analytics/district/indicators');
  },

  getIndicatorRegistry: (status?: string): Promise<IndicatorRegistryResponse> => {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return fetchJson<IndicatorRegistryResponse>(`/analytics/district/indicators/registry${q}`);
  },

  getIndicatorAudit: (): Promise<IndicatorAuditReportResponse> => {
    return fetchJson<IndicatorAuditReportResponse>('/analytics/district/indicators/audit');
  },

  getDistrictMonthlyTrends: (params: {
    district: string;
    s_no: string;
    subgroup_type?: string;
    start_month?: string;
    end_month?: string;
    financial_year?: string;
  }): Promise<DistrictMonthlyTrendsResponse> => {
    const query = new URLSearchParams();
    query.append('district', params.district);
    query.append('s_no', params.s_no);
    if (params.subgroup_type) query.append('subgroup_type', params.subgroup_type);
    if (params.start_month) query.append('start_month', params.start_month);
    if (params.end_month) query.append('end_month', params.end_month);
    if (params.financial_year) query.append('financial_year', params.financial_year);
    return fetchJson<DistrictMonthlyTrendsResponse>(`/analytics/district/trends?${query.toString()}`);
  },

  getDistrictComparison: (params: {
    s_no: string;
    reporting_month: string;
    subgroup_type?: string;
    districts?: string[];
    financial_year?: string;
  }): Promise<DistrictComparisonResponse> => {
    const query = new URLSearchParams();
    query.append('s_no', params.s_no);
    query.append('reporting_month', params.reporting_month);
    if (params.subgroup_type) query.append('subgroup_type', params.subgroup_type);
    if (params.financial_year) query.append('financial_year', params.financial_year);
    if (params.districts && params.districts.length > 0) {
      params.districts.forEach(d => query.append('districts', d));
    }
    return fetchJson<DistrictComparisonResponse>(`/analytics/district/compare?${query.toString()}`);
  },

  getDistrictQuality: (): Promise<DistrictDataQualitySummaryResponse> => {
    return fetchJson<DistrictDataQualitySummaryResponse>('/analytics/district/quality');
  },

  downloadDistrictTrendsCsv: async (params: DistrictTrendsExportParams): Promise<void> => {
    const query = new URLSearchParams();
    query.append('district', params.district);
    query.append('s_no', params.s_no);
    if (params.subgroup_type) query.append('subgroup_type', params.subgroup_type);
    if (params.start_month) query.append('start_month', params.start_month);
    if (params.end_month) query.append('end_month', params.end_month);
    if (params.financial_year) query.append('financial_year', params.financial_year);

    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}/analytics/district/export/trends?${query.toString()}`, { headers });
    if (!res.ok) {
      throw new ApiError(`Failed to export trends CSV (${res.status})`, res.status);
    }
    const blob = await res.blob();
    const filename = `district_trends_${params.district.replace(/\s+/g, '_').toLowerCase()}_${params.s_no.replace(/\./g, '_')}.csv`;
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  },

  downloadDistrictComparisonCsv: async (params: DistrictComparisonExportParams): Promise<void> => {
    const query = new URLSearchParams();
    query.append('s_no', params.s_no);
    query.append('reporting_month', params.reporting_month);
    if (params.subgroup_type) query.append('subgroup_type', params.subgroup_type);
    if (params.financial_year) query.append('financial_year', params.financial_year);
    if (params.districts && params.districts.length > 0) {
      params.districts.forEach(d => query.append('districts', d));
    }

    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}/analytics/district/export/compare?${query.toString()}`, { headers });
    if (!res.ok) {
      throw new ApiError(`Failed to export comparison CSV (${res.status})`, res.status);
    }
    const blob = await res.blob();
    const filename = `district_compare_${params.s_no.replace(/\./g, '_')}_${params.reporting_month}.csv`;
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  },
};

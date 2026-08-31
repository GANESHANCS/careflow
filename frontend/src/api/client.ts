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
  LoginPayload
} from './types';

const API_BASE_URL = '/api';
const TOKEN_KEY = 'careflow_access_token';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
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

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
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

    if (res.status === 401 && endpoint !== '/auth/login') {
      removeStoredToken();
    }

    if (!res.ok) {
      let errorMsg = `API Error (${res.status} ${res.statusText})`;
      let errorData = null;
      try {
        errorData = await res.json();
        if (errorData?.detail) {
          errorMsg = errorData.detail;
        }
      } catch {
        // Fallback
      }
      throw new ApiError(errorMsg, res.status, errorData);
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
  }
};

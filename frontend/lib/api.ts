import type {
  AuditResult,
  AuditRunResult,
  Business,
  ImportResult,
  Lead,
  LeadScore,
  ScoreRunResult,
  Stats,
} from './types';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** A connection-level failure (server unreachable, CORS, DNS, etc.) as
 * opposed to an ApiError, which means the server responded with an
 * error status. The dashboard uses this distinction to show "check your
 * API URL / is the server running?" vs. a specific error message. */
export class ApiUnreachableError extends Error {
  constructor(apiBase: string) {
    super(`Could not reach the SYJ LeadForge API at ${apiBase}`);
    this.name = 'ApiUnreachableError';
  }
}

async function request<T>(apiBase: string, path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...init,
      headers: {
        ...(init?.body && !(init.body instanceof FormData)
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiUnreachableError(apiBase);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // Response wasn't JSON; fall back to statusText.
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export function checkHealth(apiBase: string): Promise<{ status: string; version: string }> {
  return request(apiBase, '/health');
}

export function importCsv(apiBase: string, file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append('file', file);
  return request(apiBase, '/businesses/import', { method: 'POST', body: form });
}

export function listBusinesses(
  apiBase: string,
  params: { category?: string; city?: string } = {}
): Promise<Business[]> {
  const qs = new URLSearchParams();
  if (params.category) qs.set('category', params.category);
  if (params.city) qs.set('city', params.city);
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return request(apiBase, `/businesses${suffix}`);
}

export function createBusiness(
  apiBase: string,
  payload: Partial<Business> & { name: string }
): Promise<Business> {
  return request(apiBase, '/businesses', { method: 'POST', body: JSON.stringify(payload) });
}

export function auditBusiness(apiBase: string, businessId: number): Promise<AuditResult> {
  return request(apiBase, `/businesses/${businessId}/audit`, { method: 'POST' });
}

export function runAllAudits(apiBase: string): Promise<AuditRunResult> {
  return request(apiBase, '/audits/run', { method: 'POST' });
}

export function scoreBusiness(apiBase: string, businessId: number): Promise<LeadScore> {
  return request(apiBase, `/businesses/${businessId}/score`, { method: 'POST' });
}

export function runAllScores(apiBase: string): Promise<ScoreRunResult> {
  return request(apiBase, '/scores/run', { method: 'POST' });
}

export function listLeads(
  apiBase: string,
  params: { tier?: string; min_score?: number } = {}
): Promise<Lead[]> {
  const qs = new URLSearchParams();
  if (params.tier) qs.set('tier', params.tier);
  if (params.min_score !== undefined) qs.set('min_score', String(params.min_score));
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return request(apiBase, `/leads${suffix}`);
}

export function getStats(apiBase: string): Promise<Stats> {
  return request(apiBase, '/stats');
}

export function exportLeadsUrl(
  apiBase: string,
  format: 'csv' | 'json' | 'markdown',
  params: { tier?: string; min_score?: number } = {}
): string {
  const qs = new URLSearchParams();
  if (params.tier) qs.set('tier', params.tier);
  if (params.min_score !== undefined) qs.set('min_score', String(params.min_score));
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return `${apiBase}/leads/export/${format}${suffix}`;
}

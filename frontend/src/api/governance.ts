import { baseUrl, requestTimeout } from './config';
import { authRequest } from './auth';

export type ObligationStatus = 'Overdue' | 'Due soon' | 'Upcoming' | 'Completed';
export interface Obligation {
  id: string; application_id: string; ci_id: string; application_name: string;
  control_name: string; control_key: string; due_date: string; window_start: string;
  frequency_months: number; due_soon_days: number; mandatory: boolean;
  evidence_requirement: string | null; policy_version_id: string; version_number: number;
  status: ObligationStatus; days_remaining: number; completed_at: string | null;
  completed_by: string | null; evidence_reference: string | null; notes: string | null;
}
export interface PortfolioApplication {
  id: string; ci_id: string; name: string; lifecycle_state: string; validation_state: string;
  governance_health: 'Overdue' | 'Due soon' | 'Current' | 'Not scheduled';
}
export interface Governance {
  as_of: string; timezone: string; counts: Record<ObligationStatus, number>;
  applications: PortfolioApplication[]; items: Obligation[];
}

export async function governanceRequest(path: string, options: RequestInit = {}): Promise<unknown> {
  const response = await fetch(`${baseUrl}/api/v1/governance${path}`, {
    ...options, credentials: 'include', cache: 'no-store',
    signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(requestTimeout)]) : AbortSignal.timeout(requestTimeout),
  });
  if (response.status === 401) window.dispatchEvent(new Event('assurgrid-session-expired'));
  if (!response.ok) {
    throw new Error(response.status === 409 ? 'This review changed or its window has not started. Refresh the list.' :
      response.status === 403 ? 'Your role cannot record completion, or the request could not be verified.' :
      response.status === 404 ? 'This obligation is outside your access or no longer exists.' :
      'Governance could not be reached. The free demo server may be waking up; please try again.');
  }
  return response.json();
}

export async function getGovernance(query: string, signal: AbortSignal): Promise<Governance> {
  const data = await governanceRequest(query ? `?${query}` : '', { signal });
  if (!data || typeof data !== 'object' || !('items' in data) || !Array.isArray(data.items) ||
      !('applications' in data) || !Array.isArray(data.applications) || !('counts' in data) ||
      !('as_of' in data) || !('timezone' in data)) throw new Error('Unexpected governance response.');
  return data as Governance;
}

export async function completeObligation(id: string, evidence_reference: string, notes: string) {
  const csrf: unknown = await (await authRequest('csrf', { method: 'POST' })).json();
  if (!csrf || typeof csrf !== 'object' || !('csrf_token' in csrf) || typeof csrf.csrf_token !== 'string') throw new Error('Could not verify this request.');
  return governanceRequest(`/${encodeURIComponent(id)}/complete`, { method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf.csrf_token },
    body: JSON.stringify({ evidence_reference, notes }) });
}

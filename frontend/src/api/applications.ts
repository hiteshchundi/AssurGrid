const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');

export interface Application {
  id: string;
  organization_id: string;
  ci_id: string;
  name: string;
  system_type: string;
  description: string | null;
  gxp_classification: string;
  criticality: string;
  lifecycle_state: string;
  validation_state: string;
  supplier: string | null;
  platform: string | null;
  created_at: string;
  updated_at: string;
  business_owner_id: string | null;
  technical_owner_id: string | null;
  quality_owner_id: string | null;
}

export interface ApplicationPage {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
}

export class RegistryError extends Error {
  constructor(message: string, public status?: number) { super(message); }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isApplication(value: unknown): value is Application {
  if (!isRecord(value)) return false;
  const required = ['id', 'organization_id', 'ci_id', 'name', 'system_type', 'gxp_classification',
    'criticality', 'lifecycle_state', 'validation_state', 'created_at', 'updated_at'];
  const nullable = ['description', 'supplier', 'platform', 'business_owner_id', 'technical_owner_id', 'quality_owner_id'];
  return required.every((key) => typeof value[key] === 'string') &&
    nullable.every((key) => value[key] === null || typeof value[key] === 'string');
}

async function request(path: string, signal: AbortSignal): Promise<unknown> {
  if (!baseUrl) throw new RegistryError('The API address is not configured. Set VITE_API_BASE_URL and restart the frontend.');
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      credentials: 'include', cache: 'no-store',
      signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]),
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new RegistryError('The registry could not be reached. Check the API connection, then try again.');
  }
  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new Event('assurgrid-session-expired'));
      throw new RegistryError('Your session has ended. Please sign in again.', 401);
    }
    if (response.status === 404) throw new RegistryError('This application was not found in the configured organization.', 404);
    if (response.status === 422) throw new RegistryError('The filters or application address are invalid. Clear the filters or return to the registry.', 422);
    if (response.status === 503) throw new RegistryError('The registry is unavailable. Check the database and local demo organization configuration.', 503);
    throw new RegistryError('The registry request failed. Please try again.', response.status);
  }
  try { return await response.json(); }
  catch { throw new RegistryError('The API returned an unexpected response. Please try again.'); }
}

export async function getApplications(query: string, signal: AbortSignal): Promise<ApplicationPage> {
  const data = await request(`/api/v1/applications${query ? `?${query}` : ''}`, signal);
  if (isRecord(data) && Array.isArray(data.items) && data.items.every(isApplication) &&
      typeof data.total === 'number' && Number.isInteger(data.total) && data.total >= 0 &&
      typeof data.page === 'number' && Number.isInteger(data.page) && data.page >= 1 &&
      typeof data.page_size === 'number' && Number.isInteger(data.page_size) && data.page_size >= 1) {
    return { items: data.items, total: data.total, page: data.page, page_size: data.page_size };
  }
  throw new RegistryError('The API returned an unexpected registry response. Please try again.');
}

export async function getApplication(id: string, signal: AbortSignal): Promise<Application> {
  const data = await request(`/api/v1/applications/${encodeURIComponent(id)}`, signal);
  if (isApplication(data)) return data;
  throw new RegistryError('The API returned an unexpected application response. Please try again.');
}

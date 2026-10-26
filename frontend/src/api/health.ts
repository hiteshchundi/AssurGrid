import { baseUrl, requestTimeout } from './config';

export type Readiness =
  | { status: 'ready'; database: 'connected' }
  | { status: 'not_ready'; database: 'unavailable' };

export async function getLiveness(signal: AbortSignal): Promise<{ status: 'ok' }> {
  const response = await fetch(`${baseUrl}/api/v1/health/live`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(requestTimeout)]),
  });
  if (!response.ok || (await response.json()).status !== 'ok') {
    throw new Error('API unavailable');
  }
  return { status: 'ok' };
}

export async function getReadiness(signal: AbortSignal): Promise<Readiness> {
  const response = await fetch(`${baseUrl}/api/v1/health/ready`, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(requestTimeout)]),
  });
  if (response.status !== 200 && response.status !== 503) {
    throw new Error('Readiness check unavailable');
  }
  const body: unknown = await response.json();
  if (typeof body === 'object' && body !== null && 'status' in body && 'database' in body) {
    if (response.status === 200 && body.status === 'ready' && body.database === 'connected') {
      return { status: 'ready', database: 'connected' };
    }
    if (response.status === 503 && body.status === 'not_ready' && body.database === 'unavailable') {
      return { status: 'not_ready', database: 'unavailable' };
    }
  }
  throw new Error('Unexpected readiness response');
}

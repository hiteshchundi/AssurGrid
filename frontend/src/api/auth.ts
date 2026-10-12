const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');
export interface Identity { user_id: string; organization_id: string; role: string }
export class AuthError extends Error {
  constructor(message: string, public status?: number) { super(message); }
}
export async function authRequest(path: string, options: RequestInit = {}): Promise<Response> {
  if (!baseUrl) throw new AuthError('The API address is not configured.');
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1/auth/${path}`, {
      ...options, credentials: 'include', cache: 'no-store',
      signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(5000)]) : AbortSignal.timeout(5000),
    });
  } catch { throw new AuthError('The sign-in service could not be reached. Please try again.'); }
  if (!response.ok) throw new AuthError(
    response.status === 401 ? 'Your email or password was not accepted, or your session has ended.' :
    response.status === 403 ? 'The request could not be verified. Please try again.' :
    response.status === 422 ? 'Check your email and password and try again.' :
    'Sign-in is unavailable. Check the local demo setup.', response.status);
  return response;
}
export async function getIdentity(signal?: AbortSignal): Promise<Identity | null> {
  try {
    const body: unknown = await (await authRequest('me', { signal })).json();
    if (typeof body !== 'object' || body === null || !('user_id' in body) || !('organization_id' in body) || !('role' in body) ||
        typeof body.user_id !== 'string' || typeof body.organization_id !== 'string' || typeof body.role !== 'string') {
      throw new AuthError('Unexpected session response. Please try again.');
    }
    return { user_id: body.user_id, organization_id: body.organization_id, role: body.role };
  } catch (error) { if (error instanceof AuthError && error.status === 401) return null; throw error; }
}

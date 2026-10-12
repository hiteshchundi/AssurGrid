import { createContext, useContext, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router';
import { AuthError, authRequest, getIdentity, type Identity } from '../../api/auth';

const AuthContext = createContext<{ identity: Identity | null; pending: boolean; error: Error | null; refresh: () => void }>({
  identity: null, pending: true, error: null, refresh: () => {},
});
export const useIdentity = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const cache = useQueryClient();
  const query = useQuery({ queryKey: ['session'], queryFn: ({ signal }) => getIdentity(signal), refetchInterval: 10000, staleTime: 0 });
  useEffect(() => {
    function expire() {
      void cache.cancelQueries().then(() => { cache.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' }); cache.setQueryData(['session'], null); });
    }
    window.addEventListener('assurgrid-session-expired', expire);
    return () => window.removeEventListener('assurgrid-session-expired', expire);
  }, [cache]);
  return <AuthContext.Provider value={{ identity: query.isError ? null : query.data ?? null, pending: query.isPending,
    error: query.error, refresh: () => { void query.refetch(); } }}>{children}</AuthContext.Provider>;
}

export function RequireLogin() {
  const { identity, pending, error, refresh } = useIdentity();
  const location = useLocation();
  if (pending) return <div className="state-panel" role="status">Checking your session…</div>;
  if (error) return <div className="state-panel" role="alert"><h1>Session unavailable</h1><p>{error.message}</p><button onClick={refresh}>Try again</button></div>;
  if (!identity) return <Navigate to="/login" replace state={{ returnTo: location.pathname + location.search }} />;
  return <Outlet key={`${identity.user_id}:${identity.role}`} />;
}

export function LoginPage() {
  const { identity, pending } = useIdentity();
  const cache = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const requested = (location.state as { returnTo?: unknown } | null)?.returnTo;
  const returnTo = typeof requested === 'string' && /^\/applications(?:[/?]|$)/.test(requested) ? requested : '/applications';
  if (identity) return <Navigate to={returnTo} replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const form = event.currentTarget;
    const values = new FormData(form);
    try {
      await authRequest('login', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: values.get('email'), password: values.get('password') }) });
      const next = await getIdentity();
      if (!next) throw new AuthError('The session could not be established. Check browser cookie settings.');
      form.reset();
      await cache.cancelQueries(); cache.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' }); cache.setQueryData(['session'], next);
      navigate(returnTo, { replace: true });
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Sign-in failed.'); }
    finally { setBusy(false); }
  }
  return <section className="login-panel panel"><p className="eyebrow">ASSURGRID WORKSPACE</p><h1>Sign in to your registry</h1>
    <p>See the applications assigned to your role in the fictional Northstar organization.</p>
    <form onSubmit={submit}>
      <label htmlFor="email">Email address</label><input id="email" name="email" type="email" autoComplete="username" maxLength={254} required />
      <label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" maxLength={256} required />
      {error ? <p className="notice" role="alert">{error}</p> : null}
      <button type="submit" disabled={busy || pending}>{busy ? 'Signing in…' : 'Sign in'}</button>
    </form><p className="login-note">Use a synthetic demo account and the password chosen during local account setup. No company credentials.</p>
  </section>;
}

export function SessionControl() {
  const { identity } = useIdentity();
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!identity) return null;
  async function logout() {
    setBusy(true); setError('');
    try {
      const body: unknown = await (await authRequest('csrf', { method: 'POST' })).json();
      if (!body || typeof body !== 'object' || !('csrf_token' in body) || typeof body.csrf_token !== 'string') throw new Error('Could not verify sign-out. Try again.');
      await authRequest('logout', { method: 'POST', headers: { 'X-CSRF-Token': body.csrf_token } });
      await cache.cancelQueries(); cache.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' }); cache.setQueryData(['session'], null); navigate('/login', { replace: true });
    } catch (failure) {
      if (failure instanceof AuthError && failure.status === 401) {
        await cache.cancelQueries(); cache.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' }); cache.setQueryData(['session'], null); navigate('/login', { replace: true });
      } else setError(failure instanceof Error ? failure.message : 'Sign-out failed.');
    } finally { setBusy(false); }
  }
  return <div className="session-control"><span>{identity.role}</span><button onClick={() => { void logout(); }} disabled={busy}>{busy ? 'Signing out…' : 'Sign out'}</button>
    {error ? <span role="alert">{error}</span> : null}</div>;
}

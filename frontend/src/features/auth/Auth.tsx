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
  const demo = useQuery({ queryKey: ['auth-options'], queryFn: async () => {
    const value: unknown = await (await authRequest('options')).json();
    return !!value && typeof value === 'object' && 'public_demo_enabled' in value && value.public_demo_enabled === true;
  }, refetchInterval: false });
  const requested = (location.state as { returnTo?: unknown } | null)?.returnTo;
  const returnTo = typeof requested === 'string' && /^\/(?:overview|applications|policies)(?:[/?]|$)/.test(requested) ? requested : '/overview';
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
  async function enterDemo(persona: string) {
    setBusy(true); setError('');
    try {
      await authRequest('demo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ persona }) });
      const next = await getIdentity();
      if (!next) throw new AuthError('The demo session could not be established. Please try again.');
      await cache.cancelQueries();
      cache.removeQueries({ predicate: query => query.queryKey[0] !== 'session' });
      cache.setQueryData(['session'], next); navigate(returnTo, { replace: true });
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not open the demo.'); }
    finally { setBusy(false); }
  }
  if (demo.data) return <section className="demo-entry"><div className="demo-intro"><p className="eyebrow">GOVERNANCE, WITH CONTEXT</p>
    <h1>Know what’s due.<br />Show where the evidence is.</h1><p>A workspace for oversight of regulated applications. Explore a fictional portfolio, inspect policy-driven review schedules, and record completion evidence.</p>
    <div className="demo-story"><span>01 · Portfolio</span><span>02 · Application</span><span>03 · Review</span><span>04 · Evidence</span></div>
    <p className="context-note">An interview portfolio prototype. Synthetic data and illustrative policies; no regulatory certification or electronic signature claim.</p></div>
    <div className="persona-panel detail-card"><p className="eyebrow">NORTHSTAR BIOPHARMA · FICTIONAL</p><h2>Choose a demo perspective</h2><p>No account setup needed. Switch roles by signing out.</p>
      <div className="persona-grid">{[
        ['quality', 'Quality', 'Inspect all 48 applications and record review evidence.'],
        ['owner', 'Application Owner', 'Focus on your 3 assigned systems and complete reviews.'],
        ['viewer', 'Viewer', 'Explore LIMS with read-only access.'],
        ['admin', 'Admin', 'Explore the full portfolio and policy history.'],
      ].map(([persona, label, description]) => <button key={persona} disabled={busy || pending} onClick={() => void enterDemo(persona)}><strong>{label} →</strong><span>{description}</span></button>)}</div>
      {busy ? <p role="status">Opening your workspace…</p> : null}{error ? <p className="notice" role="alert">{error}</p> : null}
      <p className="context-note">Shared sandbox: completion records are visible to other visitors. Enter fictional information only.</p></div></section>;
  return <section className="login-panel panel"><p className="eyebrow">ASSURGRID WORKSPACE</p><h1>Sign in to your registry</h1>
    {demo.isPending ? <p role="status">Checking demo availability… The free server may take a minute to wake up.</p> : null}
    {demo.isError ? <p className="notice" role="alert">The demo server could not be reached. <button onClick={() => void demo.refetch()}>Try again</button></p> : null}
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

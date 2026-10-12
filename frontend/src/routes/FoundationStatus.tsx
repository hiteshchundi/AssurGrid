import { useQuery } from '@tanstack/react-query';
import { getLiveness, getReadiness } from '../api/health';

export function FoundationStatus() {
  const live = useQuery({ queryKey: ['health', 'live'], queryFn: ({ signal }) => getLiveness(signal) });
  const ready = useQuery({ queryKey: ['health', 'ready'], queryFn: ({ signal }) => getReadiness(signal) });
  const apiStatus = live.isPending ? 'Checking' : live.isError ? 'Unavailable' : 'Connected';
  const databaseStatus = ready.isPending ? 'Checking' : ready.isError ? 'Unknown' :
    ready.data.database === 'connected' ? 'Connected' : 'Unavailable';
  const unavailable = live.isError || ready.isError || ready.data?.status === 'not_ready';
  const checking = live.isFetching || ready.isFetching;

  return (
      <section className="foundation-panel" aria-labelledby="foundation-title">
        <p className="eyebrow">AG-03 · Foundation</p>
        <h1 id="foundation-title">Foundation status</h1>
        <p className="intro">Connection checks for your local development environment.</p>
        <div aria-live="polite" aria-atomic="true">
          <dl className="detail-fields">
            <div><dt>API</dt><dd className={apiStatus === 'Connected' ? 'connected' : ''}>{apiStatus}</dd></div>
            <div><dt>Database</dt><dd className={databaseStatus === 'Connected' ? 'connected' : ''}>{databaseStatus}</dd></div>
          </dl>
          {unavailable ? <p className="notice">The foundation is unavailable. Check the backend and PostgreSQL, then retry.</p> : null}
        </div>
        <footer className="foundation-footer">
          <span>Checks refresh every 10 seconds.</span>
          <button type="button" disabled={checking} onClick={() => { void live.refetch(); void ready.refetch(); }}>
            {checking ? 'Checking…' : 'Check again'}
          </button>
        </footer>
      </section>
  );
}

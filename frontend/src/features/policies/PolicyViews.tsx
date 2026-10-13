import { useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams, useSearchParams } from 'react-router';
import { getHistory, getPolicies, getResolution, type Rule } from '../../api/policies';
import { useIdentity } from '../auth/Auth';

function Rules({ rows }: { rows: Rule[] }) {
  if (!rows.length) return <p className="context-note">No rules recorded for this version.</p>;
  return <div className="policy-table" role="region" aria-label="Policy rules" tabIndex={0}><table><caption className="visually-hidden">Review rules and evidence requirements</caption>
    <thead><tr><th scope="col">Control</th><th scope="col">Frequency</th><th scope="col">Due soon</th><th scope="col">Required</th><th scope="col">Evidence reference</th></tr></thead>
    <tbody>{rows.map((r) => <tr key={r.id}><th scope="row">{r.control_name}<span className="policy-key">{r.control_key}{!r.control_active ? ' · Inactive' : ''}</span></th>
      <td>Every {r.frequency_months} calendar months</td><td>{r.due_soon_days} days</td><td>{r.mandatory ? 'Yes' : 'No'}</td><td>{r.evidence_requirement ?? 'Not specified'}</td></tr>)}</tbody></table></div>;
}
function Failure({ error, retry, busy }: { error: Error; retry: () => void; busy: boolean }) {
  return <div className="state-panel error-panel" role="alert"><p>{error.message}</p><button disabled={busy} onClick={retry}>Try again</button></div>;
}
export function PolicyCatalog() {
  const { identity } = useIdentity();
  const allowed = identity?.role === 'Admin' || identity?.role === 'Quality';
  const [params, setParams] = useSearchParams();
  const raw = params.get('page') ?? '1';
  const page = /^\d+$/.test(raw) && Number(raw) >= 1 && Number(raw) <= 10000 ? Number(raw) : 1;
  const query = useQuery({ queryKey: ['policies', identity?.user_id, identity?.role, page], queryFn: ({ signal }) => getPolicies(page, signal), enabled: allowed, refetchInterval: false });
  if (!allowed) return <div className="state-panel"><h1>Policy administration access required</h1><p>Admin and Quality can inspect the organization catalog. Open an assigned application to see its applicable policy defaults.</p><Link to="/applications">Open application registry</Link></div>;
  return <><div className="page-heading"><div><p className="eyebrow">Organization configuration</p><h1>Governance policies</h1><p className="intro">Inspect review rules and their effective versions.</p></div><button disabled={query.isFetching} onClick={() => void query.refetch()}>Refresh policies</button></div>
    <p className="context-note">Illustrative organization policies. Frequencies are fictional and are not regulator-mandated.</p>
    {query.isPending ? <div className="state-panel" role="status">Loading policies…</div> : query.isError ? <Failure error={query.error} busy={query.isFetching} retry={() => void query.refetch()} /> :
      <section className="detail-card"><h2>Policy profiles</h2>{query.data.items.length ? <ul className="policy-list">{query.data.items.map((p) => <li key={p.id}><Link to={`/policies/${p.id}`}>{p.name}</Link><span className="policy-key">{p.policy_key}</span></li>)}</ul> : <p>No policy profiles found on this page.</p>}
        <div className="pagination"><span>Page {page}</span><div><button disabled={page === 1} onClick={() => setParams({ page: String(page-1) })}>Previous</button><button disabled={!query.data.has_more || page === 10000} onClick={() => setParams({ page: String(page+1) })}>Next</button></div></div></section>}
  </>;
}
export function PolicyHistory() {
  const { identity } = useIdentity();
  const { id = '' } = useParams();
  const allowed = identity?.role === 'Admin' || identity?.role === 'Quality';
  const query = useQuery({ queryKey: ['policy-history', identity?.user_id, identity?.role, id], queryFn: ({ signal }) => getHistory(id, signal), enabled: allowed, refetchInterval: false });
  if (!allowed) return <div className="state-panel"><h1>Policy administration access required</h1><Link to="/applications">Open application registry</Link></div>;
  return <><Link className="back-link" to="/policies">← Back to governance policies</Link>
    {query.isPending ? <div className="state-panel" role="status">Loading policy history…</div> : query.isError ? <Failure error={query.error} busy={query.isFetching} retry={() => void query.refetch()} /> : <>
      <div className="page-heading"><div><p className="eyebrow">{query.data.policy_key}</p><h1>{query.data.name}</h1><p className="intro">Effective versions and recorded review rules.</p></div><button disabled={query.isFetching} onClick={() => void query.refetch()}>Refresh history</button></div>
      <p className="context-note">Periods include the start date and exclude the end date. Synthetic configuration is not historical approval evidence.</p>
      {!query.data.versions.length ? <div className="state-panel">No versions recorded.</div> : query.data.versions.map((v) => <section className="detail-card policy-version" key={v.id}>
        <h2>Version {v.version_number}</h2><p><strong>Effective:</strong> {v.effective_from} to {v.effective_to ? `${v.effective_to} (exclusive)` : 'no end date'}</p>
        <p><strong>Applies to:</strong> {v.gxp_classification} · {v.criticality} criticality</p><p className="context-note">{v.change_reason}</p><Rules rows={v.rules} /></section>)}
    </>}
  </>;
}
function today() { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; }
export function ApplicablePolicy({ applicationId }: { applicationId: string }) {
  const { identity } = useIdentity();
  const [day, setDay] = useState(today);
  const query = useQuery({ queryKey: ['application-policy', identity?.user_id, identity?.role, applicationId, day], queryFn: ({ signal }) => getResolution(applicationId, day, signal), refetchInterval: false });
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const value = new FormData(event.currentTarget).get('day'); if (typeof value === 'string' && value) setDay(value); }
  return <section className="detail-card policy-section"><h2>Applicable policy</h2><p className="context-note">Inspect policy defaults using the application's currently recorded classification and criticality. Obligations and governance health are not calculated here.</p>
    <form className="policy-date" onSubmit={submit}><label htmlFor="policy-day">Policy date</label><input id="policy-day" name="day" type="date" defaultValue={day} required /><button type="submit">Inspect date</button><button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>Refresh policy</button></form>
    {query.isPending ? <p role="status">Loading applicable policy…</p> : query.isError ? <Failure error={query.error} busy={query.isFetching} retry={() => void query.refetch()} /> : <>
      <p className="policy-result" role="status"><strong>{query.data.configuration}</strong> · {query.data.as_of} · {query.data.timezone}</p><p className="context-note">{query.data.explanation}</p>
      {query.data.candidates.map((p) => <p key={p.policy_version_id}><strong>{p.policy_name}</strong> · Version {p.version_number} · From {p.effective_from}{p.effective_to ? ` to ${p.effective_to} (exclusive)` : ''}</p>)}
      {query.data.configuration === 'Resolved' ? <Rules rows={query.data.rules} /> : null}
    </>}
  </section>;
}

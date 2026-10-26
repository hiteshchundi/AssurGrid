import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router';
import { completeObligation, getGovernance, type Obligation, type ObligationStatus } from '../../api/governance';
import { useIdentity } from '../auth/Auth';

export function Status({ value }: { value: string }) {
  return <span className={`status-badge status-${value.toLowerCase().replaceAll(' ', '-')}`}>{value}</span>;
}

function CompletionForm({ item, onClose }: { item: Obligation; onClose: () => void }) {
  const cache = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ reference, notes }: { reference: string; notes: string }) => completeObligation(item.id, reference, notes),
    onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['governance'] }); onClose(); },
  });
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    mutation.mutate({ reference: String(values.get('reference')).trim(), notes: String(values.get('notes')).trim() });
  }
  return <section className="completion-panel" aria-label={`Record completion for ${item.control_name}`}>
    <h3>Record completion</h3>
    <p>{item.application_name} · {item.control_name}</p>
    <p className="context-note">{item.evidence_requirement} Record a reference to supporting evidence; files remain in their source repository.</p>
    <form onSubmit={submit}>
      <label>Evidence reference<input autoFocus name="reference" placeholder="e.g. DEMO-PCR-LIMS-2026 v1.0" maxLength={500} required pattern=".*\S.*" /></label>
      <label>Completion notes<textarea name="notes" placeholder="Describe what was reviewed and the outcome." maxLength={2000} required /></label>
      <p className="context-note">Saving preserves the original deadline and adds the next review using the recorded policy cadence. This shared sandbox stores synthetic evidence references only.</p>
      {mutation.isError ? <p className="notice" role="alert">{mutation.error.message}</p> : null}
      <div className="button-row"><button className="primary-button" disabled={mutation.isPending} type="submit">{mutation.isPending ? 'Saving…' : 'Save completion'}</button>
        <button disabled={mutation.isPending} type="button" onClick={onClose}>Cancel</button></div>
    </form>
  </section>;
}

export function ObligationList({ items, asOf }: { items: Obligation[]; asOf: string }) {
  const { identity } = useIdentity();
  const [selected, setSelected] = useState<Obligation | null>(null);
  const canComplete = identity?.role !== 'Viewer';
  return <>
    {selected ? <CompletionForm key={selected.id} item={selected} onClose={() => setSelected(null)} /> : null}
    {items.length ? <div className="obligation-list">{items.map(item => <article className="obligation-card" key={item.id}>
      <div className="obligation-title"><div><p className="eyebrow">{item.ci_id}</p><h3>{item.control_name}</h3>
        <Link to={`/applications/${item.application_id}`}>{item.application_name}</Link></div><Status value={item.status} /></div>
      <dl className="obligation-facts"><div><dt>Due date</dt><dd>{item.due_date}</dd></div>
        <div><dt>Cadence</dt><dd>Every {item.frequency_months} months</dd></div>
        <div><dt>Policy snapshot</dt><dd>Version {item.version_number} · {item.mandatory ? 'Mandatory' : 'Optional'}</dd></div>
        <div><dt>Time remaining</dt><dd>{item.status === 'Completed' ? 'Completion recorded' : item.days_remaining < 0 ? `${Math.abs(item.days_remaining)} days overdue` : `${item.days_remaining} days`}</dd></div></dl>
      {item.completed_at ? <div className="completion-evidence"><strong>Evidence: {item.evidence_reference}</strong><p>{item.notes}</p>
        <span>Recorded by {item.completed_by} · {new Date(item.completed_at).toLocaleString()}</span></div> :
        <div className="obligation-footer"><span>{item.evidence_requirement}</span>{canComplete && item.window_start <= asOf ?
          <button onClick={() => setSelected(item)}>Record completion</button> : <span>{canComplete ? 'Review window has not started' : 'Viewer · read-only'}</span>}</div>}
    </article>)}</div> : <div className="state-panel"><h3>No reviews in this view</h3><p>Choose another status or application. Missing schedules do not imply compliant governance.</p></div>}
  </>;
}

export function ApplicationGovernance({ applicationId }: { applicationId: string }) {
  const { identity } = useIdentity();
  const query = useQuery({ queryKey: ['governance', identity?.user_id, identity?.role, applicationId],
    queryFn: ({ signal }) => getGovernance(`application_id=${encodeURIComponent(applicationId)}`, signal), refetchInterval: false });
  if (query.isPending) return <section className="detail-card" role="status">Loading governance…</section>;
  if (query.isError) return <section className="detail-card" role="alert"><h2>Governance unavailable</h2><p>{query.error.message}</p><button onClick={() => void query.refetch()}>Try again</button></section>;
  return <section className="application-governance"><div className="page-heading"><div><h2>Governance & review evidence</h2>
    <p className="intro">As of {query.data.as_of} · {query.data.timezone}. Lifecycle and validation stay independent.</p></div>
    <Status value={query.data.applications[0]?.governance_health ?? 'Not scheduled'} /></div>
    <ObligationList items={query.data.items} asOf={query.data.as_of} /></section>;
}

export function GovernanceOverview() {
  const { identity } = useIdentity();
  const [params, setParams] = useSearchParams();
  const portfolio = useQuery({ queryKey: ['governance', identity?.user_id, identity?.role, 'filter-options'],
    queryFn: ({ signal }) => getGovernance('', signal), refetchInterval: false });
  const query = useQuery({ queryKey: ['governance', identity?.user_id, identity?.role, params.toString()],
    queryFn: ({ signal }) => getGovernance(params.toString(), signal), refetchInterval: false });
  const statuses: ObligationStatus[] = ['Overdue', 'Due soon', 'Upcoming', 'Completed'];
  function filterStatus(value: string) { const next = new URLSearchParams(params); value ? next.set('status', value) : next.delete('status'); setParams(next); }
  return <>
    <div className="page-heading"><div><p className="eyebrow">Northstar Biopharma · Oversight workspace</p><h1>What needs your attention?</h1>
      <p className="intro">Follow each deadline from the portfolio to its application, policy, and completion evidence.</p></div>
      <button disabled={query.isFetching} onClick={() => void query.refetch()}>{query.isFetching ? 'Refreshing…' : 'Refresh overview'}</button></div>
    {query.isPending ? <div className="state-panel" role="status">Loading your governance workspace… The free demo server may take a minute to wake up.</div> :
      query.isError ? <div className="state-panel error-panel" role="alert"><h2>Overview unavailable</h2><p>{query.error.message}</p><button onClick={() => void query.refetch()}>Try again</button></div> : <>
      <div className="metric-grid">{statuses.map(status => <button key={status} className={`metric-card ${params.get('status') === status ? 'selected' : ''}`} onClick={() => filterStatus(params.get('status') === status ? '' : status)}>
        <span>{status}</span><strong>{query.data.counts[status]}</strong><small>{status === 'Completed' ? 'Evidence recorded' : 'Review obligations'} →</small></button>)}</div>
      <p className="context-note">Live evaluation: {query.data.as_of} · {query.data.timezone} · {query.data.applications.length} applications in your access scope. Deadlines are fictional; “Current” describes scheduled reviews only.</p>
      <section className="filter-panel governance-filters" aria-label="Filter reviews"><label>Review status<select value={params.get('status') ?? ''} onChange={event => filterStatus(event.target.value)}><option value="">All reviews</option>{statuses.map(status => <option key={status}>{status}</option>)}</select></label>
        <label>Application<select value={params.get('application_id') ?? ''} onChange={event => { const next = new URLSearchParams(params); event.target.value ? next.set('application_id', event.target.value) : next.delete('application_id'); setParams(next); }}>
          <option value="">All accessible applications</option>{(portfolio.data?.applications ?? query.data.applications).map(item => <option key={item.id} value={item.id}>{item.ci_id} · {item.name}</option>)}</select></label>
        <button onClick={() => setParams({})}>Clear filters</button></section>
      <div className="section-heading"><h2>{params.get('status') ?? 'All scheduled reviews'}</h2><span>{query.data.items.length} records</span></div>
      <ObligationList items={query.data.items} asOf={query.data.as_of} />
      <section className="coverage-panel detail-card"><h2>Schedule coverage</h2><p>{query.data.applications.filter(item => item.governance_health === 'Not scheduled').length} applications have no mandatory open review schedule in this scope. Inspect policy applicability before drawing a governance conclusion.</p><Link to="/applications">Explore the application registry →</Link></section>
      </>}
  </>;
}

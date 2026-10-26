import { useIdentity } from '../auth/Auth';
import type { FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router';
import { getApplications } from '../../api/applications';
import { getGovernance } from '../../api/governance';
import { Status } from '../governance/Governance';

const filterOptions = [
  { name: 'classification', label: 'GxP classification', values: ['GxP', 'Non-GxP'] },
  { name: 'criticality', label: 'Criticality', values: ['High', 'Medium', 'Low'] },
  { name: 'lifecycle_state', label: 'Lifecycle', values: ['Implementation', 'Operational', 'Retirement', 'Retired'] },
  { name: 'validation_state', label: 'Validation', values: ['Not Assessed', 'Validation Required', 'In Validation', 'Validated', 'Remediation Required'] },
];

export function ApplicationRegistry() {
  const { identity } = useIdentity();
  const [params, setParams] = useSearchParams();
  const queryString = params.toString();
  const governance = useQuery({ queryKey: ['governance', identity?.user_id, identity?.role, 'registry'],
    queryFn: ({ signal }) => getGovernance('', signal), refetchInterval: false });
  const health = new Map(governance.isError ? [] : governance.data?.applications.map(item => [item.id, item.governance_health]));
  const query = useQuery({
    queryKey: ['applications', identity?.user_id, identity?.role, queryString], queryFn: ({ signal }) => getApplications(queryString, signal),
    refetchInterval: false, staleTime: 30000,
  });

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = new URLSearchParams();
    for (const [key, value] of new FormData(event.currentTarget)) {
      if (typeof value === 'string' && value.trim()) next.set(key, value.trim());
    }
    setParams(next);
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(params);
    next.set('page', String(page));
    setParams(next);
  }

  const data = query.data;
  return (
    <>
      <div className="page-heading">
        <div><p className="eyebrow">Application oversight</p><h1>Application registry</h1>
          <p className="intro">Find a system, understand its purpose, and inspect its recorded state.</p></div>
        <button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>
          {query.isFetching ? 'Refreshing…' : 'Refresh records'}
        </button>
      </div>
      <form className="filter-panel" key={queryString} onSubmit={applyFilters} aria-label="Filter applications">
        <div className="search-row">
          <label className="search-field" htmlFor="application-search">Search applications
            <input id="application-search" name="search" type="search" maxLength={100}
              defaultValue={params.get('search') ?? ''} placeholder="Application name or CI ID" />
          </label>
          <button className="primary-button" type="submit">Apply filters</button>
          <button type="button" onClick={(event) => { event.currentTarget.form?.reset(); setParams({}); }}>Clear filters</button>
        </div>
        <div className="filter-fields">
          {filterOptions.map(({ name, label, values }) => (
            <label key={name} htmlFor={name}>{label}
              <select id={name} name={name} defaultValue={params.get(name) ?? ''}>
                <option value="">All</option>
                {values.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          ))}
          <label htmlFor="page-size">Rows per page
            <select id="page-size" name="page_size" defaultValue={params.get('page_size') ?? '20'}>
              <option value="20">20</option><option value="50">50</option><option value="100">100</option>
            </select>
          </label>
        </div>
      </form>
      <p className="context-note">Lifecycle, validation, and governance are independent. Governance reflects open mandatory review schedules; an absent schedule does not imply compliance.</p>
      {query.isPending ? <div className="state-panel" role="status">Loading applications…</div> :
        query.isError ? <div className="state-panel error-panel" role="alert"><h2>Registry unavailable</h2><p>{query.error.message}</p>
          <button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>Try again</button></div> : data ? (
          <section className="registry-results" aria-label="Application results" aria-busy={query.isFetching}>
            <div className="results-heading"><h2>Applications</h2><span role="status">{data.total} matching {data.total === 1 ? 'application' : 'applications'}</span></div>
            {data.items.length === 0 ? <div className="empty-state"><h3>{data.total === 0 ? 'No applications found' : 'No applications on this page'}</h3>
              <p>{data.total === 0 ? 'Try a different search or clear your filters. If the registry is empty, load the synthetic demo dataset.' : 'Return to the first page to see the matching applications.'}</p>
              <button type="button" onClick={() => data.total === 0 ? setParams({}) : goToPage(1)}>{data.total === 0 ? 'Clear filters' : 'First page'}</button>
            </div> : <div className="table-scroll" role="region" aria-label="Applications table" tabIndex={0}>
              <table>
                <caption className="visually-hidden">Applications sorted by CI ID. Open a name to inspect the record.</caption>
                <thead><tr><th scope="col">Application / CI ID</th><th scope="col">System type</th><th scope="col">GxP</th><th scope="col">Criticality</th><th scope="col">Lifecycle</th><th scope="col">Validation</th><th scope="col">Governance</th></tr></thead>
                <tbody>{data.items.map((item) => <tr key={item.id}>
                  <th scope="row"><Link to={`/applications/${item.id}${queryString ? `?${queryString}` : ''}`}>{item.name}</Link><span className="ci-id">{item.ci_id}</span></th>
                  <td>{item.system_type}</td><td>{item.gxp_classification}</td><td>{item.criticality}</td>
                  <td><span className="state-label">{item.lifecycle_state}</span></td><td>{item.validation_state}</td><td><Status value={governance.isError ? 'Unavailable' : health.get(item.id) ?? 'Checking'} /></td>
                </tr>)}</tbody>
              </table>
            </div>}
            <div className="pagination">
              <span>{data.total === 0 ? 'No results' : `Page ${data.page} of ${Math.ceil(data.total / data.page_size)}`}</span>
              <div><button type="button" disabled={data.page <= 1 || query.isFetching} onClick={() => goToPage(data.page - 1)}>Previous</button>
                <button type="button" disabled={data.page * data.page_size >= data.total || query.isFetching} onClick={() => goToPage(data.page + 1)}>Next</button></div>
            </div>
          </section>
        ) : null}
    </>
  );
}

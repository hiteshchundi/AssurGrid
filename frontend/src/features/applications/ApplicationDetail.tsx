import { ApplicablePolicy } from '../policies/PolicyViews';
import { useIdentity } from '../auth/Auth';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useParams } from 'react-router';
import { getApplication, RegistryError } from '../../api/applications';
import { ApplicationGovernance } from '../governance/Governance';

function timestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
  }).format(date);
}

export function ApplicationDetail() {
  const { identity } = useIdentity();
  const { id = '' } = useParams();
  const { search } = useLocation();
  const query = useQuery({
    queryKey: ['application', identity?.user_id, identity?.role, id], queryFn: ({ signal }) => getApplication(id, signal),
    refetchInterval: false, staleTime: 30000,
  });
  const item = query.data;
  return (
    <>
      <Link className="back-link" to={`/applications${search}`}>← Back to application registry</Link>
      {query.isPending ? <div className="state-panel" role="status">Loading application…</div> :
        query.isError ? <div className="state-panel error-panel" role="alert">
          <h1>{query.error instanceof RegistryError && query.error.status === 404 ? 'Application not found' : 'Application unavailable'}</h1>
          <p>{query.error.message}</p><button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>Try again</button>
        </div> : item ? <>
          <div className="page-heading"><div><p className="eyebrow">{item.ci_id} · {item.system_type}</p><h1>{item.name}</h1>
            <p className="intro">Application record · {item.gxp_classification} · {item.criticality} criticality</p></div>
            <button type="button" disabled={query.isFetching} onClick={() => void query.refetch()}>{query.isFetching ? 'Refreshing…' : 'Refresh record'}</button>
          </div>
          <section className="state-summary" aria-label="Independent application states">
            <div><h2>Lifecycle</h2><p>{item.lifecycle_state}</p><span>Where the system is in its lifecycle</span></div>
            <div><h2>Validation</h2><p>{item.validation_state}</p><span>Recorded validation state</span></div>
            <div><h2>Governance</h2><p><a href="#governance-reviews">Review schedules ↓</a></p><span>Calculated from concrete obligations below</span></div>
          </section>
          <ApplicablePolicy key={item.id} applicationId={item.id} />
          <div id="governance-reviews"><ApplicationGovernance applicationId={item.id} /></div>
          <div className="detail-grid">
            <section className="detail-card"><h2>System overview</h2><p className="description">{item.description ?? 'No description recorded.'}</p>
              <dl className="detail-fields"><div><dt>CI ID</dt><dd>{item.ci_id}</dd></div><div><dt>System type</dt><dd>{item.system_type}</dd></div>
                <div><dt>Supplier</dt><dd>{item.supplier ?? 'Not recorded'}</dd></div><div><dt>Platform</dt><dd>{item.platform ?? 'Not recorded'}</dd></div></dl>
            </section>
            <section className="detail-card"><h2>Ownership</h2><p className="context-note">Owner assignments are not available in this prototype yet.</p>
              <dl className="detail-fields"><div><dt>Business owner</dt><dd>{item.business_owner_id ?? 'Not recorded'}</dd></div>
                <div><dt>Technical owner</dt><dd>{item.technical_owner_id ?? 'Not recorded'}</dd></div><div><dt>Quality owner</dt><dd>{item.quality_owner_id ?? 'Not recorded'}</dd></div></dl>
            </section>
            <section className="detail-card record-details"><h2>Record details</h2><p className="context-note">Synthetic seed timestamps describe the fixture, not verified business events. Times use your browser’s timezone.</p>
              <dl className="detail-fields"><div><dt>Created</dt><dd><time dateTime={item.created_at}>{timestamp(item.created_at)}</time></dd></div>
                <div><dt>Last updated</dt><dd><time dateTime={item.updated_at}>{timestamp(item.updated_at)}</time></dd></div>
                <div><dt>Application ID</dt><dd className="record-id">{item.id}</dd></div><div><dt>Organization ID</dt><dd className="record-id">{item.organization_id}</dd></div></dl>
            </section>
          </div>
        </> : null}
    </>
  );
}

import { NavLink, Outlet } from 'react-router';
import { SessionControl, useIdentity } from '../features/auth/Auth';

export function AppLayout() {
  const { identity } = useIdentity();
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="app-header">
        <NavLink className="brand-link" to="/overview" aria-label="AssurGrid overview">
          <span className="brand-mark" aria-hidden="true">AG</span><span className="brand">AssurGrid</span>
        </NavLink>
        <nav className="primary-nav" aria-label="Main navigation">
          <NavLink to="/overview">Overview</NavLink>
          <NavLink to="/applications">Application registry</NavLink>
          {identity?.role === 'Admin' || identity?.role === 'Quality' ? <NavLink to="/policies">Governance policies</NavLink> : null}
          <NavLink to="/foundation">Foundation status</NavLink>
        </nav>
        <SessionControl />
      </header>
      <div className="demo-banner"><strong>SYNTHETIC DEMO DATA</strong><span>Shared fictional sandbox · No company records · Illustrative policies</span></div>
      <main id="main-content" tabIndex={-1}><Outlet /></main>
    </div>
  );
}

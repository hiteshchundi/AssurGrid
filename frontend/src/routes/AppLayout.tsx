import { NavLink, Outlet } from 'react-router';
import { SessionControl } from '../features/auth/Auth';

export function AppLayout() {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="app-header">
        <NavLink className="brand-link" to="/applications" aria-label="AssurGrid application registry">
          <span className="brand-mark" aria-hidden="true">AG</span><span className="brand">AssurGrid</span>
        </NavLink>
        <nav className="primary-nav" aria-label="Main navigation">
          <NavLink to="/applications">Application registry</NavLink>
          <NavLink to="/foundation">Foundation status</NavLink>
        </nav>
        <SessionControl />
      </header>
      <div className="demo-banner"><strong>SYNTHETIC DEMO DATA</strong><span>Fictional records for demonstration. Read-only access.</span></div>
      <main id="main-content" tabIndex={-1}><Outlet /></main>
    </div>
  );
}

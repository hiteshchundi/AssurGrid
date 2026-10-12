import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router';

import { FoundationStatus } from './routes/FoundationStatus';
import { AppLayout } from './routes/AppLayout';
import { ApplicationRegistry } from './features/applications/ApplicationRegistry';
import { ApplicationDetail } from './features/applications/ApplicationDetail';
import './styles/global.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchInterval: 10000 } },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/applications" replace />} />
            <Route path="/applications" element={<ApplicationRegistry />} />
            <Route path="/applications/:id" element={<ApplicationDetail />} />
            <Route path="/foundation" element={<FoundationStatus />} />
            <Route path="*" element={<div className="state-panel"><h1>Page not found</h1><Link to="/applications">Return to application registry</Link></div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);

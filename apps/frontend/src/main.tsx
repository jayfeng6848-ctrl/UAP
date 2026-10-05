/**
 * Application entry (Appendix AL H11).
 *
 * The STEP-0 skeleton page (a bare `/api/v1/meta` fetch) is replaced by the real
 * foundation: design tokens → global reset → App (providers → router → shell).
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './app/App';
import './platform/design/tokens.css';
import './platform/design/global.css';

const container = document.getElementById('root');
if (container === null) {
  throw new Error('UAP Console root element is missing');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

import { defineConfig, devices } from '@playwright/test';

/**
 * Minimal E2E baseline: the app must boot.
 *
 * The suite runs against the production preview server (same-origin SPA, per
 * Appendix AL H11). No backend dependency is required for the boot check and no
 * Company business flow is touched.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    // Bind IPv4 explicitly: `vite preview` otherwise listens on [::1] only.
    baseURL: 'http://127.0.0.1:4173',
    trace: 'off',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run preview -- --port 4173 --strictPort --host 127.0.0.1',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
});

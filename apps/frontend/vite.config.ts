import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const API_TARGET = process.env.VITE_API_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  build: {
    // Same-origin SPA (Appendix AL H11): the bundle never embeds an API target.
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/health': { target: API_TARGET, changeOrigin: true },
      '/ready': { target: API_TARGET, changeOrigin: true },
      // Authentication surface (required by the Foundation auth bootstrap).
      '/me': { target: API_TARGET, changeOrigin: true },
      '/sessions': { target: API_TARGET, changeOrigin: true },
      '/identity': { target: API_TARGET, changeOrigin: true },
      '/devices': { target: API_TARGET, changeOrigin: true },
      // Company UI (HD-P21-01): the frozen P20 namespace lives at /company/... and the
      // P17 structure read used for the assignment space picker is
      // GET /tenants/{tenant_id}/spaces.
      //
      // `/company` never collides with an SPA route, so a prefix rule is safe. `/tenants`
      // DOES collide (the console's own routes live under /tenants/:tenant_id/company/...),
      // so the space read is proxied by an anchored pattern instead of a whole prefix —
      // a deep link such as /tenants/<id>/company/employees keeps serving the SPA.
      // Development-only routing; production is same-origin behind a reverse proxy.
      '/company': { target: API_TARGET, changeOrigin: true },
      '^/tenants/[^/]+/spaces': { target: API_TARGET, changeOrigin: true },
      // Customer AI onboarding (HD-P21-17). The trailing slash matters: the SPA's own
      // customer entry is exactly `/ai`, so only the API namespace `/ai/...`
      // (connection / messages) is proxied and the entry route keeps serving the SPA.
      '/ai/': { target: API_TARGET, changeOrigin: true },
      // Company Intelligence Facade (P21 Company UI · OQ-CUI-03/-09). Same rule as
      // `/ai/`: the SPA has no `/intelligence` route of its own, so the whole
      // namespace is proxied to the backend — never a second API target, and the
      // provider secret never passes through here (the proxy only forwards bytes).
      '/intelligence': { target: API_TARGET, changeOrigin: true },
    },
  },
});

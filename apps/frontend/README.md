# UAP Frontend

Status: **Platform UI foundation** (Appendix AL). The Foundation (shell, routing,
auth context, tenant context, typed API client, error system, design tokens, UI
primitives, test baseline) is implemented. **Company UI is NOT implemented** —
`src/modules/company/` is a placeholder boundary only.

## Stack

- React + Vite + TypeScript (frozen by Appendix AL H01); React Router for routing
- Native `fetch` based typed API client (no Axios)
- UAP design tokens + CSS Modules (no component framework)
- Vitest + React Testing Library (unit/component) · Playwright (E2E baseline)

## Commands

```bash
npm install
npm run dev            # http://localhost:5173 (proxies /api, /health, /ready, auth surface)
npm run typecheck
npm run test:run
npm run test:coverage
npm run build          # → dist/
npm run e2e
```

## Rules

- The frontend talks to the API only. It never imports backend packages.
- The frontend never decides authorization: the backend is the security boundary
  (`403` is the final denial). There is no frontend ACL engine.
- Auth tokens are memory-only: never persisted to `localStorage`/`sessionStorage`.
- Secrets are never bundled; only public client configuration (see `.env.example`).
- Company pages belong to a later, separately authorized stage.

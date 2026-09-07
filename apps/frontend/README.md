# UAP Frontend

Status: **skeleton only** (STEP 0). It exists so the project has a defined
place for the web client; no product UI has been built.

## Stack

- Vite + React + TypeScript
- Dev server proxies `/api`, `/health`, `/ready` to the API (`VITE_API_TARGET`,
  default `http://localhost:8000`)

## Commands

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

## Rules

- The frontend talks to the API only. It never imports backend packages.
- Secrets are never bundled; runtime config comes from the environment.

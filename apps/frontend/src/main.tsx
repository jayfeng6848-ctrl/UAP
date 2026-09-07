import React from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [meta, setMeta] = React.useState<Record<string, unknown> | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch('/api/v1/meta')
      .then((res) => res.json())
      .then(setMeta)
      .catch((err) => setError(String(err)));
  }, []);

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32 }}>
      <h1>UAP Console</h1>
      <p>Universal AI Platform — STEP 0 foundation.</p>
      {error && <p style={{ color: 'crimson' }}>Backend unreachable: {error}</p>}
      {meta && <pre>{JSON.stringify(meta, null, 2)}</pre>}
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);

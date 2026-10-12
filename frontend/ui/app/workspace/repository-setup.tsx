"use client";

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';

type Configuration = { framework: 'npm' | 'pytest'; test_files: string[]; editable_files: string[] };
export type RepositorySetup = { status: string; source_sha?: string; configuration?: Configuration; result?: { message?: string; output?: string; exit_code?: number } };

export default function RepositorySetupForm({ repository, csrf, initial, onReady }: {
  repository: string; csrf: string; initial?: RepositorySetup; onReady: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [setup, setSetup] = useState<RepositorySetup>(initial || {status:'not_configured'});
  const [framework, setFramework] = useState<'npm' | 'pytest'>(initial?.configuration?.framework || 'npm');
  const [tests, setTests] = useState(initial?.configuration?.test_files.join('\n') || 'package.json\npackage-lock.json\n');
  const [files, setFiles] = useState(initial?.configuration?.editable_files.join('\n') || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const endpoint = `/api/repositories/${repository}/setup`;
  const readyCallback = useRef(onReady);
  useEffect(() => { readyCallback.current = onReady; }, [onReady]);

  useEffect(() => {
    if (setup.status !== 'validating') return;
    let alive = true;
    const controller = new AbortController();
    const timer = setInterval(async () => {
      try {
        const next = await api<RepositorySetup>(endpoint, {signal:controller.signal});
        if (!alive) return;
        setSetup(next); setError('');
        if (next.status === 'ready') readyCallback.current();
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : 'Could not refresh validation.');
      }
    }, 10000);
    return () => { alive=false; controller.abort(); clearInterval(timer); };
  }, [endpoint, setup.status]);

  async function validate(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    const lines = (value: string) => value.split('\n').map(p=>p.trim()).filter(Boolean);
    try {
      setSetup(await api<RepositorySetup>(endpoint, {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:JSON.stringify({framework,test_files:lines(tests),editable_files:lines(files)})}));
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not start validation.'); }
    finally { setBusy(false); }
  }

  return <div className="mt-2">
    <button type="button" onClick={()=>setOpen(!open)} aria-expanded={open} className="text-xs font-medium underline">{open ? 'Close test setup' : 'Set up tests'}</button>
    {open && <form onSubmit={validate} className="mt-3 space-y-3 rounded-xl border border-zinc-200 bg-zinc-50 p-3">
      <p className="text-xs text-zinc-600">Pass a hosted validation run to enable this repository automatically. Public repositories only.</p>
      <label className="block text-xs font-medium">Test environment
        <select value={framework} onChange={e=>{const value=e.target.value as 'npm'|'pytest';setFramework(value);setTests(value==='npm'?'package.json\npackage-lock.json\n':'');}} disabled={setup.status==='validating'} className="mt-1 w-full rounded border bg-white p-2">
          <option value="npm">Node.js — Vitest, Jest or node:test</option><option value="pytest">Python — pytest</option>
        </select>
      </label>
      <p className="text-xs text-zinc-500">{framework==='npm' ? 'Requires a lockfile and test script exactly “vitest run”, “jest --runInBand” or “node --test”. Dependency install hooks are disabled.' : 'Python 3.11 with pytest. Third-party project dependencies are not supported yet.'}</p>
      <label className="block text-xs font-medium">Test files and configuration (one path per line)
        <textarea required value={tests} onChange={e=>setTests(e.target.value)} disabled={setup.status==='validating'} rows={4} placeholder={framework==='npm'?'package.json\npackage-lock.json\ntests/example.test.ts\nvitest.config.ts':'tests/test_example.py\nconftest.py'} className="mt-1 w-full rounded border bg-white p-2 font-mono text-xs"/>
      </label>
      <p className="text-xs text-zinc-500">Include test helpers and configuration. Up to 10 files, frozen at the validation commit.</p>
      <label className="block text-xs font-medium">Source files TORQUE may edit (one path per line)
        <textarea required value={files} onChange={e=>setFiles(e.target.value)} disabled={setup.status==='validating'} rows={3} placeholder="src/example.ts" className="mt-1 w-full rounded border bg-white p-2 font-mono text-xs"/>
      </label>
      <button disabled={busy || setup.status==='validating'} className="rounded-lg bg-black px-3 py-2 text-xs font-medium text-white disabled:opacity-40">{busy ? 'Starting…' : setup.status==='validating' ? 'Validating tests…' : 'Validate and enable'}</button>
      <p role="status" className="text-xs">{setup.result?.message || (setup.status==='validating' ? 'Tests are running. This panel refreshes automatically.' : '')}</p>
      {setup.source_sha && <p className="text-xs text-zinc-500">Test revision: {setup.source_sha.slice(0,7)}</p>}
      {setup.result?.output && <details><summary className="cursor-pointer text-xs">Validation output</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all text-xs">{setup.result.output}</pre></details>}
      {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
    </form>}
  </div>;
}

"use client";

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowRight, Check, ExternalLink, GitPullRequest, LoaderCircle, LogOut, Play, RefreshCw } from 'lucide-react';
import { api, ApiError, githubLogin } from '@/lib/api';
import RepositorySetupForm, { type RepositorySetup } from './repository-setup';

type Session = { user_id: string; github_login: string; csrf_token: string };
type Repository = { full_name: string; run_supported: boolean; run_reason?: string | null; setup?: RepositorySetup; permissions: { push?: boolean }; app_permissions: { contents?: string; pull_requests?: string } };
type Run = { run_id: string; issue_url: string; status: string; created_at: number; updated_at?: number; current_agent?: string | null; error?: string | null; pr_url?: string | null;
  result?: { verified?: boolean; summary?: string; trace_id?: string; published_commit_sha?: string; plan?: {summary?: string; acceptance_criteria?: string[]}; budget?: { calls: number; tokens: number; estimated_cost_usd: number } };
  attempts?: { number: number; tests_passed: boolean; review?: { approved?: boolean; rationale?: string; satisfied_criteria?: number[] } }[] };
type RunEvent = {id: number; created_at: number; status?: string; error?: string | null};
const terminal = new Set(['completed','failed','cancelled','interrupted','ready_to_publish']);
const stages = ['queued','investigating','implementing','recovering','verifying','ready_to_publish','publishing','completed'];
const label = (value: string) => value.replaceAll('_',' ').replace(/^./, s => s.toUpperCase());
const safePR = (url?: string | null) => !!url && /^https:\/\/github\.com\/[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+\/pull\/[1-9][0-9]*$/.test(url);

export default function Workspace() {
  const router=useRouter();
  const [session,setSession] = useState<Session | null>(null);
  const [loading,setLoading] = useState(true);
  const [expired,setExpired] = useState(false);
  const [error,setError] = useState('');
  const [history,setHistory] = useState<Run[]>([]);
  const [repositories,setRepositories] = useState<Repository[]>([]);
  const [testRepository,setTestRepository] = useState('');
  const [automaticMessages,setAutomaticMessages] = useState<Record<string,string>>({});
  const repositorySnapshot = useRef<Repository[]>([]);
  useEffect(() => { repositorySnapshot.current = repositories; }, [repositories]);
  const [accessChecking,setAccessChecking] = useState(false);
  const [accessMessage,setAccessMessage] = useState('');
  const [issue,setIssue] = useState('');
  const [runId,setRunId] = useState('');
  const [run,setRun] = useState<Run | null>(null);
  const [events,setEvents] = useState<RunEvent[]>([]);
  const [progressError,setProgressError] = useState('');
  const [lastSynced,setLastSynced] = useState<number | null>(null);
  const [refreshRun,setRefreshRun] = useState(0);
  const [destination,setDestination] = useState('');
  const [busy,setBusy] = useState(false);
  const [submitting,setSubmitting] = useState(false);
  const [retry,setRetry] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const key = useRef<{ issue: string; value: string } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let alive = true;
    async function load() {
      setLoading(true); setError('');
      try {
        const user = await api<Session>('/api/auth/session',{signal:controller.signal});
        if (!alive) return;
        setSession(user); setExpired(false);
        const results = await Promise.allSettled([
          api<{runs:Run[]}>('/api/runs',{signal:controller.signal}),
          api<{repositories:Repository[]}>('/api/auth/github/repositories',{signal:controller.signal})
        ]);
        if (!alive) return;
        if (results[0].status === 'fulfilled') {
          setHistory(results[0].value.runs);
          const active = results[0].value.runs.find(item => !terminal.has(item.status));
          const selected=active || results[0].value.runs[0];
          if (selected) setRunId(selected.run_id);
        }
        if (results[1].status === 'fulfilled') setRepositories(results[1].value.repositories);
        for (const result of results) if (result.status === 'rejected') throw result.reason;
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) { setExpired(true); setSession(null); }
        else setError(e instanceof Error ? e.message : 'Could not load workspace.');
      } finally { if (alive) setLoading(false); }
    }
    void load();
    return () => { alive = false; controller.abort(); };
  },[retry]);

  useEffect(() => {
    if (!runId || !session) return;
    const controller = new AbortController();
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    let cursor=0;
    let recorded: RunEvent[]=[];
    async function poll() {
      try {
        const current = await api<Run>('/api/runs/'+runId,{signal:controller.signal});
        if (!alive) return;
        setRun(current);
        setHistory(previous=>previous.map(item=>item.run_id===current.run_id ? {...item,status:current.status,pr_url:current.pr_url} : item));
        const batch=await api<{events:RunEvent[]}>(`/api/runs/${runId}/events?after=${cursor}`,{signal:controller.signal});
        if (!alive) return;
        recorded=[...recorded,...batch.events];
        if (batch.events.length) cursor=batch.events[batch.events.length-1].id;
        setEvents(recorded);setProgressError('');setLastSynced(Date.now());
        // Drain full event pages even after a run has finished.
        if (terminal.has(current.status) && batch.events.length<100) return;
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) { setExpired(true); setSession(null); return; }
        setProgressError(e instanceof Error ? e.message : 'Progress unavailable.');
        if (e instanceof ApiError && e.status === 404) return;
      }
      if (alive) timer=setTimeout(poll,2500);
    }
    void poll();
    return () => { alive=false; controller.abort(); clearTimeout(timer); };
  },[runId,session,refreshRun]);

  useEffect(() => {
    if (!session) return;
    let alive = true, checking = false;
    const attempted = new Set<string>();
    const controller = new AbortController();
    async function checkTests() {
      if (checking) return;
      checking = true;
      try {
        for (const repo of repositorySnapshot.current) {
          if (!alive || repo.run_supported) continue;
          const pending = repo.setup?.status === 'validating';
          if (!pending && (repo.setup?.status !== 'not_configured' || attempted.has(repo.full_name))) continue;
          const endpoint = `/api/repositories/${repo.full_name}/setup`;
          try {
            const setup = await api<RepositorySetup>(pending ? endpoint : endpoint+'/automatic', {
              method: pending ? 'GET' : 'POST', signal:controller.signal,
              headers: pending ? {} : {'X-CSRF-Token':session!.csrf_token}
            });
            if (!alive) return;
            attempted.add(repo.full_name);
            setAutomaticMessages(current => { const next = {...current}; delete next[repo.full_name]; return next; });
            setRepositories(current => current.map(item => item.full_name === repo.full_name
              ? {...item, setup, run_supported:setup.status === 'ready'} : item));
          } catch (e) {
            if (!alive) return;
            if (e instanceof ApiError && e.status === 401) { setExpired(true); setSession(null); return; }
            if (e instanceof ApiError && (e.status === 429 || e.status === 409 || e.status >= 500)) {
              setAutomaticMessages(current => ({...current,[repo.full_name]:'Automatic validation is waiting; retrying shortly.'}));
              break;
            }
            attempted.add(repo.full_name);
            setAutomaticMessages(current => ({...current,[repo.full_name]:e instanceof Error ? e.message : 'Manual test setup needed.'}));
          }
        }
      } finally { checking = false; }
    }
    void checkTests();
    const timer = setInterval(()=>void checkTests(),10000);
    return () => { alive=false;controller.abort();clearInterval(timer); };
  }, [session]);

  async function action(path: string, body?: object, idempotency?: string) {
    if (!session) throw new Error('Connect GitHub first.');
    return api<Run & {run_id:string}>(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf_token,...(idempotency ? {'Idempotency-Key':idempotency} : {})},body:body ? JSON.stringify(body) : undefined});
  }
  async function perform(fn: () => Promise<void>) {
    setBusy(true); setError('');
    try { await fn(); }
    catch(e) {
      if (e instanceof ApiError && e.status===401) { setSession(null); setExpired(true); }
      setError(e instanceof Error ? e.message : 'Action failed.');
    } finally { setBusy(false); }
  }
  async function reconfirmAccess() {
    setAccessChecking(true); setAccessMessage('');
    try {
      await perform(async () => {
        const saved = await api<{repositories:Repository[]}>('/api/auth/github/repositories');
        setRepositories(saved.repositories);
        setAccessMessage(saved.repositories.length
          ? `Access rechecked. Torque can access ${saved.repositories.length} ${saved.repositories.length === 1 ? 'repository' : 'repositories'}.`
          : 'No accessible repositories found. Check your Torque GitHub App installation.');
      });
    } finally { setAccessChecking(false); }
  }
  function submit(e: React.FormEvent) {
    e.preventDefault();
    const value=issue.trim();
    if (!/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/issues\/[1-9][0-9]*$/.test(value)) { setError('Enter a GitHub issue URL, such as https://github.com/owner/repo/issues/4.'); return; }
    const repository=value.split('/').slice(3,5).join('/');
    const source=repositories.find(repo => repo.full_name.toLowerCase()===repository.toLowerCase());
    if (!source) { setError('Install the Torque GitHub App on this source repository, then refresh access.'); return; }
    if (!source.run_supported) { setError(source.run_reason || 'This repository is not supported yet.'); return; }
    if (!key.current || key.current.issue!==value) key.current={issue:value,value:crypto.randomUUID()};
    setSubmitting(true);setRunId('');setRun(null);setEvents([]);setLastSynced(null);setProgressError('');setDestination('');
    void perform(async () => {
      try {
        const saved=await action('/api/runs',{issue_url:value},key.current!.value);
        key.current=null;
        setRun({run_id:saved.run_id,issue_url:value,status:saved.status,created_at:Date.now()/1000});
        setRunId(saved.run_id);
        const list=await api<{runs:Run[]}>('/api/runs');setHistory(list.runs);
      } finally { setSubmitting(false); }
    });
  }
  const active=!!run && !terminal.has(run.status);
  const hasActive=active || history.some(item => !terminal.has(item.status));
  const visited=new Set(events.map(event=>event.status));
  const review=run?.attempts?.at(-1)?.review;
  const writable=repositories.filter(repo => repo.permissions.push && repo.app_permissions.contents==='write' && repo.app_permissions.pull_requests==='write');

  return <div className="min-h-screen bg-[#fafafa]">
    <header className="border-b border-zinc-200 bg-white"><nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <Link href="/" className="text-2xl font-bold tracking-tight">torque<span className="text-zinc-400">.</span></Link>
      {session && <button disabled={busy} onClick={() => dialog.current?.showModal()} className="flex items-center gap-2 rounded-xl border border-zinc-200 px-4 py-2 text-sm hover:bg-zinc-100 disabled:opacity-50"><LogOut size={16}/>Disconnect GitHub</button>}
    </nav></header>
    <main className="mx-auto max-w-6xl px-6 py-12 sm:py-16">
      {loading ? <p role="status" className="flex items-center gap-3"><LoaderCircle className="animate-spin" size={20}/>Loading your workspace…</p> : !session ? <section className="rounded-3xl border border-zinc-200 bg-white p-10">
        <h1 className="text-4xl font-semibold">Your Torque workspace</h1><p className="my-5 text-lg text-zinc-600">{expired ? 'Connect GitHub to access your runs.' : 'We could not load your session. Check the API and try again.'}</p>
        <button onClick={githubLogin} className="rounded-xl bg-black px-6 py-3 font-medium text-white">Connect GitHub</button><button onClick={() => setRetry(value=>value+1)} className="ml-4 underline">Retry</button>
      </section> : <>
        <div className="mb-10"><p className="mb-3 text-sm font-medium uppercase tracking-widest text-zinc-500">Your workspace</p><h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Hello, {session.github_login} <span className="torque-wave inline-block" role="img" aria-label="waving hand">👋</span></h1><p className="mt-4 text-lg text-zinc-500">Give Torque an issue. Follow the fix from investigation to a verified pull request.</p></div>
        <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
          <section className="space-y-6">
            <form onSubmit={submit} className="rounded-3xl border border-zinc-200 bg-white p-6 sm:p-8">
              <label htmlFor="issue" className="text-xl font-semibold">What should we fix?</label><input id="issue" type="url" required value={issue} onChange={e=>setIssue(e.target.value)} placeholder="https://github.com/owner/repo/issues/4" className="mt-5 w-full rounded-xl border border-zinc-300 bg-zinc-50 px-4 py-4 text-base outline-none focus:ring-2 focus:ring-black"/>
              <p className="mt-3 text-sm text-zinc-500">Choose an issue in an installed repository with a supported test recipe.</p>
              {submitting && <p role="status" className="mt-3 text-sm">Submitting your issue…</p>}
              {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
              <button disabled={busy || hasActive || !repositories.some(repo=>repo.run_supported)} className="mt-6 flex items-center gap-2 rounded-xl bg-black px-6 py-3 font-semibold text-white hover:bg-zinc-800 disabled:opacity-40"><Play size={17}/>{busy ? 'Working…' : hasActive ? 'Run in progress' : 'Run Torque'}</button>
            </form>
            <section className="glass-panel relative overflow-hidden rounded-3xl p-6 sm:p-8" aria-label="Workflow progress">
              <div className="flex items-center justify-between gap-4"><h2 className="text-2xl font-semibold">{run ? label(run.status) : 'Ready when you are'}</h2>{active && <LoaderCircle className="animate-spin" aria-label="Run active" size={20}/>}</div>
              {!run ? <p className="mt-4 text-zinc-500">Your workflow will appear here when you start a run.</p> : <>
                <p className="mt-3 break-all text-sm text-zinc-500">{run.issue_url}</p>
                <ol className="mt-8 grid gap-3 sm:grid-cols-2">{stages.map((step,index) => <li key={step} aria-current={run.status===step ? 'step' : undefined} className={`flex items-center gap-3 rounded-xl border p-3 ${run.status===step ? 'border-black bg-white' : 'border-zinc-200 bg-white/40'}`}>
                  <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs ${visited.has(step) && run.status!==step ? 'bg-black text-white' : 'bg-zinc-100 text-zinc-500'}`}>{visited.has(step) && run.status!==step ? <Check size={14}/> : index+1}</span><span className="text-sm">{label(step)}{step==='recovering' && !visited.has(step) && run.status!==step ? ' (if needed)' : ''}</span>
                </li>)}</ol>
                <p role="status" className="mt-5 text-sm text-zinc-600">{run.status==='recovering' ? 'Recovery is analyzing the failed attempt before retrying.' : run.status==='queued' ? 'Waiting for the separate worker to pick up this run.' : run.current_agent ? `${label(run.current_agent)} is active.` : label(run.status)}</p>
                <div className="mt-3 flex items-center justify-between gap-3 text-xs text-zinc-500"><span>{lastSynced ? `Last checked ${new Date(lastSynced).toLocaleTimeString()}` : 'Checking progress…'}</span><button disabled={busy} onClick={()=>{setEvents([]);setProgressError('');setRefreshRun(value=>value+1);}} className="underline">Refresh progress</button></div>
                {progressError && <p role="alert" className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">Progress is temporarily unavailable. Showing the last saved result. {progressError}</p>}
                {run.result?.summary && <p className="mt-5 text-zinc-700">{run.result.summary}</p>}
                {run.error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{run.error}</p>}
                {run.result?.budget && <p className="mt-5 text-sm text-zinc-500">{run.result.budget.calls} model calls · {run.result.budget.tokens.toLocaleString()} tokens · ${run.result.budget.estimated_cost_usd.toFixed(4)} estimated</p>}
                {!!run.attempts?.length && <p className="mt-3 text-sm text-zinc-500">{run.attempts.length} recorded attempt(s) · latest tests {run.attempts.at(-1)?.tests_passed ? 'passed' : 'failed'}</p>}
                {!!run.result?.plan?.acceptance_criteria?.length && <div className="mt-6 border-t border-zinc-200 pt-5"><h3 className="font-semibold">Acceptance results</h3><ul className="mt-3 space-y-3">{run.result.plan.acceptance_criteria.map((criterion,index)=><li key={index} className="text-sm text-zinc-600"><span className="mr-2 font-medium text-zinc-900">{run.result?.verified && review?.approved && review.satisfied_criteria?.includes(index) ? 'Passed' : 'Not verified'}</span>{criterion}</li>)}</ul>{review?.rationale && <p className="mt-4 text-sm text-zinc-500">Review: {review.rationale}</p>}</div>}
                {run.result?.trace_id && <p className="mt-5 break-all text-xs text-zinc-500">Trace ID: <code>{run.result.trace_id}</code></p>}
                {run.result?.published_commit_sha && <p className="mt-2 break-all text-xs text-zinc-500">Published commit: <code>{run.result.published_commit_sha}</code></p>}
                {!!events.length && <details className="mt-6 border-t border-zinc-200 pt-4"><summary className="cursor-pointer font-medium">Activity ({events.length})</summary><ol className="mt-4 max-h-64 space-y-3 overflow-auto">{events.map(event=><li key={event.id} className="text-sm text-zinc-600"><time className="mr-3 text-xs text-zinc-400">{new Date(event.created_at*1000).toLocaleTimeString()}</time>{event.status ? label(event.status) : 'Run updated'}{event.error && <p className="mt-1 text-red-700">{event.error}</p>}</li>)}</ol></details>}
                {run.status==='ready_to_publish' && <div className="mt-6 border-t border-zinc-200 pt-6"><label htmlFor="destination" className="font-medium">Publish a draft PR</label><select id="destination" value={destination} onChange={e=>setDestination(e.target.value)} className="mt-3 w-full rounded-xl border border-zinc-300 bg-white p-3"><option value="">Choose your source repository or fork</option>{writable.map(repo=><option key={repo.full_name} value={repo.full_name}>{repo.full_name}</option>)}</select><p className="mt-2 text-sm text-zinc-500">The destination must be your own source or fork at the verified revision.</p><button disabled={busy || !destination} onClick={()=>void perform(async()=>{const published=await action(`/api/runs/${run.run_id}/publish?destination=${encodeURIComponent(destination)}`);setRun(published);setRefreshRun(value=>value+1);const saved=await api<{runs:Run[]}>('/api/runs');setHistory(saved.runs);})} className="mt-4 rounded-xl bg-black px-5 py-3 text-white disabled:opacity-40">Publish draft PR</button></div>}
                {safePR(run.pr_url) && <a href={run.pr_url!} target="_blank" rel="noopener noreferrer" className="mt-6 inline-flex items-center gap-2 rounded-xl bg-black px-5 py-3 font-medium text-white"><GitPullRequest size={18}/>View pull request<ExternalLink size={14}/></a>}
                {active && <button disabled={busy} onClick={()=>void perform(async()=>{setRun(await action('/api/runs/'+run.run_id+'/cancel'));})} className="mt-5 block text-sm text-zinc-600 underline disabled:opacity-40">Request cancellation</button>}
              </>}
            </section>
          </section>
          <aside className="space-y-6"><section className="rounded-3xl border border-zinc-200 bg-white p-6"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Repository access</h2><button aria-label="Refresh repository access" disabled={busy} onClick={()=>void perform(async()=>{const saved=await api<{repositories:Repository[]}>('/api/auth/github/repositories');setRepositories(saved.repositories);})}><RefreshCw size={16}/></button></div><p className="mt-3 text-sm text-zinc-500">{repositories.length ? 'Repositories connected through your GitHub App installation.' : 'Install the Torque App on a public repository, then refresh access.'}</p><ul className="mt-4 space-y-2">{repositories.map(repo=><li className="break-all text-sm" key={repo.full_name}>{repo.full_name}<span className={`ml-2 text-xs ${repo.run_supported ? 'text-emerald-700' : 'text-zinc-500'}`}>{repo.run_supported ? 'Ready to run' : repo.setup?.status === 'validating' ? 'Checking tests' : repo.setup?.status === 'failed' || automaticMessages[repo.full_name] ? 'Setup needed' : 'Connected ? detecting tests'}</span>{!repo.run_supported && (automaticMessages[repo.full_name] || repo.setup?.result?.message) && <p className="mt-1 text-xs text-zinc-500">{repo.setup?.result?.message || automaticMessages[repo.full_name]}</p>}</li>)}</ul><button type="button" disabled={busy || accessChecking} onClick={()=>void reconfirmAccess()} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-zinc-200 px-4 py-3 text-sm font-semibold hover:bg-zinc-50 disabled:opacity-40"><RefreshCw size={16} className={accessChecking ? 'animate-spin' : ''}/>{accessChecking ? 'Checking access?' : 'Reconfirm Torque access'}</button><p role="status" className="mt-3 text-sm text-zinc-600">{accessMessage}</p></section>
            {repositories.some(repo=>!repo.run_supported && (repo.setup?.status === 'failed' || automaticMessages[repo.full_name])) && <section className="rounded-3xl border border-zinc-200 bg-white p-6"><h2 className="text-lg font-semibold">Repository tests</h2><p className="mt-3 text-sm text-zinc-500">Torque checks supported tests automatically. If detection or validation needs help, configure the test files here.</p><label htmlFor="test-repository" className="mt-4 block text-sm font-medium">Repository</label><select id="test-repository" value={testRepository} onChange={e=>setTestRepository(e.target.value)} className="mt-2 w-full rounded-xl border border-zinc-200 bg-white p-3 text-sm"><option value="">Choose a repository</option>{repositories.filter(repo=>!repo.run_supported && (repo.setup?.status === 'failed' || automaticMessages[repo.full_name])).map(repo=><option key={repo.full_name} value={repo.full_name}>{repo.full_name}</option>)}</select>{testRepository && repositories.some(repo=>repo.full_name===testRepository) && <RepositorySetupForm key={testRepository} repository={testRepository} csrf={session.csrf_token} initial={repositories.find(repo=>repo.full_name===testRepository)?.setup} onReady={()=>void perform(async()=>{const saved=await api<{repositories:Repository[]}>('/api/auth/github/repositories');setRepositories(saved.repositories);})}/>}</section>}
            <section className="rounded-3xl border border-zinc-200 bg-white p-6"><h2 className="text-lg font-semibold">Run history</h2>{!history.length ? <p className="mt-4 text-sm text-zinc-500">Your first run starts here.</p> : <ul className="mt-4 space-y-2">{history.map(item=><li key={item.run_id}><button disabled={busy} onClick={()=>{if(item.run_id!==runId) {setRun(null);setEvents([]);setLastSynced(null);setProgressError('');setDestination('');setRunId(item.run_id);}setError('');}} className={`w-full rounded-xl p-3 text-left hover:bg-zinc-100 ${item.run_id===runId ? 'bg-zinc-100' : ''}`}><span className="block truncate text-sm font-medium">{item.issue_url.split('/').slice(3).join('/')}</span><span className="mt-1 block text-xs text-zinc-500">{label(item.status)} · {new Date(item.created_at*1000).toLocaleDateString()}</span></button></li>)}</ul>}</section>
          </aside>
        </div>
      </>}
      {error && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>}
    </main>
    <dialog ref={dialog} className="m-auto max-w-md rounded-3xl border border-zinc-200 bg-white p-8 shadow-xl backdrop:bg-black/30"><h2 className="text-2xl font-semibold">Disconnect GitHub?</h2><p className="my-4 text-zinc-600">This signs you out and requests cancellation of unfinished runs. Published pull requests remain on GitHub.</p><div className="mt-6 flex justify-end gap-3"><button disabled={busy} onClick={()=>dialog.current?.close()} className="rounded-xl border px-4 py-2">Keep connected</button><button disabled={busy} onClick={()=>void perform(async()=>{await action('/api/auth/disconnect');dialog.current?.close();setSession(null);router.replace('/');})} className="rounded-xl bg-black px-4 py-2 text-white">{busy ? 'Disconnecting…' : 'Disconnect'}</button></div>{error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}</dialog>
    <footer className="mx-auto max-w-6xl border-t border-zinc-200 px-6 py-6 text-sm text-zinc-500"><Link href="/" className="inline-flex items-center gap-2">Back to Torque<ArrowRight size={14}/></Link></footer>
  </div>;
}

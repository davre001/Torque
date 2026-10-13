import { NextRequest } from 'next/server';

export const maxDuration = 60;

async function proxy(request: NextRequest) {
  const upstream = process.env.TORQUE_BACKEND_ORIGIN;
  const secret = process.env.TORQUE_PROXY_SECRET;
  const origin = process.env.TORQUE_FRONTEND_ORIGIN;
  if (!upstream || !secret || !origin) {
    return Response.json({ detail: 'Backend proxy is not configured' }, { status: 503 });
  }
  const target = new URL(upstream);
  if (target.protocol !== 'https:' || target.username || target.password || target.search || target.hash || target.pathname !== '/') {
    return Response.json({ detail: 'Invalid backend proxy configuration' }, { status: 503 });
  }
  if (request.nextUrl.origin !== origin || (request.method === 'POST' && request.headers.get('origin') !== origin)) {
    return Response.json({ detail: 'Invalid request origin' }, { status: 403 });
  }
  const repositorySetup = /^\/api\/repositories\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/setup(?:\/automatic)?$/.test(request.nextUrl.pathname);
  if (!repositorySetup && !request.nextUrl.pathname.startsWith('/api/auth/') && request.nextUrl.pathname !== '/api/runs' && !request.nextUrl.pathname.startsWith('/api/runs/')) {
    return Response.json({ detail: 'Not Found' }, { status: 404 });
  }
  const headers = new Headers({ 'x-torque-proxy-secret': secret });
  for (const name of ['cookie', 'content-type', 'origin', 'x-csrf-token', 'idempotency-key']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const chunks: Uint8Array[] = [];
  let size = 0;
  if (request.body) {
    const reader = request.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 65536) {
        await reader.cancel();
        return Response.json({ detail: 'Request body too large' }, { status: 413 });
      }
      chunks.push(value);
    }
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.length; }
  target.pathname = request.nextUrl.pathname;
  target.search = request.nextUrl.search;
  try {
    const response = await fetch(target, { method: request.method, headers,
      body: request.method === 'POST' ? body : undefined, cache: 'no-store',
      redirect: 'manual', signal: AbortSignal.timeout(50000) });
    const outgoing = new Headers({ 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer' });
    for (const name of ['content-type', 'location', 'retry-after']) {
      const value = response.headers.get(name);
      if (value) outgoing.set(name, value);
    }
    for (const cookie of response.headers.getSetCookie()) outgoing.append('set-cookie', cookie);
    return new Response(response.body, { status: response.status, headers: outgoing });
  } catch {
    return Response.json({ detail: 'Backend request unavailable; check run status before retrying' }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;

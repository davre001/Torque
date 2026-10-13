/* Credential-free contract checks for the real Next.js proxy handler. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const ui = path.resolve(__dirname, '../frontend/ui');
const load = createRequire(path.join(ui, 'package.json'));
const ts = load('typescript');
const { NextRequest } = load('next/server');
const source = fs.readFileSync(path.join(ui, 'app/api/[...path]/route.ts'), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const compiled = { exports: {} };
new Function('require', 'module', 'exports', js)(load, compiled, compiled.exports);
process.env.TORQUE_BACKEND_ORIGIN = 'https://backend.example.test';
process.env.TORQUE_FRONTEND_ORIGIN = 'https://frontend.example.test';
process.env.TORQUE_PROXY_SECRET = 'fixture-proxy-secret';
let upstreamCalls = 0;
global.fetch = async (url, options) => {
  upstreamCalls++;
  assert.equal(url.origin, 'https://backend.example.test');
  assert.equal(options.redirect, 'manual');
  assert.equal(options.headers.get('x-torque-proxy-secret'), 'fixture-proxy-secret');
  assert.equal(options.headers.get('authorization'), null);
  const headers = new Headers({ location: 'https://github.com/login/oauth/authorize', 'set-cookie': '__Host-torque_oauth=fixture; Secure; HttpOnly; Path=/' });
  return new Response(null, { status: 302, headers });
};
(async () => {
  const request = new NextRequest('https://frontend.example.test/api/auth/github/connect', { headers: { authorization: 'Bearer visitor-input', cookie: 'fixture=1' } });
  const response = await compiled.exports.GET(request);
  assert.equal(response.status, 302);
  assert.match(response.headers.get('set-cookie'), /__Host-torque_oauth/);
  assert.equal(response.headers.get('x-torque-proxy-secret'), null);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  const cross = new NextRequest('https://frontend.example.test/api/runs', { method: 'POST', headers: { origin: 'https://attacker.example.test' }, body: '{}' });
  assert.equal((await compiled.exports.POST(cross)).status, 403);
  const oversized = new NextRequest('https://frontend.example.test/api/runs', { method: 'POST', headers: { origin: 'https://frontend.example.test' }, body: 'x'.repeat(65537) });
  assert.equal((await compiled.exports.POST(oversized)).status, 413);
  assert.equal(upstreamCalls, 1);
  for (const suffix of ['setup', 'setup/automatic']) {
    const setup = new NextRequest(`https://frontend.example.test/api/repositories/owner/repo/${suffix}`, {
      method: 'POST', headers: { origin: 'https://frontend.example.test', 'x-csrf-token': 'fixture-csrf' }
    });
    assert.equal((await compiled.exports.POST(setup)).status, 302);
  }
  const unknown = new NextRequest('https://frontend.example.test/api/repositories/owner/repo/setup/automatic/extra');
  assert.equal((await compiled.exports.GET(unknown)).status, 404);
  assert.equal(upstreamCalls, 3);
  console.log('Proxy cookie, redirect, origin, body-limit and secret-isolation checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });

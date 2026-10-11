// Browser contract smoke test. API responses are explicit fixtures; no live jobs/PRs.
// Run: node tests/workspace-browser.mjs (requires Edge and a running Next.js dev server).
import { spawn } from 'node:child_process';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const profile = await mkdtemp(join(tmpdir(), 'torque-browser-'));
const edge = spawn(process.env.TORQUE_TEST_BROWSER || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  ['--headless=new', '--disable-gpu', '--no-first-run', '--remote-debugging-port=0', '--remote-allow-origins=*', '--user-data-dir='+profile, 'about:blank'],
  { windowsHide: true, stdio: 'ignore' });
let socket;
try {
  let port;
  for (let i=0;i<100;i++) {
    try { port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]; break; }
    catch { await sleep(100); }
  }
  assert.ok(port, 'Browser did not start');
  const targets=await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  socket=new WebSocket(targets.find(item=>item.type==='page').webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  let next=0;
  const pending=new Map();
  const failures=[];
  const requests=[];
  let connected=true, submitted=false, published=false, failed=false, reads=0;
  const id='f'.repeat(32);
  const saved=JSON.parse(await readFile(new URL('../evidence/runs/6634790aa28943629348e02914d9b56c/run.json',import.meta.url),'utf8'));
  const fixture={...saved,run_id:id,user_id:'github:123',issue_url:'https://github.com/davre001/kokon/issues/4'};
  const send=(method,params={})=>new Promise((resolve,reject)=>{
    const requestId=++next; pending.set(requestId,{resolve,reject});socket.send(JSON.stringify({id:requestId,method,params}));
  });
  socket.onmessage=event=>{
    const message=JSON.parse(event.data);
    if (message.id) {
      const waiting=pending.get(message.id);pending.delete(message.id);
      if (message.error) waiting?.reject(new Error(message.error.message)); else waiting?.resolve(message.result);
      return;
    }
    if (message.method==='Runtime.exceptionThrown') failures.push(message.params.exceptionDetails.text);
    if (message.method==='Fetch.requestPaused') void intercept(message.params).catch(error=>{
      // React StrictMode cleanup and navigation can abort an intercepted read.
      if (error.message!=='Invalid InterceptionId.') failures.push(error.message);
    });
  };
  async function intercept({requestId,request}) {
    const url=new URL(request.url);
    requests.push(request);
    let status=200,body={};
    if (request.method==='OPTIONS') status=204;
    else if (url.pathname==='/api/auth/session') {
      if (!connected) {status=401;body={detail:'Login required'};}
      else body={user_id:'github:123',github_login:'fixture-user',csrf_token:'fixture-csrf'};
    } else if (url.pathname==='/api/auth/github/repositories') {
      body={repositories:[{full_name:'davre001/kokon',permissions:{push:true},app_permissions:{contents:'write',pull_requests:'write'}}]};
    } else if (url.pathname==='/api/runs' && request.method==='POST') {
      assert.equal(request.headers['X-CSRF-Token'] || request.headers['x-csrf-token'],'fixture-csrf');
      assert.ok(request.headers['Idempotency-Key'] || request.headers['idempotency-key']);
      assert.equal(JSON.parse(request.postData).issue_url,fixture.issue_url);
      submitted=true; body={run_id:id,status:'queued'};status=201;
    } else if (url.pathname==='/api/runs') {
      body={runs:submitted ? [{...fixture,status:failed ? 'failed' : published ? 'completed' : 'queued'}] : []};
    } else if (url.pathname.endsWith('/events')) {
      const states=failed ? ['queued','investigating','failed'] : ['queued','investigating','implementing','recovering','verifying','ready_to_publish',...(published ? ['publishing','completed'] : [])];
      body={events:url.searchParams.get('after')==='0' ? states.map((status,index)=>({id:index+1,created_at:fixture.created_at+index,status})) : []};
    } else if (url.pathname.endsWith('/publish')) {
      assert.equal(request.headers['X-CSRF-Token'] || request.headers['x-csrf-token'],'fixture-csrf');
      assert.equal(url.searchParams.get('destination'),'davre001/kokon');
      published=true; body=fixture;
    } else if (url.pathname==='/api/auth/disconnect') {
      assert.equal(request.headers['X-CSRF-Token'] || request.headers['x-csrf-token'],'fixture-csrf');
      connected=false;body={disconnected:true};
    } else if (url.pathname===`/api/runs/${id}`) {
      reads++;const state=failed ? 'failed' : published ? 'completed' : reads===1 ? 'recovering' : 'ready_to_publish';
      body={...fixture,status:state,pr_url:published ? fixture.pr_url : null};
      if (failed) body={...body,pr_url:null,error:'Fixture provider failure',result:{...fixture.result,verified:false},attempts:[]};
    } else {status=404;body={detail:'Unexpected fixture request'};}
    await send('Fetch.fulfillRequest',{requestId,responseCode:status,responseHeaders:[
      {name:'Content-Type',value:'application/json'},
      {name:'Access-Control-Allow-Origin',value:'http://localhost:3000'},
      {name:'Access-Control-Allow-Credentials',value:'true'},
      {name:'Access-Control-Allow-Methods',value:'GET,POST,OPTIONS'},
      {name:'Access-Control-Allow-Headers',value:'Content-Type,X-CSRF-Token,Idempotency-Key'}
    ],body:Buffer.from(JSON.stringify(body)).toString('base64')});
  }
  async function evaluate(expression) {
    const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
    return result.result.value;
  }
  async function wait(expression,message) {
    for(let i=0;i<120;i++) {if(await evaluate(expression))return;await sleep(100);}
    throw new Error(message);
  }
  await send('Runtime.enable');await send('Page.enable');
  await send('Fetch.enable',{patterns:[{urlPattern:'*://*/api/*'}]});
  await send('Page.navigate',{url:'http://localhost:3000/workspace'});
  await wait("document.body.innerText.includes('Hello, fixture-user')",'Session greeting absent');
  await evaluate(`(()=>{const input=document.querySelector('#issue');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(fixture.issue_url)});input.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await evaluate("document.querySelector('form').requestSubmit()");
  await wait("document.body.innerText.includes('Recovery is analyzing')",'Recovery status absent');
  await wait("document.querySelector('#destination')!==null",'Verified publication control absent');
  assert.ok(await evaluate("document.body.innerText.includes('Acceptance results') && document.body.innerText.includes('Passed')"));
  const stoppedReads=reads;await sleep(3000);assert.equal(reads,stoppedReads,'Terminal polling did not stop');
  await evaluate("(()=>{const select=document.querySelector('#destination');select.value='davre001/kokon';select.dispatchEvent(new Event('change',{bubbles:true}));})()");
  await evaluate("Array.from(document.querySelectorAll('button')).find(button=>button.textContent==='Publish draft PR').click()");
  await wait("Array.from(document.querySelectorAll('a')).some(a=>a.textContent.includes('View pull request'))",'Real PR link absent');
  assert.equal(await evaluate("Array.from(document.querySelectorAll('a')).find(a=>a.textContent.includes('View pull request')).href"),fixture.pr_url);
  failed=true;
  await send('Page.navigate',{url:'http://localhost:3000/workspace'});
  await wait("document.body.innerText.includes('Fixture provider failure')",'Persisted failure absent');
  assert.ok(await evaluate("document.body.innerText.includes('Not verified') && !Array.from(document.querySelectorAll('a')).some(a=>a.textContent.includes('View pull request'))"));
  await evaluate("Array.from(document.querySelectorAll('button')).find(button=>button.textContent==='Disconnect GitHub').click()");
  assert.ok(await evaluate("document.querySelector('dialog').open"));
  await evaluate("Array.from(document.querySelector('dialog').querySelectorAll('button')).find(button=>button.textContent==='Disconnect').click()");
  await wait("location.pathname==='/'",'Disconnect did not return to landing');
  await send('Page.navigate',{url:'http://localhost:3000/workspace'});
  await wait("Array.from(document.querySelectorAll('button')).some(button=>button.textContent==='Connect GitHub')",'Expired session login gate absent');
  assert.deepEqual(failures,[]);
  console.log('PASS: fixture session, CSRF submission, recovery/progress, acceptance results, stopped terminal polling, explicit PR result, saved failure after reload, confirmed disconnect and expired-session gate.');
  console.log('API requests were intercepted; no live jobs, provider calls or PR writes occurred.');
} finally {
  socket?.close();edge.kill();
}

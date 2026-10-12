"""Explicit, idempotent publication to a configured operator-owned repository."""
import hashlib
import json
import os
import re
from datetime import datetime,timezone
from urllib.parse import quote
import httpx
from backend.config import ROOT
from backend.execution import load_recipes,workspace_root
from backend.models import Conflict,PipelineError,Patch,parse_issue
from backend.tools.files import read_files


def verified_files(run,recipe,workspaces=None,artifacts=None,store=None):
    result=run['result']
    if not result.get('verified') or not run['attempts']:
        raise Conflict('Publication requires a verified attempt')
    attempt=run['attempts'][-1]
    if not attempt.get('tests_passed') or not attempt.get('review',{}).get('approved'):
        raise Conflict('The latest attempt did not pass verification')
    if result.get('plan',{}).get('acceptance_criteria') != recipe.acceptance_criteria:
        raise Conflict('Acceptance policy changed; run verification again')
    if set(attempt['review'].get('satisfied_criteria',[])) != set(range(len(recipe.acceptance_criteria))):
        raise Conflict('Review did not approve all criteria')
    records={}
    if len(result['artifacts']) > 64:
        raise Conflict('Verification artifact manifest exceeds its bound')
    for entry in result['artifacts']:
        name=entry['name']
        if not re.fullmatch(r'[a-z0-9-]+\.json',name):
            raise Conflict('Invalid verification artifact path')
        if store is not None and store.database.postgres:
            from backend.artifacts import read_durable
            records[name]=read_durable(store,run['run_id'],entry)
            if sum(len(json.dumps(value).encode()) for value in records.values()) > 8*1024*1024:
                raise Conflict('Verification artifacts exceed the publication read limit')
            continue
        path=(artifacts or ROOT/'var'/'artifacts')/run['run_id']/name
        if path.is_symlink():
            raise Conflict('Verification artifacts cannot be symlinks')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise Conflict('Verification artifact changed')
        records[name]=json.loads(data)
    number=attempt['number']
    tests=records.get(f'tests-{number}.json',{})
    if tests.get('exit_code') != 0 or tests.get('failure_kind') is not None or tests.get('timed_out') or tests.get('assertions_passed') != len(recipe.acceptance_criteria):
        raise Conflict('Saved acceptance results did not pass')
    patch=Patch.model_validate(records[f'patch-{number}.json'])
    if store is not None and store.database.postgres:
        context=records.get('verified-context.json')
        if not isinstance(context,dict) or set(context) != set(recipe.context_files):
            raise Conflict('Durable verified context unavailable')
    else:
        context=read_files((workspaces or workspace_root())/run['run_id'],recipe.context_files)
    digest=hashlib.sha256()
    for name,item in sorted(context.items()):
        digest.update(name.encode()+b'\0'+item['content'].encode())
    if digest.hexdigest() != result.get('verified_content_sha256'):
        raise Conflict('Workspace changed after verification; run verification again')
    names=[edit.path for edit in patch.edits]
    if len(set(names)) != len(names) or any(name not in recipe.editable_files or name not in context for name in names):
        raise Conflict('Patch exceeds reviewed file permissions')
    digest=hashlib.sha256()
    legacy_windows_digest=hashlib.sha256()
    files={}
    for name in names:
        files[name]=context[name]['content']
        digest.update(name.encode()+b'\0'+files[name].encode())
        # Older Windows workers hashed native path separators. Content and artifact
        # verification above remains mandatory for these existing demo records.
        legacy_windows_digest.update(name.replace('/','\\').encode()+b'\0'+files[name].encode())
    if result.get('patch_sha256') not in {digest.hexdigest(),legacy_windows_digest.hexdigest()} or attempt.get('patch_sha256') != result.get('patch_sha256'):
        raise Conflict('Patch does not match the verified attempt')
    return files


class Publisher:
    def __init__(self,token,destination,client=None):
        if not token:
            raise Conflict('Set GITHUB_TOKEN with Contents and Pull requests read/write on the destination')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}',destination) or destination.split('/')[1] in {'.','..'}:
            raise Conflict('Set TORQUE_PUBLISH_REPOSITORY to an operator-owned source repository or fork')
        self.destination=destination.lower()
        self.client=client or httpx.Client(base_url='https://api.github.com',timeout=20,follow_redirects=False,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10'})

    def request(self,method,path,optional=False,**kwargs):
        try:
            response=self.client.request(method,path,**kwargs)
            if optional and response.status_code == 404:
                return None
            if response.status_code >= 300:
                raise PipelineError(f'GitHub publication request failed (HTTP {response.status_code}); check repository access and permissions')
            return response.json()
        except httpx.HTTPError:
            raise PipelineError('GitHub publication connection failed; retry the same publish request to reconcile remote state') from None

    def tree_entries(self,repository,sha):
        tree=self.request('GET',f'/repos/{repository}/git/trees/{sha}',params={'recursive':'1'})
        if tree.get('truncated'):
            raise Conflict('Repository tree is truncated; publication is unsupported')
        return {item['path']:(item['mode'],item['type'],item['sha']) for item in tree['tree'] if item['type']!='tree'}

    def validate_destination(self,run):
        """Read-only validation before durable publication ownership is claimed."""
        source_owner,source_repo,_=parse_issue(run['issue_url'])
        source=f'{source_owner}/{source_repo}'.lower()
        sha=run['result']['source_sha']
        if not re.fullmatch('[a-f0-9]{40}',sha) or run['result']['source_repository'].lower()!=source:
            raise Conflict('Source identity is invalid')
        user=self.request('GET','/user')['login'].lower()
        destination=self.request('GET',f'/repos/{self.destination}')
        upstream=self.request('GET',f'/repos/{source}')
        if destination['full_name'].lower()!=self.destination or destination['owner']['login'].lower()!=user or not destination.get('permissions',{}).get('push'):
            raise Conflict('Destination must be owned by the authenticated operator with write access')
        if destination['id']!=upstream['id'] and destination.get('source',{}).get('id')!=upstream['id'] and destination.get('parent',{}).get('id')!=upstream['id']:
            raise Conflict('Destination is not the verified source repository or its fork')
        return sha,user,destination

    def publish(self,run,files):
        # Recheck after claiming ownership; preflight is not a write authorization.
        sha,user,destination=self.validate_destination(run)
        base=destination['default_branch']
        prefix=f'/repos/{self.destination}'
        branch='torque/'+run['run_id']
        marker=f'<!-- torque-run:{run["run_id"]} -->'
        existing=self.request('GET',prefix+'/pulls',params={'state':'all','head':user+':'+branch,'base':base,'per_page':100})
        base_head=self.request('GET',prefix+'/commits/'+quote(base,safe=''))['sha']
        if base_head!=sha:
            raise Conflict('Destination base changed since verification; verify its new revision before publishing')
        base_commit=self.request('GET',prefix+'/git/commits/'+sha)
        base_tree=base_commit['tree']['sha']
        expected=self.tree_entries(self.destination,base_tree)
        entries=[]
        for name,content in files.items():
            if name not in expected or expected[name][:2]!=('100644','blob'):
                raise Conflict('Publication supports only existing regular non-executable files')
            raw=content.encode()
            blob_sha=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
            expected[name]=('100644','blob',blob_sha)
            entries.append({'path':name,'mode':'100644','type':'blob','content':content})
        tree=self.request('POST',prefix+'/git/trees',json={'base_tree':base_tree,'tree':entries})['sha']
        if self.tree_entries(self.destination,tree)!=expected:
            raise Conflict('GitHub tree differs from the verified files')
        date=datetime.fromtimestamp(run['created_at'],timezone.utc).isoformat()
        identity={'name':'Torque','email':'torque@users.noreply.github.com','date':date}
        commit=self.request('POST',prefix+'/git/commits',json={'message':f'Torque verified fix for {run["run_id"]}',
            'tree':tree,'parents':[sha],'author':identity,'committer':identity})
        head=commit['sha']
        if commit['tree']['sha']!=tree or [parent['sha'] for parent in commit['parents']]!=[sha]:
            raise Conflict('Published commit does not match the verified tree and source parent')
        ref=self.request('GET',prefix+'/git/ref/heads/'+quote(branch,safe='/'),optional=True)
        if ref is None:
            self.request('POST',prefix+'/git/refs',json={'ref':'refs/heads/'+branch,'sha':head})
        elif ref['object']['sha']!=head:
            raise Conflict('Publication branch already exists with different content; it will not be overwritten')
        if len(existing)>1:
            raise Conflict('Multiple PRs exist for this run; manual reconciliation required')
        if existing:
            pr=existing[0]
        else:
            if self.request('GET',prefix+'/commits/'+quote(base,safe=''))['sha']!=sha:
                raise Conflict('Destination base changed during publication; verify its new revision')
            body=(f'Tested fix for {run["issue_url"]}.\n\nControlled demo PR; no upstream PR was created.\n\n'
                  f'Run: `{run["run_id"]}`. Source: `{sha}`.\n'
                  f'Verified head: `{head}`. Attempt: {run["attempts"][-1]["number"]}.\n'
                  f'Change: {run["result"].get("summary", run["result"]["plan"].get("summary", "Verified patch"))}\n'
                  f'All {len(run["result"]["plan"]["acceptance_criteria"])} independent browser assertions passed; agent review approved.\n'
                  f'Trace ID: `{run["result"].get("trace_id", "unavailable")}` (dashboard readback unconfirmed).\n\n{marker}')
            pr=self.request('POST',prefix+'/pulls',json={'title':'Torque: verified fix for issue '+str(parse_issue(run['issue_url'])[2]),
                'head':branch,'base':base,'body':body,'draft':True})
        if pr['head']['sha']!=head or pr['base']['sha']!=sha or marker not in (pr.get('body') or '') or pr['base']['repo']['full_name'].lower()!=self.destination:
            raise Conflict('PR identity does not match this verified publication')
        if pr['state']!='open' and not pr.get('merged_at'):
            raise Conflict('Publication PR was closed without merging; it will not be reopened automatically')
        url=pr['html_url']
        if not re.fullmatch(r'https://github\.com/'+re.escape(self.destination)+r'/pull/[1-9][0-9]*',url,re.I):
            raise Conflict('Unexpected PR URL')
        return url,head

    def close(self):
        self.client.close()


def publish_run(store,run_id,user_id='operator',destination=None):
    run=store.get(run_id,user_id)
    if run is None:
        raise Conflict('Run not found')
    if run['status']=='completed' and run.get('pr_url'):
        return run
    if run['status'] not in {'ready_to_publish','publishing'}:
        raise Conflict('Only a verified ready-to-publish run can be published')
    if user_id == 'operator':
        destination=destination or os.getenv('TORQUE_PUBLISH_REPOSITORY','')
        token=os.getenv('GITHUB_TOKEN','')
    else:
        from backend.github_auth import GitHubAuth
        auth=GitHubAuth(store)
        source_owner,source_repo,_=parse_issue(run['issue_url'])
        auth.authorize(user_id,f'{source_owner}/{source_repo}')
        destination=destination or f'{source_owner}/{source_repo}'
        token=auth.authorize(user_id,destination,write=True)
    publisher=Publisher(token,destination)
    owner=None
    try:
        source_owner,source_repo,_=parse_issue(run['issue_url'])
        source=f'{source_owner}/{source_repo}'.lower()
        allowed=[item.strip().lower() for item in os.getenv('TORQUE_ALLOWED_REPOSITORIES','').split(',')]
        recipe=load_recipes().get(source)
        if source not in allowed or recipe is None:
            raise Conflict('Source repository is not currently authorized')
        files=verified_files(run,recipe,store=store)
        publisher.validate_destination(run)
        store.release_rejected_publication(run_id,user_id)
        owner=store.claim_publication(run_id,user_id,publisher.destination)
        url,head=publisher.publish(run,files)
        store.finish_publication(run_id,owner,pr_url=url,commit_sha=head)
        return store.get(run_id,user_id)
    except (Conflict,PipelineError) as exc:
        if owner:
            store.finish_publication(run_id,owner,error=str(exc))
        raise
    except Exception:
        message='Publication failed; retry the same request to reconcile GitHub state'
        if owner:
            store.finish_publication(run_id,owner,error=message)
        raise PipelineError(message) from None
    finally:
        publisher.close()

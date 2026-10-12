"""Opt-in read-only Entire search; never import Torque history as target context."""
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from backend.config import ROOT

class EntireContext:
    def search(self, repository, revision, query, context=None):
        record = {'repository':repository,'source_sha':revision,'source':'entire-search',
                  'status':'disabled','results':[]}
        if os.getenv('TORQUE_ENTIRE_CONTEXT','0') != '1':
            return record
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not re.fullmatch(r'[a-f0-9]{40}',revision):
            return {**record,'status':'invalid-target'}
        executable=shutil.which('entire')
        if not executable:
            return {**record,'status':'unavailable','reason':'CLI not installed'}
        # Home is retained for CLI-owned authentication; app credentials are excluded.
        environment={k:v for k,v in os.environ.items() if k.upper() in
                     {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','HOME','USERPROFILE','APPDATA','LOCALAPPDATA'}}
        command=[executable,'search',query[:300],'--repo','gh/'+repository,'--compact','--limit','3']
        record['command']=['entire',*command[1:]]
        try:
            with tempfile.TemporaryFile() as output:
                process=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=output,stderr=subprocess.DEVNULL)
                try:
                    code=process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait()
                    return {**record,'status':'unavailable','reason':'Search timed out'}
                if code or output.tell()>100000:
                    return {**record,'status':'unavailable','reason':'Search unavailable; verify target mirror and CLI login'}
                output.seek(0);data=json.load(output)
            hits=[]
            for hit in data.get('results',[]):
                if hit.get('repo','').lower().removeprefix('gh/') != repository.lower():
                    continue
                hits.append({k:hit[k] for k in ('id','type','repo','title','snippet','date') if k in hit})
            if not hits and context:
                term=Path(next(iter(context))).stem
                code_command=[executable,'search',term,'--repo','gh/'+repository,'--code','--json','--limit','3']
                record['code_command']=['entire',*code_command[1:]]
                with tempfile.TemporaryFile() as output:
                    process=subprocess.Popen(code_command,cwd=ROOT,env=environment,stdout=output,stderr=subprocess.DEVNULL)
                    try:
                        code=process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait()
                        return {**record,'status':'unavailable','reason':'Code search timed out'}
                    if code or output.tell()>100000:
                        return {**record,'status':'unavailable','reason':'Code search unavailable'}
                    output.seek(0);data=json.load(output)
                for hit in data.get('results',[]):
                    name=hit.get('path');line=hit.get('line');snippet=hit.get('context_line')
                    if hit.get('repo','').lower().removeprefix('gh/') != repository.lower() or name not in context:
                        continue
                    lines=context[name]['content'].splitlines()
                    if type(line) is not int or not 1 <= line <= len(lines) or snippet != lines[line-1]:
                        continue
                    hits.append({'repo':repository,'path':name,'line':line,'context_line':snippet,
                                 'file_sha256':context[name]['sha256'],'pinned_line_verified':True})
                record['source']='entire-code-search'
            return {**record,'status':'available' if hits else 'empty','results':hits[:3],
                    'scope':'Historical context; not proof these records belong to source_sha'}
        except (OSError,ValueError,TypeError,AttributeError):
            return {**record,'status':'unavailable','reason':'Invalid or unavailable search response'}

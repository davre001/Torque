import json
from backend.integrations.entire import EntireContext

def test_code_context_rejects_wrong_repo_and_stale_lines(monkeypatch):
    monkeypatch.setenv('TORQUE_ENTIRE_CONTEXT','1')
    monkeypatch.setenv('GITHUB_TOKEN','must-not-reach-child')
    monkeypatch.setattr('backend.integrations.entire.shutil.which',lambda _: 'entire')
    class Process:
        def __init__(self,command,**kwargs):
            assert 'GITHUB_TOKEN' not in kwargs['env']
            data={'results':[]} if '--code' not in command else {'results':[
                {'repo':'gh/a/b','path':'Gallery.tsx','line':1,'context_line':'actual'},
                {'repo':'gh/a/b','path':'Gallery.tsx','line':1,'context_line':'stale'},
                {'repo':'gh/other/repo','path':'Gallery.tsx','line':1,'context_line':'actual'}]}
            kwargs['stdout'].write(json.dumps(data).encode())
        def wait(self,timeout): return 0
    monkeypatch.setattr('backend.integrations.entire.subprocess.Popen',Process)
    result=EntireContext().search('a/b','a'*40,'gallery',{'Gallery.tsx':{'content':'actual','sha256':'hash'}})
    assert result['status']=='available'
    assert len(result['results'])==1
    assert result['results'][0]['pinned_line_verified']

def test_disabled_context_never_runs_cli(monkeypatch):
    monkeypatch.delenv('TORQUE_ENTIRE_CONTEXT',raising=False)
    monkeypatch.setattr('backend.integrations.entire.shutil.which',lambda _: (_ for _ in ()).throw(AssertionError()))
    assert EntireContext().search('a/b','a'*40,'query')['status']=='disabled'

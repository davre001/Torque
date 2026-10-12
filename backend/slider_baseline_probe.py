"""Run and save the reviewed slider baseline on the existing Actions runner."""
import hashlib
import json
from backend.acceptance_profiles import SLIDER_SHA
from backend.config import ROOT,Settings
from backend.execution import load_recipes
from backend.tools.actions_runner import ActionsRunner


def main():
    Settings.load()
    workspace=ROOT/'var/slider-check/source'
    calibration=json.loads((ROOT/'evidence/slider/acceptance-validation.json').read_text())
    for item in calibration['files']:
        if hashlib.sha256((workspace/item['path']).read_bytes()).hexdigest()!=item['source_sha256']:
            raise RuntimeError('Cached baseline source differs from the reviewed original')
    runner=ActionsRunner(load_recipes(ROOT/'backend/recipes.slider.json')['davre001/kokon'])
    original=runner._request
    request_id=None
    observed=None
    last_status=None
    def request(method,path,**kwargs):
        nonlocal request_id,observed,last_status
        response=original(method,path,**kwargs)
        if method=='POST' and path.endswith('/dispatches'):
            request_id=kwargs['json']['inputs']['request_id']
            print('Dispatched slider baseline '+request_id,flush=True)
        if method=='GET' and '/actions/' in path and ('/runs' in path):
            data=response.json()
            candidates=data.get('workflow_runs',[data])
            for run in candidates:
                if request_id and run.get('display_title')=='Torque test '+request_id:
                    observed=run
                    status=run['status']
                    if status!=last_status:
                        print('Actions '+str(run['id'])+': '+status,flush=True)
                        last_status=status
        return response
    runner._request=request
    try:
        runner.bind_source('davre001','kokon',SLIDER_SHA)
        result=runner.run(workspace,lambda:None)
        assert observed is not None
        expected=['slider-semantics','slider-keys','sweep-and-focus','image-descriptions']
        reproduced=result.failure_kind=='assertion' and result.assertions_passed==1 and all(name in result.output for name in expected)
        report={'mode':'live-hosted-slider-baseline','request_id':request_id,
                'source_repository':'davre001/kokon','source_sha':SLIDER_SHA,
                'actions_run_id':observed['id'],'actions_url':observed['html_url'],
                'workflow_sha':runner.workflow_sha,'workflow_conclusion':observed.get('conclusion'),
                'suite_sha256':runner.suite_sha256,'image_digest':runner.test_image,
                'baseline_reproduced':reproduced,'provider_calls':0,'pr_writes':0,
                'production_database_modified':False,'result':result.model_dump()}
        folder=ROOT/'evidence/slider';folder.mkdir(parents=True,exist_ok=True)
        (folder/('hosted-baseline-'+request_id+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
        if not reproduced:raise SystemExit('Hosted baseline did not reproduce the expected assertion failures')
    finally:runner.close()


if __name__=='__main__':main()

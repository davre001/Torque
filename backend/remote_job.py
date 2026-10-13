"""GitHub workflow entry point. Only public demo source enters the test container."""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zlib
from backend.config import ROOT
from backend.execution import Recipe
from backend.models import TestResult
from backend.tools.repository import snapshot
from backend.tools.files import safe_path
from backend.tools.sandbox import DockerRunner
from backend.acceptance_profiles import GALLERY_FILES, GALLERY_CRITERIA, SLIDER_FILES, SLIDER_CRITERIA, validate_source

def decode_gallery_bundle(encoded, expected_files=GALLERY_FILES):
    if len(encoded)>60000:raise ValueError('Oversized gallery input')
    compressed=base64.b64decode(encoded,validate=True)
    decoder=zlib.decompressobj()
    raw=decoder.decompress(compressed,250001)
    if len(raw)>250000 or not decoder.eof or decoder.unused_data:raise ValueError('Invalid or oversized compressed input')
    files=json.loads(raw)
    if not isinstance(files,dict) or set(files)!=set(expected_files) or any(not isinstance(content,str) for content in files.values()):
        raise ValueError('Unreviewed gallery file scope')
    return files

def main():
    request_id = os.environ["TORQUE_REQUEST_ID"]
    sha = os.environ["TORQUE_SOURCE_SHA"]
    if not re.fullmatch("[a-f0-9]{32}",request_id) or not re.fullmatch("[a-f0-9]{40}",sha):
        raise ValueError("Invalid request identity")
    record = {"request_id":request_id,"source_sha":sha,"suite_sha256":None}
    try:
        profile=os.getenv('TORQUE_ACCEPTANCE_PROFILE','reduced-motion') or 'reduced-motion'
        repository=os.getenv('TORQUE_SOURCE_REPOSITORY','gabrielelozupone/kokon').lower() or 'gabrielelozupone/kokon'
        if profile == 'repository-tests':
            record.update(acceptance_profile=profile, source_repository=repository)
            from backend.repository_test_job import execute
            record.update(execute(repository, sha, os.environ['TORQUE_REPOSITORY_SETUP'], os.environ['TORQUE_FILES_BUNDLE']))
            Path('remote-result').mkdir(exist_ok=True)
            Path('remote-result/result.json').write_text(json.dumps(record), encoding='utf-8')
            return
        if not validate_source(profile,repository,sha):raise ValueError('Source/profile not reviewed')
        record.update(acceptance_profile=profile,source_repository=repository)
        if profile=='slider-keyboard':
            replacements=decode_gallery_bundle(os.environ['TORQUE_FILES_BUNDLE'],SLIDER_FILES)
            suite=ROOT/'tests/acceptance/slider'
            command=['python','/acceptance/test_slider.py']
            criteria=SLIDER_CRITERIA
        elif profile=='gallery-keyboard':
            replacements=decode_gallery_bundle(os.environ['TORQUE_FILES_BUNDLE'])
            suite=ROOT/'tests/acceptance/gallery'
            command=['python','/acceptance/test_gallery.py']
            criteria=GALLERY_CRITERIA
        else:
            encoded = os.environ["TORQUE_INDEX_HTML"]
            if len(encoded) > 60000:raise ValueError("Oversized input")
            replacements={'site/index.html':base64.b64decode(encoded,validate=True).decode('utf-8')}
            suite=ROOT/'tests/acceptance/kokon'
            command=['python','/acceptance/test_reduced_motion.py']
            criteria=['reduced motion paused','manual play','normal autoplay']
        # No inputs are interpolated into shell commands.
        subprocess.run(["docker","build","-t","torque-kokon-tests",
                        str(suite)],check=True,timeout=300)
        image = subprocess.check_output(["docker","image","inspect","torque-kokon-tests",
                                         "--format","{{.Id}}"],text=True).strip()
        record["image_digest"] = image
        recipe = Recipe(image=image,command=command,
                        context_files=list(replacements),editable_files=list(replacements),
                        acceptance_criteria=criteria,suite_directory=str(suite),timeout_seconds=120)
        runner = DockerRunner(recipe)
        runner.preflight()
        record["suite_sha256"] = runner.suite_sha256
        with tempfile.TemporaryDirectory(prefix="torque-source-") as temporary:
            workspace = Path(temporary)/"source"
            owner,repo=repository.split('/')
            snapshot(owner,repo,sha,workspace,lambda:None)
            for name,content in replacements.items():safe_path(workspace,name).write_bytes(content.encode())
            result = runner.run(workspace,lambda:None)
        print(result.output,flush=True)
        record["result"] = result.model_dump()
    except Exception:
        # Do not export exception text or workflow environment.
        record["result"] = TestResult(exit_code=125,output="Remote runner infrastructure failed",
            failure_kind="infrastructure",command=["remote-kokon-acceptance"]).model_dump()
    Path("remote-result").mkdir(exist_ok=True)
    Path("remote-result/result.json").write_text(json.dumps(record),encoding="utf-8")

if __name__ == "__main__":
    main()

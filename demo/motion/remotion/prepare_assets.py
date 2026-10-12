"""Prepare only explicit demo assets; never reads environment credentials."""
from pathlib import Path
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FFMPEG = Path('C:/Users/USER/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe')
FFPROBE = FFMPEG.with_name('ffprobe.exe')
PUBLIC = HERE/'public'
PUBLIC.mkdir(exist_ok=True)
sources = {'issue':'ORIGINal github issue.webm', 'publication-probe':'Published PR.webm',
           'incident':'resolution.webm', 'run':'run-json.webm', 'verified':'verified-json.webm', 'pr':'screen-capture (16).webm'}
manifest = {}
for name, source in sources.items():
    target = PUBLIC/(name+'.mp4')
    subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1', '-filter_threads', '1', '-i', str(ROOT/'frontend/static'/source),
                    '-an', '-c:v', 'copy', '-movflags', '+faststart', str(target)], check=True)
    data = json.loads(subprocess.check_output([str(FFPROBE), '-v','error','-show_entries','format=duration:stream=width,height','-of','json',str(target)]))
    manifest[name] = {'duration':float(data['format']['duration']), **data['streams'][0]}
for original, name in [('torque-plan-summary.png','cfo-summary.png'), ('torque-assumptions.png','cfo-assumptions.png'), ('unit-economics-and-sensitivity.png','cfo-economics.png')]:
    shutil.copyfile(ROOT/'cfo.ai/screenshots'/original, PUBLIC/name)
shutil.copyfile(ROOT/'frontend/static/test 1-json.png', PUBLIC/'tests.png')
for original, name in [('run.json','run.json'),('verified.json','verified.json'),('tests-1.json','tests.json')]:
    shutil.copyfile(ROOT/'evidence/runs/6634790aa28943629348e02914d9b56c'/original, PUBLIC/name)
from datetime import date
(PUBLIC/'assets.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))

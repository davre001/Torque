"""Trusted suite wrapper: emit diagnostics from pytest's real exit and report."""
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

config = json.loads(Path('/acceptance/config.json').read_text())
shutil.copytree('/workspace', '/tmp/project')
os.chdir('/tmp/project')
tests = [p for p in config['test_files'] if p.endswith('.py') and Path(p).name != 'conftest.py']
started = time.monotonic()
with tempfile.TemporaryFile() as output:
    result = subprocess.run([sys.executable, '-m', 'pytest', '-vv', '-p', 'no:cacheprovider',
                             '--junitxml=/tmp/results.xml', *tests], stdout=output, stderr=subprocess.STDOUT)
    output.seek(0)
    text = output.read(20000).decode('utf-8', errors='replace')
report = Path('/tmp/results.xml')
try:
    if report.stat().st_size > 100000: raise ValueError()
    xml = ET.fromstring(report.read_bytes())
    cases = list(xml.iter('testcase'))
    executed = [case for case in cases if case.find('skipped') is None]
    valid = bool(executed)
except (OSError, ValueError, ET.ParseError):
    valid = False
passed = result.returncode == 0 and valid
print(text.replace('TORQUE_TEST_RESULT=', 'TEST_LOG='), flush=True)
print('TORQUE_TEST_RESULT=' + json.dumps({'assertions_passed': int(passed),
      'failure_kind': None if passed else 'assertion' if valid else 'infrastructure',
      'cases': [{'name': 'Frozen repository test suite', 'passed': passed,
                 'duration_ms': (time.monotonic()-started)*1000,
                 'stdout': text[-4000:], 'stderr': '' if passed else text[-4000:],
                 'stacktrace': '' if passed else text[-6000:]}]}), flush=True)
sys.exit(0 if passed else result.returncode or 125)

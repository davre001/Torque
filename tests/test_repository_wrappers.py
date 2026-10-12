"""Exercise managed reporters against real local test processes, without Docker."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def result(process):
    lines = [line for line in process.stdout.splitlines() if line.startswith('TORQUE_TEST_RESULT=')]
    assert len(lines) == 1
    return json.loads(lines[0].split('=', 1)[1])


@pytest.mark.parametrize('mode', ['pass', 'fail', 'empty'])
def test_pytest_wrapper_requires_real_executed_tests(tmp_path, mode):
    workspace, acceptance, output = tmp_path/'workspace', tmp_path/'acceptance', tmp_path/'tmp'
    workspace.mkdir(); acceptance.mkdir(); output.mkdir()
    body = '' if mode == 'empty' else 'def test_actual():\n    print("TORQUE_TEST_RESULT={fake}")\n    assert ' + ('True' if mode == 'pass' else 'False') + '\n'
    (workspace/'test_actual.py').write_text(body)
    (acceptance/'config.json').write_text(json.dumps({'test_files': ['test_actual.py']}))
    script = (ROOT/'tests/acceptance/repository/run.py').read_text()
    script = script.replace('/workspace', workspace.as_posix()).replace('/acceptance', acceptance.as_posix()).replace('/tmp', output.as_posix())
    wrapper = tmp_path/'run.py'; wrapper.write_text(script)
    process = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True, timeout=30)
    report = result(process)
    assert report['assertions_passed'] == int(mode == 'pass')
    assert report['failure_kind'] == (None if mode == 'pass' else 'assertion' if mode == 'fail' else 'infrastructure')
    assert report['cases'][0]['passed'] == (mode == 'pass')
    if mode == 'fail': assert 'AssertionError' in report['cases'][0]['stacktrace']


@pytest.mark.parametrize('mode', ['pass', 'fail', 'empty'])
def test_node_wrapper_requires_real_executed_tests(tmp_path, mode):
    node = shutil.which('node')
    if not node: pytest.skip('Node.js is not installed')
    workspace, acceptance, output = tmp_path/'workspace', tmp_path/'acceptance', tmp_path/'tmp'
    workspace.mkdir(); acceptance.mkdir(); output.mkdir(); (workspace/'node_modules').mkdir()
    body = '' if mode == 'empty' else "const test=require('node:test');const assert=require('node:assert/strict');test('actual check',()=>assert.equal(1," + ('1' if mode == 'pass' else '2') + '));'
    (workspace/'actual.test.cjs').write_text(body)
    (acceptance/'config.json').write_text(json.dumps({'engine': 'node', 'test_files': ['actual.test.cjs']}))
    script = (ROOT/'tests/acceptance/repository/run.cjs').read_text()
    script = script.replace('/workspace', workspace.as_posix()).replace('/acceptance', acceptance.as_posix()).replace('/tmp', output.as_posix())
    wrapper = tmp_path/'run.cjs'; wrapper.write_text(script)
    process = subprocess.run([node, str(wrapper)], capture_output=True, text=True, timeout=30)
    report = result(process)
    assert report['assertions_passed'] == int(mode == 'pass')
    assert report['failure_kind'] == (None if mode == 'pass' else 'assertion' if mode == 'fail' else 'infrastructure')
    if mode == 'fail': assert 'AssertionError' in report['cases'][0]['stacktrace']

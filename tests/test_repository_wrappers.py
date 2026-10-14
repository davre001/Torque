"""Exercise managed reporters against real local test processes, without Docker."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_wrapper_imports_monorepo_app_and_installed_dependencies(tmp_path):
    workspace, acceptance, output = tmp_path/'workspace', tmp_path/'acceptance', tmp_path/'tmp'
    (workspace/'backend/tests').mkdir(parents=True)
    (workspace/'backend/app').mkdir()
    (workspace/'torque-python-deps').mkdir()
    acceptance.mkdir(); output.mkdir()
    (workspace/'backend/app/__init__.py').write_text('VALUE = 42')
    (workspace/'torque-python-deps/public_dependency.py').write_text('VALUE = 42')
    (workspace/'backend/tests/test_imports.py').write_text('import os\nimport app\nimport public_dependency\ndef test_imports():\n    assert app.VALUE == public_dependency.VALUE\n    assert os.environ["PYTHON_DOTENV_DISABLED"] == "1"\n')
    (acceptance/'config.json').write_text(json.dumps({'test_files':['backend/tests/test_imports.py']}))
    script = (ROOT/'tests/acceptance/repository/run.py').read_text()
    script = script.replace('/tmp', output.as_posix()).replace('/workspace', workspace.as_posix()).replace('/acceptance', acceptance.as_posix())
    wrapper = tmp_path/'run.py'; wrapper.write_text(script)
    process = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True, timeout=30)
    assert result(process)['assertions_passed'] == 1


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
    # Replace /tmp first: Linux fixture paths themselves start with /tmp.
    # Replacing it last corrupts the workspace/acceptance paths just inserted.
    script = script.replace('/tmp', output.as_posix()).replace('/workspace', workspace.as_posix()).replace('/acceptance', acceptance.as_posix())
    wrapper = tmp_path/'run.py'; wrapper.write_text(script)
    process = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True, timeout=30)
    report = result(process)
    assert report['assertions_passed'] == int(mode == 'pass')
    assert report['failure_kind'] == (None if mode == 'pass' else 'assertion' if mode == 'fail' else 'infrastructure')
    assert report['cases'][0]['passed'] == (mode == 'pass')
    if mode == 'fail': assert 'AssertionError' in report['cases'][0]['stacktrace']


@pytest.mark.parametrize('mode', ['pass', 'fail', 'empty'])
@pytest.mark.parametrize('package_root', ['', 'frontend'])
def test_node_wrapper_requires_real_executed_tests(tmp_path, mode, package_root):
    node = shutil.which('node')
    if not node: pytest.skip('Node.js is not installed')
    workspace, acceptance, output = tmp_path/'workspace', tmp_path/'acceptance', tmp_path/'tmp'
    workspace.mkdir(); acceptance.mkdir(); output.mkdir(); (workspace/'node_modules').mkdir()
    body = '' if mode == 'empty' else "const test=require('node:test');const assert=require('node:assert/strict');test('actual check',()=>assert.equal(1," + ('1' if mode == 'pass' else '2') + '));'
    package = workspace/package_root
    package.mkdir(exist_ok=True)
    (package/'actual.test.cjs').write_text(body)
    (acceptance/'config.json').write_text(json.dumps({'engine': 'node', 'package_root':package_root, 'test_files': [(package_root+'/' if package_root else '')+'actual.test.cjs']}))
    script = (ROOT/'tests/acceptance/repository/run.cjs').read_text()
    script = script.replace('/tmp', output.as_posix()).replace('/workspace', workspace.as_posix()).replace('/acceptance', acceptance.as_posix())
    wrapper = tmp_path/'run.cjs'; wrapper.write_text(script)
    process = subprocess.run([node, str(wrapper)], capture_output=True, text=True, timeout=30)
    report = result(process)
    assert report['assertions_passed'] == int(mode == 'pass')
    assert report['failure_kind'] == (None if mode == 'pass' else 'assertion' if mode == 'fail' else 'infrastructure')
    if mode == 'fail': assert 'AssertionError' in report['cases'][0]['stacktrace']

"""Credential-free container preparation for public repository test suites."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from backend.config import ROOT
from backend.execution import Recipe
from backend.repository_configuration import SetupConfig
from backend.tools.repository import snapshot
from backend.tools.files import safe_path
from backend.tools.sandbox import DockerRunner


def prepare_dependencies(workspace, image, package_root='', manager='npm'):
    name = 'torque-install-' + uuid.uuid4().hex
    cache = workspace.parent/'node-install-cache'
    cache.mkdir()
    uid, gid = getattr(os, 'getuid', lambda: 65534)(), getattr(os, 'getgid', lambda: 65534)()
    installer_user = f'{uid}:{gid}' if uid else '65534:65534'
    args = ['docker', 'run', '--rm', '--init', '--name', name, '--read-only',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', installer_user,
            '--cpus=1', '--memory=2g', '--memory-swap=2g', '--pids-limit=128',
            '--tmpfs', '/tmp:rw,exec,nosuid,nodev,size=128m',
            '--mount', f'type=bind,src={cache},dst=/cache',
            '--mount', f'type=bind,src={workspace},dst=/workspace', '--workdir', '/workspace' + ('/'+package_root if manager == 'npm' and package_root else ''),
            image]
    if manager == 'pnpm':
        root_package = json.loads((workspace/'package.json').read_text())
        pinned = root_package.get('packageManager', '')
        if not re.fullmatch(r'pnpm@\d+\.\d+\.\d+', pinned):
            raise ValueError('pnpm requires a pinned packageManager version')
        args += ['npx', '--yes', '--ignore-scripts', '--registry=https://registry.npmjs.org', '--cache=/cache/npm-cache', pinned,
                 '--filter', './'+(package_root or '.'), 'install', '--frozen-lockfile', '--ignore-scripts', '--store-dir=/cache/pnpm-store', '--network-concurrency=4']
    else:
        args += ['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund', '--cache', '/cache/npm-cache']
    # Public registry access is needed only in this credential-free install container.
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 180
        try:
            while process.poll() is None:
                if time.monotonic() > deadline or os.fstat(log.fileno()).st_size > 100000:
                    raise ValueError('Dependency installation exceeded limits')
                time.sleep(.1)
            if process.returncode:
                raise ValueError('Dependency installation failed')
        finally:
            if process.poll() is None:
                subprocess.run(['docker', 'rm', '-f', name], timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.kill()
                process.wait(timeout=10)


def prepare_python_dependencies(workspace, image, test_files):
    from backend.python_dependencies import requirements
    packages = []
    for file in test_files:
        if Path(file).name == 'requirements.txt':
            packages.extend(requirements(safe_path(workspace, file).read_text(encoding='utf-8')))
    if not packages:
        return
    target = workspace/'torque-python-deps'
    target.mkdir()
    target.chmod(0o777)
    name = 'torque-python-install-' + uuid.uuid4().hex
    uid = getattr(os, 'getuid', lambda: 65534)()
    gid = getattr(os, 'getgid', lambda: 65534)()
    # The coordinator must retain ownership to normalize permissions and clean
    # up installed wheels. The installer still runs as an unprivileged user.
    installer_user = f'{uid}:{gid}' if uid else '65534:65534'
    args = ['docker', 'run', '--rm', '--init', '--name', name, '--read-only',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', installer_user,
            '--cpus=1', '--memory=1g', '--memory-swap=1g', '--pids-limit=128',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=512m',
            '--mount', f'type=bind,src={target},dst=/dependencies', image,
            'python', '-m', 'pip', '--isolated', 'install', '--only-binary=:all:',
            '--no-cache-dir', '--disable-pip-version-check', '--index-url', 'https://pypi.org/simple',
            '--target', '/dependencies', *list(dict.fromkeys(packages))]
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 180
        try:
            while process.poll() is None:
                if time.monotonic() > deadline or os.fstat(log.fileno()).st_size > 100000:
                    raise ValueError('Python dependency installation exceeded limits')
                time.sleep(.1)
            if process.returncode:
                raise ValueError('Python wheel dependency installation failed')
        finally:
            if process.poll() is None:
                subprocess.run(['docker', 'rm', '-f', name], timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.kill()
                process.wait(timeout=10)


def execute(repository, sha, encoded_config, encoded_files):
    if not re.fullmatch('[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+', repository) or len(encoded_config) > 12000:
        raise ValueError('Invalid repository test input')
    settings = json.loads(encoded_config)
    suite_sha = settings.pop('suite_sha')
    if not re.fullmatch('[a-f0-9]{40}', suite_sha):
        raise ValueError('Invalid frozen suite revision')
    config = SetupConfig.model_validate(settings)
    from backend.remote_job import decode_gallery_bundle
    # Validation dispatch sends an empty bundle; agent attempts send exact editable scope.
    try: replacements = decode_gallery_bundle(encoded_files, config.editable_files)
    except ValueError:
        replacements = decode_gallery_bundle(encoded_files, [])
    owner, repo = repository.split('/')
    with tempfile.TemporaryDirectory(prefix='torque-repository-') as temporary:
        root = Path(temporary)
        workspace, frozen, suite = root/'source', root/'frozen', root/'suite'
        snapshot(owner, repo, sha, workspace, lambda: None)
        snapshot(owner, repo, suite_sha, frozen, lambda: None)
        suite.mkdir()
        total = 0
        for name in config.test_files:
            source = safe_path(frozen, name)
            total += source.stat().st_size
            from backend.node_repository import frozen_file_limit
            if not source.is_file() or source.stat().st_size > frozen_file_limit(name) or total > 2000000:
                raise ValueError('Frozen tests exceed limit')
            target = safe_path(workspace, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            archived = safe_path(suite/'frozen', name)
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, archived)
        for name, contents in replacements.items():
            safe_path(workspace, name).write_text(contents, encoding='utf-8')
        template = ROOT/'tests/acceptance/repository'
        framework = config.framework
        # Build only a trusted Dockerfile, with no repository-supplied build steps.
        subprocess.run(['docker', 'build', '-t', 'torque-repository-tests', '-f',
                        str(template/('Dockerfile.' + framework)), str(template)], check=True, timeout=180)
        image = subprocess.check_output(['docker', 'image', 'inspect', 'torque-repository-tests', '--format', '{{.Id}}'], text=True).strip()
        for path in workspace.rglob('*'):
            if path.is_file(): path.chmod(0o644)
            elif path.is_dir(): path.chmod(0o777 if framework == 'npm' else 0o755)
        workspace.chmod(0o777 if framework == 'npm' else 0o755)
        # Temp ancestors must be traversable by the unprivileged container UID.
        root.chmod(0o755)
        if framework == 'npm':
            from backend.node_repository import node_layout, test_engine
            package_root, manager = node_layout(config.test_files)
            package = json.loads(safe_path(workspace, (package_root+'/' if package_root else '')+'package.json').read_text())
            engine = test_engine(package)
            config_data = {**config.model_dump(), 'engine': engine, 'package_root':package_root}
            prepare_dependencies(workspace, image, package_root, manager)
            command = ['node', '/acceptance/run.cjs']
            shutil.copyfile(template/'run.cjs', suite/'run.cjs')
        else:
            config_data = config.model_dump()
            prepare_python_dependencies(workspace, image, config.test_files)
            command = ['python', '/acceptance/run.py']
            shutil.copyfile(template/'run.py', suite/'run.py')
        (suite/'config.json').write_text(json.dumps(config_data))
        recipe = Recipe(image=image, command=command, context_files=config.editable_files,
                        editable_files=config.editable_files, acceptance_criteria=['Frozen test suite passes'],
                        suite_directory=str(suite), timeout_seconds=120)
        runner = DockerRunner(recipe)
        runner.preflight()
        result = runner.run(workspace, lambda: None)
        return {'acceptance_profile': 'repository-tests', 'source_repository': repository,
                'suite_revision': suite_sha, 'suite_sha256': runner.suite_sha256,
                'image_digest': image, 'result': result.model_dump()}

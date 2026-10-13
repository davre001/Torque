import pytest
from backend.python_dependencies import requirements


def test_public_python_requirements_with_constraints_and_comments():
    assert requirements('# core\nfastapi\nhttpx>=0.28,<1\npsycopg[binary]>=3.1 # driver\n') == ['fastapi', 'httpx>=0.28,<1', 'psycopg[binary]>=3.1']


@pytest.mark.parametrize('value', ['-r secrets.txt', '--index-url https://example.com', 'git+https://example.com/package', './local-package', 'package @ https://example.com/pkg.whl', '${TOKEN}', '-e .'])
def test_dependency_manifest_cannot_supply_urls_paths_or_options(value):
    with pytest.raises(ValueError):
        requirements(value)


def test_installer_uses_wheels_in_a_container_without_source_or_secrets(tmp_path, monkeypatch):
    from backend.repository_test_job import prepare_python_dependencies
    (tmp_path/'requirements.txt').write_text('fastapi\nhttpx\n')
    calls = []
    class Process:
        returncode = 0
        def __init__(self, args, **kwargs): calls.append(args)
        def poll(self): return 0
    monkeypatch.setattr('backend.repository_test_job.subprocess.Popen', Process)
    monkeypatch.setattr('backend.repository_test_job.os.getuid', lambda: 1001, raising=False)
    monkeypatch.setattr('backend.repository_test_job.os.getgid', lambda: 1001, raising=False)
    prepare_python_dependencies(tmp_path, 'sha256:fixture', ['requirements.txt'])
    args = calls[0]
    assert '--only-binary=:all:' in args
    assert '--isolated' in args
    assert args[-2:] == ['fastapi', 'httpx']
    assert not any('dst=/workspace' in arg for arg in args)
    assert '--read-only' in args and '--cap-drop=ALL' in args
    assert args[args.index('--user') + 1] == '1001:1001'

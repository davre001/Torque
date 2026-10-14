"""Infer managed Node test commands without executing repository scripts."""
import re


def test_engine(package):
    script = package.get('scripts', {}).get('test', '')
    # Accept common watch-mode defaults; the trusted runner forces a single run.
    if not isinstance(script, str) or not re.fullmatch(r'(vitest(?: run)?|jest|node --test)(?: --(?:runInBand|watch=false|passWithNoTests))?', script.strip()):
        raise ValueError('No supported test engine detected in this package')
    return script.strip().split()[0].replace('node', 'node')


def node_layout(test_files):
    manifests = [p for p in test_files if p.endswith('package.json')]
    candidates = [p for p in manifests if any(t.startswith(p[:-12]) and re.search(r'\.(test|spec)\.', t) for t in test_files)]
    # Prefer the closest package to the frozen tests over the workspace root.
    manifest = max(candidates or manifests, key=len)
    return manifest[:-12].rstrip('/'), 'pnpm' if 'pnpm-lock.yaml' in test_files else 'npm'


def frozen_file_limit(path):
    return 1000000 if path.rsplit('/', 1)[-1] in {'pnpm-lock.yaml', 'package-lock.json'} else 100000

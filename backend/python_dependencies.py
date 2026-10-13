"""Public wheel dependencies only: no build scripts, URLs, indexes or secrets."""
import re


def requirements(text):
    if len(text.encode('utf-8')) > 100000:
        raise ValueError('Python dependency manifest exceeds limits')
    packages = []
    pattern = r'[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[A-Za-z0-9_,.-]+\])?(?:[<>=!~]{1,2}[A-Za-z0-9.*+_-]+(?:,[<>=!~]{1,2}[A-Za-z0-9.*+_-]+)*)?'
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        if not re.fullmatch(pattern, line):
            raise ValueError('Python dependencies must be public package names with optional version constraints; URLs, local paths and pip options are unsupported')
        packages.append(line)
    if len(packages) > 100:
        raise ValueError('Python dependency count exceeds limits')
    return packages

"""Credential-free, bounded per-check diagnostics for isolated acceptance suites."""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import io
import time
import traceback


class BoundedOutput(io.StringIO):
    def write(self, value):
        combined=(self.getvalue()+value)[-4000:]
        self.seek(0)
        self.truncate()
        super().write(combined)
        return len(value)


class Reporter:
    def __init__(self):
        self.cases = []

    @contextmanager
    def case(self, name):
        stdout, stderr = BoundedOutput(), BoundedOutput()
        start = time.monotonic()
        record = {'name': name, 'passed': False}
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                yield
            record['passed'] = True
        except Exception:
            record['stacktrace'] = traceback.format_exc()[-6000:]
            raise
        finally:
            record.update(duration_ms=(time.monotonic()-start)*1000,
                          stdout=stdout.getvalue()[-4000:], stderr=stderr.getvalue()[-4000:])
            self.cases.append(record)
            print(('PASS ' if record['passed'] else 'FAIL ')+name, flush=True)
            for key in ('stdout', 'stderr', 'stacktrace'):
                if record.get(key): print(record[key], flush=True)

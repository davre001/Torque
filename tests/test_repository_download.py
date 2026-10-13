from contextlib import contextmanager
from backend.tools import repository


def test_download_batches_lease_checks_and_checks_before_extraction(monkeypatch,tmp_path):
    checks = []
    class Response:
        def raise_for_status(self):
            pass
        def iter_bytes(self,chunk_size):
            assert chunk_size == 65536
            yield from [b"source"] * 1000
    @contextmanager
    def stream(*args,**kwargs):
        yield Response()
    def extract(data,root):
        assert len(checks) == 2
        assert data == b"source" * 1000
        return root
    monkeypatch.setattr(repository.httpx,"stream",stream)
    monkeypatch.setattr(repository.time,"monotonic",lambda:1)
    monkeypatch.setattr(repository,"extract_archive",extract)
    root = tmp_path/"source"
    assert repository.snapshot("owner","repo","a"*40,root,lambda:checks.append(True)) == root


def test_cloud_download_checks_cancellation_without_per_chunk_round_trips(monkeypatch, tmp_path):
    checks = []
    clock = [0]

    class Response:
        def raise_for_status(self): pass
        def iter_bytes(self, chunk_size):
            for second in range(1, 21):
                clock[0] = second
                yield b'source'

    @contextmanager
    def stream(*args, **kwargs):
        yield Response()

    monkeypatch.setattr(repository.httpx, 'stream', stream)
    monkeypatch.setattr(repository.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(repository, 'extract_archive', lambda data, root: root)
    repository.snapshot('owner', 'repo', 'a' * 40, tmp_path/'source', lambda: checks.append(clock[0]))
    assert checks == [0, 10, 20, 20]

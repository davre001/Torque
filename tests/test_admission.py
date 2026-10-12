from concurrent.futures import ThreadPoolExecutor
import pytest
from backend.admission import Admission
from backend.models import AdmissionDenied
from backend.store import Store

def test_atomic_global_reservation_and_idempotency(tmp_path):
    store=Store(tmp_path/'db',clock=lambda:100000)
    store.initialize()
    limits=Admission(queue=20,per_user_active=20,global_usd=2)
    def submit(user):
        try:
            return store.submit('https://github.com/a/b/issues/1',user,user,admission=limits)
        except AdmissionDenied:
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(submit,['a','b','c','d']))
    assert sum(value is not None for value in results)==1
    winner=['a','b','c','d'][next(i for i,r in enumerate(results) if r)]
    assert submit(winner) in results

def test_cancellation_keeps_reservation_until_next_utc_day(tmp_path):
    now=[100000]
    store=Store(tmp_path/'db',clock=lambda:now[0]);store.initialize()
    limits=Admission(per_user_daily=1)
    rid=store.submit('https://github.com/a/b/issues/1','a',admission=limits)
    store.cancel(rid,'a')
    with pytest.raises(AdmissionDenied):
        store.submit('https://github.com/a/b/issues/2','a',admission=limits)
    now[0]+=86400
    assert store.submit('https://github.com/a/b/issues/2','a',admission=limits)

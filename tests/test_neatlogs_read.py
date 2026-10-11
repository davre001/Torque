import httpx
import pytest
from backend.integrations.neatlogs_read import TraceReader, ReadbackUnavailable, HOST

TRACE = 'a'*32


def reader(handler):
    return TraceReader('read-secret', client=httpx.Client(transport=httpx.MockTransport(handler)), wait_seconds=0)


def payload(path, status='ERROR'):
    if '/spans' in path:
        return {'spans':[{'spanId':'root','traceId':TRACE,'spanName':'expected-attempt',
                          'parentSpanId':None,'spanType':'WORKFLOW','status':status,'endedAt':'2026-10-11T00:00:00Z',
                          'messages':'read-secret source prompt'}], 'page':{'hasMore':False,'nextCursor':None}}
    return {'traceId':TRACE,'finalizationStatus':'finalized','spansCount':1,'status':status}


def test_only_read_token_and_safe_complete_fields():
    requests=[]
    def handle(req):
        requests.append(req)
        assert str(req.url).startswith(HOST+'/api/v1/public/traces/'+TRACE)
        assert req.headers['Authorization']=='Bearer read-secret'
        assert req.headers['x-project-id']
        return httpx.Response(200,json={'data':payload(req.url.path)})
    result=reader(handle).read(TRACE,expected_name='expected-attempt')
    assert len(requests)==2
    assert result['finalization_status']=='finalized'
    assert 'read-secret' not in str(result)
    assert 'messages' not in str(result)


@pytest.mark.parametrize('status',[401,403,404,409,429,503,302])
def test_failures_do_not_leak_server_body(status):
    r=reader(lambda req:httpx.Response(status,text='read-secret sensitive payload'))
    with pytest.raises(ReadbackUnavailable) as exc:r.read(TRACE)
    assert 'read-secret' not in str(exc.value)


@pytest.mark.parametrize('mutation',[ 'pending','dlq','wrong-id','count','foreign-span','wrong-name','unfinished','orphan','truncated'])
def test_incomplete_or_unrelated_trace_is_not_recovery_evidence(mutation):
    def handle(req):
        data=payload(req.url.path)
        if '/spans' in req.url.path:
            s=data['spans'][0]
            if mutation=='foreign-span':s['traceId']='b'*32
            if mutation=='wrong-name':s['spanName']='different-run'
            if mutation=='unfinished':s['endedAt']=None
            if mutation=='orphan':s['parentSpanId']='missing'
            if mutation=='truncated':data['page']={'hasMore':True,'nextCursor':None}
        else:
            if mutation in {'pending','dlq'}:data['finalizationStatus']=mutation
            if mutation=='wrong-id':data['traceId']='b'*32
            if mutation=='count':data['spansCount']=2
        return httpx.Response(200,json={'data':data})
    with pytest.raises(ReadbackUnavailable):reader(handle).read(TRACE,expected_name='expected-attempt')


def test_missing_token_makes_no_request():
    def handle(req):raise AssertionError('Must not use SDK key as read token')
    with pytest.raises(ReadbackUnavailable):TraceReader('',client=httpx.Client(transport=httpx.MockTransport(handle))).read(TRACE)


def test_cyclic_hierarchy_is_rejected():
    def handle(req):
        data=payload(req.url.path)
        if '/spans' in req.url.path:
            base=data['spans'][0]
            data['spans'] += [{**base,'spanId':'a','parentSpanId':'b'},
                              {**base,'spanId':'b','parentSpanId':'a'}]
        else:data['spansCount']=3
        return httpx.Response(200,json={'data':data})
    with pytest.raises(ReadbackUnavailable,match='Cyclic'):reader(handle).read(TRACE)


def test_cancellation_is_not_converted_to_local_fallback():
    from backend.models import Cancelled
    def check():raise Cancelled()
    def handle(req):raise AssertionError('No request after cancellation')
    with pytest.raises(Cancelled):reader(handle).read(TRACE,check)

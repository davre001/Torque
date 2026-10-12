import asyncio
from types import SimpleNamespace
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from backend.config import Settings
from backend.public_boundary import PublicPolicy, PublicBoundary
from backend.store import Store


def test_public_policy_rejects_operator_and_insecure_origins(monkeypatch):
    monkeypatch.setenv('TORQUE_PUBLIC_MODE', '1')
    auth = SimpleNamespace(configured=True, callback='https://api.example.test/api/auth/github/callback', origin='https://example.test')
    assert PublicPolicy.load(SimpleNamespace(operator_token=''), auth).host == 'api.example.test'
    with pytest.raises(ValueError): PublicPolicy.load(SimpleNamespace(operator_token='operator-secret'), auth)
    auth.origin = 'http://localhost:3000'
    with pytest.raises(ValueError): PublicPolicy.load(SimpleNamespace(operator_token=''), auth)


def test_actual_stream_size_and_shared_rate_counters(tmp_path):
    store = Store(tmp_path/'db'); store.initialize()
    calls = []
    async def app(scope, receive, send):
        calls.append((await receive())['body'])
        await send({'type':'http.response.start','status':200,'headers':[]})
        await send({'type':'http.response.body','body':b'ok'})
    policy = PublicPolicy('api.example.test', max_body=4, per_ip_minute=2, global_minute=3)
    def request(boundary, chunks, ip='127.0.0.1'):
        messages=[{'type':'http.request','body':c,'more_body':i<len(chunks)-1} for i,c in enumerate(chunks)]
        output=[]
        async def receive(): return messages.pop(0)
        async def send(message): output.append(message)
        asyncio.run(boundary({'type':'http','client':(ip,1),'headers':[]},receive,send))
        return output[0]['status']
    first = PublicBoundary(app, store, policy); second = PublicBoundary(app, store, policy)
    assert request(first,[b'ab',b'cde']) == 413
    assert request(second,[b'ab',b'cd']) == 200
    assert calls == [b'abcd']
    assert request(first,[b'a']) == 429  # Shared across boundary instances.
    assert request(second,[b'a'],'127.0.0.2') == 200
    assert request(first,[b'a'],'127.0.0.3') == 429  # Deployment-wide cap.


def test_public_api_minimal_health_host_check_and_no_operator_access(tmp_path, monkeypatch):
    from backend.api import create_app
    for key,value in {'TORQUE_PUBLIC_MODE':'1', 'GITHUB_APP_ID':'12',
                      'GITHUB_APP_CLIENT_ID':'fixture', 'GITHUB_APP_CLIENT_SECRET':'fixture',
                      'TORQUE_SESSION_ENCRYPTION_KEY':Fernet.generate_key().decode(),
                      'GITHUB_APP_CALLBACK_URL':'https://api.example.test/api/auth/github/callback',
                      'TORQUE_FRONTEND_ORIGIN':'https://example.test'}.items(): monkeypatch.setenv(key,value)
    app = create_app(Settings(tmp_path/'db'))
    with TestClient(app, base_url='https://api.example.test') as client:
        assert client.get('/health').json() == {'status':'ok'}
        assert client.get('/api/runs', headers={'Authorization':'Bearer fixture'}).status_code == 401
        assert client.get('/api/runs').status_code == 401
        assert client.get('/health', headers={'Host':'attacker.example.test'}).status_code == 400


def test_public_proxy_secret_and_secure_oauth_cookie(tmp_path,monkeypatch):
    from backend.api import create_app
    values={'TORQUE_PUBLIC_MODE':'1','GITHUB_APP_ID':'12','GITHUB_APP_CLIENT_ID':'fixture',
            'GITHUB_APP_CLIENT_SECRET':'fixture','TORQUE_SESSION_ENCRYPTION_KEY':Fernet.generate_key().decode(),
            'GITHUB_APP_CALLBACK_URL':'https://frontend.example.test/api/auth/github/callback',
            'TORQUE_FRONTEND_ORIGIN':'https://frontend.example.test',
            'TORQUE_BACKEND_ORIGIN':'https://backend.example.test','TORQUE_PROXY_SECRET':'fixture-proxy-secret'}
    for key,value in values.items():monkeypatch.setenv(key,value)
    app=create_app(Settings(tmp_path/'db'))
    with TestClient(app,base_url='https://backend.example.test') as client:
        assert client.get('/health').status_code==200
        assert client.get('/api/auth/github/connect').status_code==403
        response=client.get('/api/auth/github/connect',headers={'x-torque-proxy-secret':'fixture-proxy-secret'},follow_redirects=False)
        assert response.status_code==302
        cookie=response.headers['set-cookie']
        assert '__Host-torque_oauth' in cookie and 'Secure' in cookie and 'HttpOnly' in cookie
        assert 'Domain=' not in cookie

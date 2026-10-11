import hashlib,json,time
from urllib.parse import urlparse,parse_qs
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from backend.api import create_app
from backend.config import Settings
from backend.github_auth import digest


def setup(tmp_path,monkeypatch):
    for k,v in {'GITHUB_APP_ID':'12','GITHUB_APP_CLIENT_ID':'client','GITHUB_APP_CLIENT_SECRET':'secret','TORQUE_SESSION_ENCRYPTION_KEY':Fernet.generate_key().decode(),'GITHUB_APP_CALLBACK_URL':'http://localhost:8000/api/auth/github/callback','TORQUE_FRONTEND_ORIGIN':'http://localhost:3000'}.items(): monkeypatch.setenv(k,v)
    app=create_app(Settings(tmp_path/'db',allowed_repositories=('source/demo',)))
    return app


def seed(app,user,raw):
    auth=app.state.github_auth
    with app.state.store.transaction() as db:
        db.execute('INSERT OR IGNORE INTO users VALUES(?,?,?)',(user,'alice',time.time()))
        db.execute('INSERT INTO github_connections VALUES(?,?,?,?,0)',(user,'alice',auth.cipher.encrypt(b'user-token').decode(),time.time()+3600))
        db.execute('INSERT INTO browser_sessions VALUES(?,?,?,?)',(digest(raw),user,'csrf',time.time()+3600))


def test_sessions_csrf_ownership_disconnect(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    with TestClient(app) as c:
        seed(app,'github:1','session1');seed(app,'github:2','session2')
        run=app.state.store.submit('https://github.com/source/demo/issues/4','github:2')
        c.cookies.set('torque_session','session1')
        assert c.get('/api/auth/session').json()['github_login']=='alice'
        assert c.get('/api/runs/'+run).status_code==404
        assert c.post('/api/auth/disconnect').status_code==403
        assert c.post('/api/auth/disconnect',headers={'Origin':'https://evil.test','X-CSRF-Token':'csrf'}).status_code==403
        own=app.state.store.submit('https://github.com/source/demo/issues/4','github:1')
        assert c.post('/api/auth/disconnect',headers={'Origin':'http://localhost:3000','X-CSRF-Token':'csrf'}).status_code==200
        assert app.state.store.get(own)['cancel_requested']
        c.cookies.set('torque_session','session1')
        assert c.get('/api/auth/session').status_code==401
        with app.state.store.transaction() as db:
            assert db.execute('SELECT token FROM github_connections WHERE user_id=?',('github:1',)).fetchone()[0]==''


def test_oauth_state_pkce_and_replay(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    auth=app.state.github_auth
    monkeypatch.setattr(auth,'api',lambda token,path:{'id':123,'login':'alice'})
    class Response:
        status_code=200
        def json(self):return {'access_token':'provider-secret','expires_in':28800}
    def post(self,url,**kwargs):
        assert kwargs['data']['code_verifier']
        return Response()
    monkeypatch.setattr('httpx.Client.post',post)
    with TestClient(app) as c:
        start=c.get('/api/auth/github/connect',follow_redirects=False)
        params=parse_qs(urlparse(start.headers['location']).query)
        assert params['code_challenge_method']==['S256']
        state=params['state'][0]
        assert c.get('/api/auth/github/callback?state=bad&code=x').status_code==400
        response=c.get('/api/auth/github/callback',params={'state':state,'code':'x'},follow_redirects=False)
        assert response.status_code==302
        assert response.headers['location']=='http://localhost:3000/workspace'
        assert 'HttpOnly' in response.headers['set-cookie']
        assert c.get('/api/auth/session').json()['user_id']=='github:123'
        c.cookies.set('torque_oauth',state)
        assert c.get('/api/auth/github/callback',params={'state':state,'code':'x'}).status_code==400
        with app.state.store.transaction() as db:
            row=db.execute('SELECT token FROM github_connections').fetchone()
            assert 'provider-secret' not in row[0]


def test_installation_permissions_and_wrong_app(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    with TestClient(app) as c:
        seed(app,'github:1','session1')
        auth=app.state.github_auth
        install={'id':7,'app_id':12,'permissions':{'contents':'read','issues':'read','pull_requests':'read'}}
        repo={'id':9,'full_name':'source/demo','private':False,'permissions':{'push':True}}
        monkeypatch.setattr(auth,'api',lambda token,path:{'installations':[install]} if path.startswith('/user/installations?') else {'repositories':[repo]})
        assert auth.authorize('github:1','source/demo')=='user-token'
        import pytest
        from fastapi import HTTPException
        with pytest.raises(HTTPException):auth.authorize('github:1','source/demo',write=True)
        install['app_id']=99
        with pytest.raises(HTTPException):auth.authorize('github:1','source/demo')
        c.cookies.set('torque_session','session1')
        assert c.post('/api/runs',json={'issue_url':'https://github.com/source/demo/issues/4'},headers={'Origin':'http://localhost:3000','X-CSRF-Token':'csrf'}).status_code==403

def test_signed_revocation_and_publication_disconnect_fence(tmp_path,monkeypatch):
    import hmac,pytest
    from backend.models import Conflict,Status
    app=setup(tmp_path,monkeypatch)
    monkeypatch.setenv('GITHUB_APP_WEBHOOK_SECRET','webhook-secret')
    with TestClient(app) as c:
        seed(app,'github:1','session1')
        run=app.state.store.submit('https://github.com/source/demo/issues/4','github:1')
        _,owner=app.state.store.claim(60)
        app.state.store.update(run,owner,Status.READY,result={'verified':True})
        publication=app.state.store.claim_publication(run,'github:1','alice/demo')
        c.cookies.set('torque_session','session1')
        headers={'Origin':'http://localhost:3000','X-CSRF-Token':'csrf'}
        assert c.post('/api/auth/disconnect',headers=headers).status_code==409
        app.state.store.finish_publication(run,publication,error='test')
        body=json.dumps({'action':'revoked','sender':{'id':1}}).encode()
        assert c.post('/api/auth/github/webhook',content=body).status_code==401
        signature='sha256='+hmac.new(b'webhook-secret',body,hashlib.sha256).hexdigest()
        assert c.post('/api/auth/github/webhook',content=body,headers={'X-Hub-Signature-256':signature,'X-GitHub-Event':'github_app_authorization'}).status_code==200
        assert c.get('/api/auth/session').status_code==401
        with pytest.raises(Conflict,match='disconnected'):
            app.state.store.claim_publication(run,'github:1','alice/demo')


def test_secure_cookie_and_expired_session(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    auth=app.state.github_auth
    auth.secure=True;auth.cookie='__Host-torque_session';auth.state_cookie='__Host-torque_oauth'
    with TestClient(app,base_url='https://testserver') as c:
        response=c.get('/api/auth/github/connect',follow_redirects=False)
        cookie=response.headers['set-cookie']
        assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=lax' in cookie and 'Domain=' not in cookie
        seed(app,'github:1','old')
        with app.state.store.transaction() as db:
            db.execute('UPDATE browser_sessions SET expires=0')
        c.cookies.set(auth.cookie,'old')
        assert c.get('/api/auth/session').status_code==401

def test_local_login_redirects_to_callback_host_before_setting_cookie(tmp_path,monkeypatch):
    app=setup(tmp_path,monkeypatch)
    with TestClient(app,base_url='http://127.0.0.1:8000') as c:
        response=c.get('/api/auth/github/connect',follow_redirects=False)
        assert response.status_code==302
        assert response.headers['location']=='http://localhost:8000/api/auth/github/connect'
        assert 'set-cookie' not in response.headers
    with TestClient(app,base_url='http://localhost:8000') as c:
        response=c.get('/api/auth/github/connect',follow_redirects=False)
        assert response.headers['location'].startswith('https://github.com/login/oauth/authorize?')
        assert 'set-cookie' in response.headers
        c.cookies.clear()
        response=c.get('/api/auth/github/callback',params={'state':'provided','code':'unused'})
        assert response.status_code==400
        assert 'cookie missing' in response.json()['detail']

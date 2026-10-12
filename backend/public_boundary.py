"""Opt-in public API boundary; shared SQLite rate counters, no caller credentials."""
from dataclasses import dataclass
import hashlib
import os
import time
from urllib.parse import urlparse
from starlette.responses import JSONResponse


@dataclass(frozen=True)
class PublicPolicy:
    host: str
    max_body: int = 65536
    per_ip_minute: int = 120
    global_minute: int = 600

    @classmethod
    def load(cls, settings, auth):
        mode = os.getenv('TORQUE_PUBLIC_MODE', '0')
        if mode not in {'0', '1'}: raise ValueError('TORQUE_PUBLIC_MODE must be 0 or 1')
        if mode == '0': return None
        callback, origin = urlparse(auth.callback), urlparse(auth.origin)
        if not auth.configured or settings.operator_token or any(
                u.scheme != 'https' or not u.hostname or u.hostname in {'localhost','127.0.0.1'}
                for u in (callback, origin)):
            raise ValueError('Public mode requires GitHub App HTTPS origins and disabled operator bearer access')
        result = cls(callback.hostname,
                     int(os.getenv('TORQUE_HTTP_BODY_BYTES', '65536')),
                     int(os.getenv('TORQUE_HTTP_IP_PER_MINUTE', '120')),
                     int(os.getenv('TORQUE_HTTP_GLOBAL_PER_MINUTE', '600')))
        if min(result.max_body, result.per_ip_minute, result.global_minute) <= 0:
            raise ValueError('Public request limits must be positive')
        return result


class PublicBoundary:
    def __init__(self, app, store, policy):
        self.app, self.store, self.policy = app, store, policy

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        async def deny(code, detail, headers=None):
            await JSONResponse({'detail':detail}, status_code=code,
                               headers={'Cache-Control':'no-store', **(headers or {})})(scope, receive, send)
        headers = dict(scope.get('headers', []))
        length = headers.get(b'content-length')
        if length is not None:
            try: declared = int(length)
            except ValueError: return await deny(400, 'Invalid request length')
            if declared < 0: return await deny(400, 'Invalid request length')
            if declared > self.policy.max_body: return await deny(413, 'Request body too large')
        try:
            window = int(time.time() // 60)
            address = (scope.get('client') or ('unknown', 0))[0]
            actor = hashlib.sha256(address.encode()).hexdigest()
            with self.store.transaction() as db:
                db.execute('CREATE TABLE IF NOT EXISTS http_admission (window INTEGER, actor TEXT, count INTEGER NOT NULL, PRIMARY KEY(window,actor))')
                db.execute('DELETE FROM http_admission WHERE window < ?', (window,))
                count = db.execute('SELECT count FROM http_admission WHERE window=? AND actor=?', (window, actor)).fetchone()
                total = db.execute('SELECT COALESCE(SUM(count),0) FROM http_admission WHERE window=?', (window,)).fetchone()[0]
                blocked = (count[0] if count else 0) >= self.policy.per_ip_minute or total >= self.policy.global_minute
                if not blocked:
                    db.execute('INSERT INTO http_admission VALUES(?,?,1) ON CONFLICT(window,actor) DO UPDATE SET count=count+1', (window,actor))
        except Exception:
            return await deny(503, 'Request admission unavailable')
        if blocked: return await deny(429, 'Request rate limit reached', {'Retry-After':str(60-int(time.time()%60))})
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect': return
            body.extend(message.get('body', b''))
            if len(body) > self.policy.max_body: return await deny(413, 'Request body too large')
            if not message.get('more_body', False): break
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered: return await receive()
            delivered = True
            return {'type':'http.request', 'body':bytes(body), 'more_body':False}
        return await self.app(scope, replay, send)

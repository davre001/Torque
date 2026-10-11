"""Bounded, read-only Public API access. SDK ingest keys are never read credentials."""
import os
import re
import time
import httpx
from backend.models import PipelineError

PROJECT = '00fd5eb9-0f63-473e-babc-4621191e4a4d'
HOST = 'https://app.neatlogs.com'


class ReadbackUnavailable(PipelineError):
    pass


class TraceReader:
    def __init__(self, token=None, project=None, client=None, wait_seconds=20):
        self.token = token if token is not None else os.getenv('NEATLOGS_TOKEN', '')
        self.project = project or os.getenv('NEATLOGS_PROJECT_ID', PROJECT)
        self.client = client or httpx.Client(timeout=5, follow_redirects=False)
        self.owned = client is None
        self.wait_seconds = wait_seconds

    @property
    def configured(self):
        return bool(self.token)

    def close(self):
        if self.owned:
            self.client.close()

    def get(self, path, check):
        if not self.configured:
            raise ReadbackUnavailable('Neatlogs read token is not configured')
        check()
        try:
            # Streaming caps even unsuccessful/malformed responses; never export raw bodies.
            with self.client.stream('GET', HOST+'/api/v1/public/'+path,
                                    headers={'Authorization': 'Bearer '+self.token,
                                             'x-project-id': self.project}) as response:
                status = response.status_code
                if status != 200:
                    raise ReadbackUnavailable(f'Neatlogs readback HTTP {status}')
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 262144:
                        raise ReadbackUnavailable('Neatlogs readback exceeds size limit')
                import json
                envelope = json.loads(data)
                if not isinstance(envelope, dict) or not isinstance(envelope.get('data'), dict):
                    raise ValueError()
                return envelope['data']
        except (httpx.HTTPError, ValueError):
            raise ReadbackUnavailable('Neatlogs readback unavailable or invalid') from None

    def read(self, trace_id, check=lambda: None, expected_name=None):
        if not re.fullmatch('[0-9a-f]{32}', trace_id):
            raise ReadbackUnavailable('Invalid Neatlogs trace ID')
        deadline = time.monotonic()+self.wait_seconds
        while True:
            try:
                trace = self.get('traces/'+trace_id, check)
                if trace.get('traceId') != trace_id:
                    raise ReadbackUnavailable('Neatlogs returned a different trace')
                if trace.get('finalizationStatus') == 'dlq':
                    raise ReadbackUnavailable('Neatlogs trace finalization failed')
                if trace.get('finalizationStatus') != 'finalized':
                    raise ReadbackUnavailable('Neatlogs trace is not finalized')
                break
            except ReadbackUnavailable as exc:
                retryable = str(exc) in {'Neatlogs readback HTTP 404', 'Neatlogs readback HTTP 409',
                                        'Neatlogs trace is not finalized'}
                if not retryable or time.monotonic() >= deadline:
                    raise
                check()
                time.sleep(min(1, max(0, deadline-time.monotonic())))
        spans, cursor = [], None
        for _ in range(4):
            from urllib.parse import urlencode
            params = {'limit': 50}
            if cursor:
                params['cursor'] = cursor
            page = self.get('traces/'+trace_id+'/spans?'+urlencode(params), check)
            batch = page.get('spans')
            if not isinstance(batch, list) or len(batch)>50 or any(not isinstance(s, dict) for s in batch):
                raise ReadbackUnavailable('Invalid Neatlogs span page')
            spans.extend(batch)
            paging = page.get('page', {})
            if not isinstance(paging, dict):
                raise ReadbackUnavailable('Invalid Neatlogs pagination')
            cursor = paging.get('nextCursor')
            if not cursor and not paging.get('hasMore'):
                break
            if not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024:
                raise ReadbackUnavailable('Incomplete Neatlogs span pagination')
        else:
            raise ReadbackUnavailable('Neatlogs span pagination exceeds limit')
        if any(not isinstance(s.get('spanId'),str) or not 1<=len(s['spanId'])<=128 or
               (s.get('parentSpanId') is not None and not isinstance(s['parentSpanId'],str)) for s in spans):
            raise ReadbackUnavailable('Invalid Neatlogs span identity')
        ids = {s.get('spanId') for s in spans}
        if not spans or len(ids) != len(spans) or None in ids or trace.get('spansCount') != len(spans):
            raise ReadbackUnavailable('Incomplete Neatlogs trace spans')
        if any(s.get('traceId') != trace_id or not s.get('endedAt') or
               (s.get('parentSpanId') and s['parentSpanId'] not in ids) for s in spans):
            raise ReadbackUnavailable('Neatlogs span identity or hierarchy mismatch')
        roots = [s for s in spans if not s.get('parentSpanId')]
        if len(roots) != 1 or (expected_name and roots[0].get('spanName') != expected_name):
            raise ReadbackUnavailable('Neatlogs attempt identity mismatch')
        parents={s['spanId']:s.get('parentSpanId') for s in spans}
        for span_id in ids:
            seen=set()
            while span_id:
                if span_id in seen:
                    raise ReadbackUnavailable('Cyclic Neatlogs span hierarchy')
                seen.add(span_id)
                span_id=parents[span_id]
        # Safe fields only; payloads, prompts, credentials and repository contents stay out.
        return {'trace_id': trace_id, 'project_id': self.project, 'host': HOST,
                'finalization_status': 'finalized', 'status': trace.get('status'),
                'total_tokens':trace.get('totalTokens'), 'llm_calls':trace.get('llmCallsCount'),
                'spans': [{k: s.get(k) for k in ('spanId', 'parentSpanId', 'spanName', 'spanType', 'status',
                                               'model','provider','totalTokens')}
                          for s in spans]}

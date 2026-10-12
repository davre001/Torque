"""Small bounded Streamable HTTP client for diagnostic MCP readback."""
import json
import os
import httpx
from backend.models import PipelineError


class NeatlogsMCP:
    def __init__(self):
        self.client=httpx.Client(timeout=25,follow_redirects=False,
            headers={'Authorization':'Bearer '+os.getenv('NEATLOGS_API_KEY',''),
                     'Accept':'application/json, text/event-stream'})
        self.counter=0
        self.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},
            'clientInfo':{'name':'torque-diagnostics','version':'1.0'}})
        self.client.post('https://ingest.neatlogs.com/mcp',json={
            'jsonrpc':'2.0','method':'notifications/initialized'})

    def request(self, method, params):
        self.counter+=1
        with self.client.stream('POST','https://ingest.neatlogs.com/mcp',json={
                'jsonrpc':'2.0','id':self.counter,'method':method,'params':params}) as response:
            if response.status_code!=200:
                raise PipelineError(f'Neatlogs MCP HTTP {response.status_code}')
            session=response.headers.get('mcp-session-id')
            if session:self.client.headers['mcp-session-id']=session
            data=bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data)>1_000_000:raise PipelineError('Neatlogs MCP response exceeds limit')
        raw=data.decode()
        if raw.lstrip().startswith('{'):envelope=json.loads(raw)
        else:
            entries=[json.loads(line[5:].strip()) for line in raw.splitlines() if line.startswith('data:')]
            envelope=next((e for e in entries if e.get('id')==self.counter),{})
        if 'error' in envelope:raise PipelineError('Neatlogs MCP returned an RPC error')
        return envelope.get('result',{})

    def call(self, name, arguments):
        result=self.request('tools/call',{'name':name,'arguments':arguments})
        if result.get('isError'):raise PipelineError('Neatlogs MCP tool failed')
        if 'structuredContent' in result:return result['structuredContent']
        for block in result.get('content',[]):
            if block.get('type')=='text':
                try:return json.loads(block['text'])
                except ValueError:pass
        raise PipelineError('Neatlogs MCP tool returned no structured data')

    def close(self):
        self.client.close()

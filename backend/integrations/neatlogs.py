"""One telemetry generation per worker; mask content and credentials at export."""
from contextlib import contextmanager
import neatlogs
from backend.artifacts import Artifacts

class Telemetry:
    def __init__(self,key,secrets=()):
        self.active = bool(key)
        self.redactor = Artifacts(".",secrets)
        if self.active:
            neatlogs.init(api_key=key,endpoint="https://ingest.neatlogs.com",
                          workflow_name="github-issue-to-pr",mask=self.mask,
                          register_shutdown_handlers=False)

    def mask(self, span):
        # Preserve model/usage/status metadata; never export source/prompt content.
        content_keys = ('input.value','output.value','prompt','completion','messages',
                        'exception.message','exception.stacktrace','gen_ai.input.messages',
                        'gen_ai.output.messages','llm.input_messages','llm.output_messages',
                        'ai.prompt','ai.response.text','llm.prompts','gen_ai.prompt','gen_ai.completion')
        def content_key(key):
            return key in content_keys or any(key.startswith(prefix+'.') for prefix in
                                             ('llm.input_messages','llm.output_messages','llm.prompts',
                                              'gen_ai.prompt','gen_ai.completion'))
        def clean(value):
            if isinstance(value,dict):
                return {k:("[content omitted]" if content_key(k)
                           else clean(v)) for k,v in value.items()}
            if isinstance(value,list):
                return [clean(v) for v in value]
            return self.redactor.sanitize(value)
        return clean(span)

    def wrap(self,client):
        return neatlogs.wrap(client) if self.active else client

    @contextmanager
    def attempt(self, name, **attributes):
        # A closed root is readable while the enclosing issue workflow stays active.
        from opentelemetry.context import Context, attach, detach
        token = attach(Context())
        try:
            with self.span(name, 'WORKFLOW', **attributes) as span:
                yield span
        finally:
            detach(token)

    def flush(self):
        return neatlogs.flush(timeout_millis=5000) if self.active else True

    @contextmanager
    def span(self,name,kind="TOOL",**attributes):
        if not self.active:
            yield None
            return
        with neatlogs.trace(name,kind=kind,**attributes) as span:
            try:
                yield span
            except BaseException:
                from opentelemetry.trace import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR,"Operation failed; details kept in sanitized local artifacts"))
                raise

    def close(self):
        if self.active:
            try:
                neatlogs.flush()
            finally:
                neatlogs.shutdown()

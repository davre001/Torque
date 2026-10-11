"""OpenAI-compatible gateway client, wrapped once for Neatlogs."""
from urllib.parse import urlparse
from backend.models import PipelineError
from backend.integrations.providers import Response

class LiteLLM:
    def __init__(self,key,base_url,model,wrap=lambda client:client):
        parsed = urlparse(base_url)
        if not key or not model or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise PipelineError("Configure LiteLLM key, HTTPS base URL, and exact gateway model alias")
        from openai import OpenAI
        self.model = model
        self.client = wrap(OpenAI(api_key=key,base_url=base_url,timeout=45,max_retries=0))

    def complete(self,prompt,max_output_tokens):
        result = self.client.chat.completions.create(
            model=self.model,messages=[{"role":"user","content":prompt}],
            max_tokens=max_output_tokens)
        usage = result.usage
        return Response(result.choices[0].message.content or "",
                        usage.prompt_tokens if usage else None,
                        usage.completion_tokens if usage else None,self.model)

    def close(self):
        self.client.close()

"""Google GenAI generate-content client, created after telemetry initialization."""
from backend.models import PipelineError
from backend.integrations.providers import Response

class Gemini:
    def __init__(self,key,model,wrap=lambda client:client):
        if not key or not model:
            raise PipelineError("Configure Gemini key and model identifier")
        from google import genai
        from google.genai import types
        self.model = model
        self.client = wrap(genai.Client(api_key=key,http_options=types.HttpOptions(
            timeout=120000,retry_options=types.HttpRetryOptions(attempts=1))))

    def complete(self,prompt,max_output_tokens):
        return self._complete(prompt,max_output_tokens)

    def complete_structured(self,prompt,max_output_tokens,schema):
        return self._complete(prompt,max_output_tokens,schema.model_json_schema())

    def _complete(self,prompt,max_output_tokens,json_schema=None):
        from google.genai import types
        result = self.client.models.generate_content(
            model=self.model,contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json",
                                               response_json_schema=json_schema,
                                               max_output_tokens=max_output_tokens))
        usage = result.usage_metadata
        incoming = usage.prompt_token_count if usage else None
        outgoing = None if usage is None or usage.candidates_token_count is None else (
            usage.candidates_token_count+(usage.thoughts_token_count or 0))
        return Response(result.text or "",incoming,outgoing,self.model)

    def close(self):
        self.client.close()

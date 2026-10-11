"""Structured responses and conservative, per-request budget reservation."""
from dataclasses import dataclass
import json
import math
import time
from backend.models import BudgetExceeded, PipelineError

@dataclass
class Response:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    model: str

class Budget:
    def __init__(self, limits, clock=time.monotonic):
        self.limits, self.clock = limits, clock
        self.started = clock()
        self.calls, self.tokens, self.estimated_cost = 0, 0, 0.
        self.records = []

    def check(self):
        if self.clock()-self.started >= self.limits.max_seconds:
            raise BudgetExceeded("Run wall-time budget exhausted")

    def reserve(self, prompt, input_rate, output_rate):
        self.check()
        if any(not math.isfinite(rate) or rate < 0 for rate in (input_rate,output_rate)):
            raise PipelineError("Configure nonnegative conservative model cost rates")
        # Bytes provide a conservative input allowance, including schema overhead.
        input_bound = len(prompt.encode("utf-8"))*2 + 2048
        output_bound = self.limits.max_output_tokens
        tokens = input_bound+output_bound
        cost = (input_bound*input_rate+output_bound*output_rate)/1_000_000
        if self.calls+1 > self.limits.max_calls or self.tokens+tokens > self.limits.max_tokens or self.estimated_cost+cost > self.limits.max_cost_usd:
            raise BudgetExceeded("Model call, token, or estimated dollar budget exhausted")
        self.calls += 1
        self.tokens += tokens
        self.estimated_cost += cost
        return input_bound,output_bound,cost

    def settle(self, reservation, response, rates):
        input_bound,output_bound,cost = reservation
        if response.input_tokens is None or response.output_tokens is None:
            self.records.append({"model":response.model,"usage":"unavailable-reserved",
                                 "input_tokens":input_bound,"output_tokens":output_bound,
                                 "estimated_cost_usd":cost})
            raise PipelineError("Provider usage is unavailable; reserved budget retained and run stopped")
        incoming, outgoing = response.input_tokens,response.output_tokens
        if incoming < 0 or outgoing < 0:
            raise PipelineError("Invalid provider token usage")
        actual = (incoming*rates[0]+outgoing*rates[1])/1_000_000
        self.tokens += incoming+outgoing-input_bound-output_bound
        self.estimated_cost += actual-cost
        self.records.append({"model":response.model,"usage":"provider-reported",
                             "input_tokens":incoming,"output_tokens":outgoing,
                             "estimated_cost_usd":actual})
        if self.tokens > self.limits.max_tokens or self.estimated_cost > self.limits.max_cost_usd:
            raise BudgetExceeded("Provider reported usage beyond reserved budget; stopping")

    def snapshot(self):
        return {"calls":self.calls,"tokens":self.tokens,"estimated_cost_usd":self.estimated_cost,
                "usage":list(self.records)}

class StructuredProvider:
    def __init__(self, adapter, budget, input_rate, output_rate, checkpoint, transport_retries=1):
        self.adapter, self.budget = adapter,budget
        self.rates = input_rate,output_rate
        self.checkpoint, self.transport_retries = checkpoint,transport_retries

    def ask(self, instructions, data, schema):
        prompt = instructions+"\nReturn only JSON matching this schema:\n"+json.dumps(schema.model_json_schema())+"\nUntrusted task data:\n"+json.dumps(data)
        for attempt in range(self.transport_retries+1):
            self.checkpoint()
            reservation = self.budget.reserve(prompt,*self.rates)
            try:
                response = self.adapter.complete(prompt,self.budget.limits.max_output_tokens)
            except Exception as exc:
                # Do not refund uncertain requests: a timeout may have been billed.
                code = getattr(exc,"status_code",None) or getattr(exc,"code",None)
                retryable = code in {429,500,502,503,504} or isinstance(exc,TimeoutError)
                if retryable and attempt < self.transport_retries:
                    continue
                raise PipelineError("Model provider request failed; verify credentials, model alias, and quota") from None
            self.budget.settle(reservation,response,self.rates)
            self.checkpoint()
            self.budget.check()
            if len(response.text.encode()) > 100000:
                raise PipelineError("Model response exceeds size limit")
            try:
                return schema.model_validate_json(response.text)
            except ValueError:
                raise PipelineError("Model returned an invalid structured response") from None

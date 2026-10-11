from backend.integrations.neatlogs import Telemetry


def test_content_mask_preserves_typed_usage_and_status():
    t=Telemetry('', ['secret'])
    masked=t.mask({'attributes':{'gen_ai.usage.prompt_tokens':42,'llm.token_count.completion':7,
                                 'prompt':'source secret','input.value':'private code',
                                 'llm.input_messages.0.message.content':'private code'},
                   'status':{'code':'ERROR','description':'test failed'},
                   'events':[{'attributes':{'exception.message':'secret source'}}]})
    assert masked['attributes']['gen_ai.usage.prompt_tokens']==42
    assert masked['attributes']['llm.token_count.completion']==7
    assert masked['attributes']['prompt']=='[content omitted]'
    assert masked['attributes']['llm.input_messages.0.message.content']=='[content omitted]'
    assert masked['status']['code']=='ERROR'
    assert 'secret' not in str(masked)

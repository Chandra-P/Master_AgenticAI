from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import os
import json


def hosted_error_message(error):
    status=getattr(error,'status_code',None)
    reasons={401:'The server API key was rejected. The owner must replace it in hosting secrets.',
        403:'The server key lacks permission for the selected model or project.',
        404:'The configured model is unavailable to this server account.',
        429:'The hosted model quota or rate limit was reached. Please retry later.',
        400:'The hosted model rejected the request or could not produce the required JSON response.'}
    if status in reasons:
        return f'Hosted generation failed (HTTP {status}). '+reasons[status]
    from pydantic import ValidationError
    if isinstance(error,ValidationError):
        return 'Hosted generation failed: the model response did not match the required evidence schema. Please retry.'
    return 'Hosted generation failed. The server owner should check the configured model, API access and free-tier rate limits. Please retry later.'


class OllamaGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.model=ChatOllama(model=settings.generation_model,base_url=settings.ollama_url,
                             temperature=0,num_ctx=4096,num_predict=512,client_kwargs={'timeout':240})

    def generate_json(self, system, prompt, schema):
        try:
            template=ChatPromptTemplate.from_messages([('system','{system}'),('human','{question}')])
            chain=template | self.model.with_structured_output(schema,method='json_schema')
            result=chain.invoke({'system':system,'question':prompt})
            return result if isinstance(result,schema) else schema.model_validate(result)
        except Exception as error:
            raise RuntimeError(f'Local generation failed. Check Ollama and model {self.settings.generation_model}: {error}') from error


class OpenAIGenerator:
    """Optional server-owned OpenAI adapter, using the existing httpx dependency."""
    def __init__(self, settings):
        if not os.getenv('OPENAI_API_KEY', '').strip():
            raise RuntimeError('Configure OPENAI_API_KEY in the server environment or private Streamlit secrets.')
        self.settings = settings

    def generate_json(self, system, prompt, schema):
        import httpx
        # OpenAI strict schemas require every property and forbid extra object keys.
        def strict(node):
            if isinstance(node, dict):
                node.pop('default', None)
                if node.get('type') == 'object':
                    node['additionalProperties'] = False
                    node['required'] = list(node.get('properties', {}))
                for value in list(node.values()): strict(value)
            elif isinstance(node, list):
                for value in node: strict(value)
            return node
        try:
            response = httpx.post('https://api.openai.com/v1/chat/completions',
                headers={'Authorization': 'Bearer '+os.environ['OPENAI_API_KEY']},
                json={'model': self.settings.generation_model,
                      'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}],
                      'response_format': {'type': 'json_schema', 'json_schema': {
                          'name': schema.__name__, 'strict': True, 'schema': strict(schema.model_json_schema())}}},
                timeout=120)
            response.raise_for_status()
            choice = response.json()['choices'][0]
            if choice['finish_reason'] != 'stop' or choice['message'].get('refusal'):
                raise ValueError('Incomplete or refused structured response')
            return schema.model_validate_json(choice['message']['content'])
        except Exception:
            raise RuntimeError('OpenAI generation failed. Check the server key, model access, quota and structured-output support.') from None


class GroqGenerator:
    def __init__(self,settings,max_retries=1):
        if not os.getenv('GROQ_API_KEY'):
            raise RuntimeError('The server owner must configure GROQ_API_KEY in hosting secrets; visitors do not supply keys.')
        from langchain_groq import ChatGroq
        self.model=ChatGroq(model=settings.generation_model,temperature=0,max_tokens=1024,
            timeout=60,max_retries=max_retries)

    def generate_json(self,system,prompt,schema):
        try:
            template=ChatPromptTemplate.from_messages([('system','{system}'),('human','{question}')])
            chain=template | self.model.with_structured_output(schema,method='json_mode')
            instructions=system+' Return only JSON matching this schema: '+json.dumps(schema.model_json_schema())
            result=chain.invoke({'system':instructions,'question':prompt})
            return result if isinstance(result,schema) else schema.model_validate(result)
        except Exception as error:
            # Keep request payloads and credentials out of the public UI.
            raise RuntimeError(hosted_error_message(error)) from error


def create_generator(settings,*,max_retries=1):
    if settings.generation_provider=='ollama':return OllamaGenerator(settings)
    if settings.generation_provider=='openai':return OpenAIGenerator(settings)
    if settings.generation_provider=='groq':return GroqGenerator(settings,max_retries=max_retries)
    raise ValueError('Unknown generation provider: '+settings.generation_provider)

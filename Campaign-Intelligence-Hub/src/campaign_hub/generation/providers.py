from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import os
import json


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


class GroqGenerator:
    def __init__(self,settings):
        if not os.getenv('GROQ_API_KEY'):
            raise RuntimeError('The server owner must configure GROQ_API_KEY in hosting secrets; visitors do not supply keys.')
        from langchain_groq import ChatGroq
        self.model=ChatGroq(model=settings.generation_model,temperature=0,max_tokens=1024,
            timeout=60,max_retries=1)

    def generate_json(self,system,prompt,schema):
        try:
            template=ChatPromptTemplate.from_messages([('system','{system}'),('human','{question}')])
            chain=template | self.model.with_structured_output(schema,method='json_mode')
            instructions=system+' Return only JSON matching this schema: '+json.dumps(schema.model_json_schema())
            result=chain.invoke({'system':instructions,'question':prompt})
            return result if isinstance(result,schema) else schema.model_validate(result)
        except Exception as error:
            # Keep request payloads and credentials out of the public UI.
            raise RuntimeError('Hosted generation failed. The server owner should check the configured model, API access and free-tier rate limits. Please retry later.') from error


def create_generator(settings):
    if settings.generation_provider=='ollama':return OllamaGenerator(settings)
    if settings.generation_provider=='groq':return GroqGenerator(settings)
    raise ValueError('Unknown generation provider: '+settings.generation_provider)

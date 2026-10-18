import json
import httpx


class OllamaGenerator:
    def __init__(self, settings):
        self.settings = settings

    def generate_json(self, system, prompt, schema):
        try:
            response = httpx.post(self.settings.ollama_url+'/api/chat', json={
                'model':self.settings.generation_model, 'stream':False, 'format':schema.model_json_schema(),
                'options':{'temperature':0, 'num_ctx':4096, 'num_predict':512},
                'messages':[{'role':'system','content':system},{'role':'user','content':prompt}]}, timeout=240)
            response.raise_for_status()
            return schema.model_validate_json(response.json()['message']['content'])
        except Exception as error:
            raise RuntimeError(f'Local generation failed. Check Ollama and model {self.settings.generation_model}: {error}') from error

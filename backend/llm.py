
import os

import google.generativeai as genai

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from look_and_feel import error, success, warning, info
from settings import settings

load_dotenv()

class EragAPI:
    def __init__(self, api_type, model=None, embedding_class=None, embedding_model=None, reranker_model=None):
        self.api_type = api_type
        self.model = model or settings.get_default_model(api_type)
        self.embedding_class = embedding_class or settings.get_default_embedding_class()
        self.embedding_model = embedding_model or settings.get_default_embedding_model(self.embedding_class)
        self.reranker_model = reranker_model or settings.reranker_model

        clients = {
            "groq": lambda: GroqClient(self.model),
            "gemini": lambda: GeminiClient(self.model)
        }
        if api_type not in clients:
            raise ValueError(f"Invalid API type: {api_type}")
        self.client = clients[api_type]()

        embedding_clients = {
            "sentence_transformers": lambda: SentenceTransformer(self.embedding_model)
        }
        if self.embedding_class not in embedding_clients:
            raise ValueError(f"Invalid embedding class: {self.embedding_class}")
        self.embedding_client = embedding_clients[self.embedding_class]()

    def _encode(self, texts):
        print(f"Starting embedding process for {len(texts)} texts")
        return self.embedding_client.encode(texts)

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            if self.api_type == "gemini":
                model = genai.GenerativeModel(self.model)
                formatted_messages = []
                for message in messages:
                    if message['role'] == 'system':
                        formatted_messages.append({"role": "user", "parts": [{"text": f"System: {message['content']}"}]})
                    elif message['role'] in ['user', 'assistant']:
                        formatted_messages.append({"role": message['role'], "parts": [{"text": message['content']}]})


                if not any(msg['role'] == 'user' for msg in formatted_messages):
                    formatted_messages.append({"role": "user", "parts": [{"text": " "}]})


                response = model.generate_content(
                    formatted_messages,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    ),
                    stream=stream
                )
                return response if stream else response.text

            return self.client.chat(messages, temperature=temperature, max_tokens=max_tokens, stream=stream)

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        try:
            return self.client.complete(prompt, temperature=temperature, max_tokens=max_tokens, stream=stream)
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def _stream_cohere_response(self, response):
        for event in response:
            if event.event_type == "text-generation":
                yield event.text

    
def update_settings(settings, api_type, model):
    setting_map = { "groq": "groq_model", "gemini": "gemini_model"}
    if api_type in setting_map:
        settings.update_setting(setting_map[api_type], model)
        settings.apply_settings()
        print(success(f"Settings updated. Using {model} with {api_type} backend."))
    else:
        print(error(f"Unknown API type: {api_type}"))
class GroqClient:
    def __init__(self, model=None):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY") or ValueError(error("GROQ_API_KEY not found in .env file")))
        self.model = model or self.get_default_model()

    def get_default_model(self):
        try:
            return self.client.models.list().data[0].id
        except Exception:
            return None

    def get_default_model(self):
        try:
            return self.client.models.list().data[0].id
        except Exception:
            return None

    def _request(self, method, **kwargs):
        try:
            return method(model=self.model, **kwargs)
        except Exception as e:
            raise Exception(error(f"Error from Groq API: {str(e)}"))

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        completion = self._request(
            self.client.chat.completions.create,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        return completion if stream else completion.choices[0].message.content

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        messages = [{"role": "user", "content": prompt}]
        completion = self._request(
            self.client.chat.completions.create,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        return completion if stream else completion.choices[0].message.content

    def stream_chat(self, messages, temperature=1, max_tokens=1024):
        for chunk in self._request(
            self.client.chat.completions.create,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        ):
            yield chunk.choices[0].delta.content or ""

class GeminiClient:
    def __init__(self, model=None):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY") or ValueError(error("GEMINI_API_KEY not found in .env file")))
        self.model = model or self.get_default_model()

    def get_default_model(self):
        try:
            return next((model.name for model in genai.list_models() if 'generateContent' in model.supported_generation_methods), None)
        except Exception:
            return None

    def _request(self, messages=None, prompt=None, temperature=0.7, max_tokens=None, stream=False):
        model = genai.GenerativeModel(self.model)
        config = genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)
        
        if messages:
            chat = model.start_chat(history=[])
            for message in messages:
                if message['role'] == 'user':
                    response = chat.send_message(message['content'], generation_config=config)
                    return self._stream_response(response) if stream else response.text
            return error("No user message found in the conversation.")
        
        response = model.generate_content(prompt, generation_config=config)
        return self._stream_response(response) if stream else response.text

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        return self._request(messages=messages, temperature=temperature, max_tokens=max_tokens, stream=stream)

    def complete(self, prompt, temperature=0.7, max_tokens=None, stream=False):
        return self._request(prompt=prompt, temperature=temperature, max_tokens=max_tokens, stream=stream)

    @staticmethod
    def _stream_response(response):
        for chunk in response:
            yield chunk.text


def create_erag_api(api_type, model=None, embedding_class=None, embedding_model=None, reranker_model=None):
    embedding_class = embedding_class or settings.get_default_embedding_class()
    embedding_model = embedding_model or settings.get_default_embedding_model(embedding_class)
    reranker_model = reranker_model or settings.reranker_model
    return EragAPI(api_type, model, embedding_class, embedding_model, reranker_model)



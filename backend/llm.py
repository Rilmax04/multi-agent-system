import os
import logging
from typing import List, Dict, Generator

from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq

from settings import settings

load_dotenv()
logger = logging.getLogger(__name__)


class EragAPI:
    _clients: Dict[str, object] = {}

    def __init__(self, api_type: str, model: str = None):
        self.api_type = api_type
        self.model = model or settings.get_default_model(api_type)
        cache_key = f"{api_type}:{self.model}"

        if cache_key not in EragAPI._clients:
            logger.info(f"Создание LLM-клиента: {cache_key}")
            if api_type == "groq":
                EragAPI._clients[cache_key] = GroqClient(self.model)
            elif api_type == "gemini":
                EragAPI._clients[cache_key] = GeminiClient(self.model)
            else:
                raise ValueError(f"Неизвестный тип API: '{api_type}'")

        self.client = EragAPI._clients[cache_key]

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        return self.client.chat(messages, temperature, max_tokens, stream)


class GroqClient:
    def __init__(self, model: str):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY отсутствует в .env")
        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info(f"GroqClient: {model}")

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
            if stream:
                return self._stream(completion)
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq ошибка: {e}")
            raise

    @staticmethod
    def _stream(completion) -> Generator[str, None, None]:
        for chunk in completion:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content


class GeminiClient:
    def __init__(self, model: str):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY отсутствует в .env")
        genai.configure(api_key=api_key)
        self.model = model
        logger.info(f"GeminiClient: {model}")

    def chat(self, messages, temperature=0.7, max_tokens=None, stream=False):
        try:
            model = genai.GenerativeModel(self.model)
            config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            history = []
            for msg in messages[:-1]:
                role = "user" if msg["role"] in ("user", "system") else "model"
                content = msg["content"]
                if msg["role"] == "system":
                    content = f"[Системная инструкция: {content}]"
                history.append({"role": role, "parts": [content]})

            chat = model.start_chat(history=history)
            last_message = messages[-1]["content"]
            response = chat.send_message(last_message, generation_config=config, stream=stream)

            if stream:
                return (chunk.text for chunk in response)
            return response.text
        except Exception as e:
            logger.error(f"Gemini ошибка: {e}")
            raise


def create_erag_api(api_type: str, model: str = None) -> EragAPI:
    return EragAPI(api_type, model)
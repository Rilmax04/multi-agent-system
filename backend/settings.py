import os
from typing import Optional, Dict

from dotenv import load_dotenv

load_dotenv()


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))

        self.agent_models: Dict[str, Dict[str, str]] = {
            "planner":  {"api": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
            "reasoner": {"api": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
            "fetcher":  {"api": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
        }

        self.temperature: float = 0.1
        self.max_tokens: Optional[int] = None

        self.api_request_timeout: int = 15
        self.api_max_retries: int = 3
        self.api_backoff_base: float = 1.0

        self.cache_ttl_prices: int = 120
        self.cache_ttl_historical: int = 300
        self.cache_ttl_top: int = 180

        self.max_context_length: int = 15000

        self.cors_origins = [
            "http://localhost:8501",
            "http://127.0.0.1:5500",
            "http://localhost:3000",
            "http://localhost:63342",
        ]

    def get_default_model(self, api_type: str) -> str:
        defaults = {
            "groq": "meta-llama/llama-4-scout-17b-16e-instruct",
            "gemini": "gemini-2.0-flash",
        }
        if api_type not in defaults:
            raise ValueError(f"Неизвестный тип API: {api_type}")
        return defaults[api_type]

    def get_agent_config(self, agent_name: str) -> Dict[str, str]:
        if agent_name not in self.agent_models:
            raise ValueError(f"Неизвестный агент: '{agent_name}'")
        return self.agent_models[agent_name]


settings = Settings()
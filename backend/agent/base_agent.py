from abc import ABC, abstractmethod
import logging

from llm import create_erag_api
from settings import settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        config = settings.get_agent_config(agent_name)
        self.llm = create_erag_api(
            api_type=config["api"],
            model=config["model"],
        )
        logger.info(f"[{self.__class__.__name__}] api={config['api']}, model={config['model']}")

    def _call_llm(self, prompt: str, temperature: float = None) -> str:
        temp = temperature if temperature is not None else settings.temperature
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
            )
            return response.strip() if isinstance(response, str) else response
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM ошибка: {e}")
            raise

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
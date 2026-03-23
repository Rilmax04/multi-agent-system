import json
import logging

from agent.base_agent import BaseAgent
from agent.contracts import FormattedContext

logger = logging.getLogger(__name__)


class RAGReasonerAgent(BaseAgent):
    def __init__(self):
        super().__init__("reasoner")

    def execute(self, user_query: str, context: FormattedContext) -> str:
        logger.info(f"[RAG] контекст: {context.total_chars} символов, усечён={context.was_truncated}")

        quality_note = ""
        if context.was_truncated:
            quality_note = "\n⚠️ Контекст был сокращён. Некоторые детали могут отсутствовать.\n"

        prompt = (
            "Ты — эксперт по криптовалютам.\n\n"
            "ПРАВИЛА:\n"
            "1. Используй ТОЛЬКО предоставленные данные\n"
            "2. Упоминай конкретные числа\n"
            "3. В конце дай краткий вывод\n"
            "4. Если данных недостаточно — скажи об этом\n"
            "5. Отвечай на языке запроса\n"
            f"{quality_note}\n"
            f"ДАННЫЕ:\n{context.context_str}\n\n"
            f"ВОПРОС: {user_query}\n\nОТВЕТ:"
        )

        try:
            response = self._call_llm(prompt, temperature=0.3)
            logger.info(f"[RAG] Ответ: {len(response)} символов")
            return response
        except Exception as e:
            logger.error(f"[RAG] Ошибка: {e}")
            return f"Ошибка генерации ответа: {e}"
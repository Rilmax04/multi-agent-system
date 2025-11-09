from llm import create_erag_api
import json


class RAGReasonerAgent:


    def __init__(self, llm_model="gemini"):
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")

    def generate_answer(self, user_query, context_data):
        """
        Формирует осмысленный ответ для пользователя на основе контекста.
        """
        # Преобразуем контекст в красивый JSON-текст
        context_str = json.dumps(context_data, ensure_ascii=False, indent=2)

        system_prompt = (
            "Ты — эксперт по криптовалютам и финансовым рынкам. "
            "Используй приведённые ниже данные (контекст), чтобы ответить на вопрос пользователя. "
            "Если данных недостаточно — сообщи об этом, не придумывай ответ. "
            "Если данные есть, но за более короткий период , то отвечай по нему "
            "Формулируй ответ ясно, аналитически и по делу, можно с коротким выводом в конце."
        )

        llm_prompt = (
            f"{system_prompt}\n\n"
            f"Контекстные данные:\n{context_str}\n\n"
            f"Вопрос пользователя:\n{user_query}\n\n"
            f"Ответ:"
        )

        try:
            response = self.llm.chat([{"role": "user", "content": llm_prompt}])
        except Exception as e:
            return f"Ошибка LLM при генерации ответа: {e}"

        print("\n=== Финальный ответ LLM ===")
        print(response)
        return response

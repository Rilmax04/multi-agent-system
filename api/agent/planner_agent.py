from api.llm import create_erag_api
import ast


class PlannerAgent:
    """
    Агент, который анализирует запрос пользователя и решает,
    какие функции нужно вызвать для получения крипто-данных.
    """

    def __init__(self, llm_model="gemini"):
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")

    def analyze_query(self, user_query: str):
        """
        Анализирует запрос пользователя и возвращает список функций без аргументов.
        """
        system_prompt = (
            "Ты агент, который определяет, какие функции нужно вызвать для сбора крипто-данных "
            "для ответа на запрос пользователя. "
            "Верни список функций без аргументов в виде Python списка. "
            "Допустимые функции: "
            "'coingecko_current_price', 'coingecko_historical_prices', "
            "'coingecko_top_coins', 'coinmarketcap_latest'. "
            "Пример ответа: ['coingecko_current_price', 'coingecko_historical_prices'] "
            "Возвращай только список функций, без лишнего текста."
        )

        llm_prompt = f"{system_prompt}\n\nПользовательский запрос: {user_query}"
        print(f"\n=== Анализ запроса ===\n{llm_prompt}\n")

        try:
            llm_response = self.llm.chat([{"role": "user", "content": llm_prompt}])
            print(f"Ответ LLM: {llm_response}")
        except Exception as e:
            print(f"Ошибка при вызове LLM: {e}")
            return []

        try:
            functions_to_call = ast.literal_eval(llm_response)
            if not isinstance(functions_to_call, list):
                raise ValueError("LLM вернула не список функций")
            return functions_to_call
        except Exception as e:
            print(f"Ошибка обработки ответа LLM: {e}")
            return []

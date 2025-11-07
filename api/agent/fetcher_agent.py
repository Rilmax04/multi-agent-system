from api.agent.crypto_api import (
    coingecko_current_price,
    coingecko_historical_prices,
    coingecko_top_coins,
    coinmarketcap_latest
)
from api.llm import create_erag_api
import json
import ast


class FetcherAgent:
    """
    Агент, который получает список функций от PlannerAgent
    и вызывает соответствующие API для сбора данных.
    """

    def __init__(self):
        self.data_store = {}
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")

    def fetch_data(self, functions_to_call):
        """
        Вызывает нужные API в зависимости от списка функций.
        """
        results = []
        for func_name in functions_to_call:
            try:
                if func_name == "coingecko_current_price":
                    data = coingecko_current_price("bitcoin,ethereum")
                    self.data_store["current_prices"] = data
                    self.data_store["source"] = "coingecko"
                    print("✅ Получены текущие цены")

                elif func_name == "coingecko_historical_prices":
                    data = {coin: coingecko_historical_prices(coin, days=7) for coin in ["bitcoin", "ethereum"]}
                    self.data_store["historical_prices"] = data
                    self.data_store["source"] = "coingecko"
                    print("✅ Получены исторические данные")

                elif func_name == "coingecko_top_coins":
                    data = coingecko_top_coins(limit=10)
                    self.data_store["top_coins"] = data
                    self.data_store["source"] = "coingecko"
                    print("✅ Получен топ монет CoinGecko")

                elif func_name == "coinmarketcap_latest":
                    data = coinmarketcap_latest(limit=10)
                    self.data_store["top_coins_cmc"] = data
                    self.data_store["source"] = "coinmarketcap"
                    print("✅ Получен топ монет CoinMarketCap")

                else:
                    print(f"⚠️ Неизвестная функция: {func_name}")
                    continue

                results.append({"function": func_name, "data": data})

            except Exception as e:
                print(f"❌ Ошибка при вызове {func_name}: {e}")

        self.data_store["rag_data"] = results
        return self.data_store

    def format_for_rag(self, user_query):
        """
        Отбирает только те данные, которые нужны для ответа пользователю.
        """
        all_data = []
        source = self.data_store.get("source", "unknown")

        for key, value in self.data_store.items():
            if key == "source":
                continue
            all_data.append({"type": key, "source": source, "data": value})

        system_prompt = (
            "Ты ассистент, который получает список крипто-данных и должен определить, "
            "какие из них нужны для ответа на вопрос пользователя. "
            "Верни список индексов элементов исходного списка, например: [0, 2]."
        )

        llm_prompt = f"{system_prompt}\n\nПользовательский запрос: {user_query}\n\nДанные: {json.dumps(all_data)}"

        try:
            llm_response = self.llm.chat([{"role": "user", "content": llm_prompt}])
        except Exception as e:
            print(f"Ошибка LLM при фильтрации: {e}")
            return all_data

        try:
            indices_to_keep = ast.literal_eval(llm_response)
            if not isinstance(indices_to_keep, list):
                raise ValueError("LLM вернула не список индексов")
        except Exception as e:
            print(f"Ошибка обработки LLM-ответа: {e}\nОтвет LLM: {llm_response}")
            return all_data

        filtered_data = [all_data[i] for i in indices_to_keep if i < len(all_data)]
        print("=== Отфильтрованные данные для RAG ===")
        print(json.dumps(filtered_data, indent=4, ensure_ascii=False))
        return filtered_data

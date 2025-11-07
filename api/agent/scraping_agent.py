from api.llm import create_erag_api
from api.crypto_api import (
    coingecko_current_price,
    coingecko_historical_prices,
    coingecko_top_coins,
    coinmarketcap_latest
)

class CryptoRAGAgentLLM:
    """
    Агент с использованием LLM для анализа запроса
    и вызова правильной функции для получения данных.
    """

    def __init__(self, llm_model="gemini"):
        # Создаем LLM-клиент
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")
        self.data_store = {}

    def handle_query(self, user_query: str):
   
    # Шаг 1: спросим LLM, какие функции вызвать
        system_prompt = (
        "Ты ассистент, который определяет, какие функции нужно вызвать для сбора крипто-данных "
        "для ответа на запрос пользователя. "
        "Верни список функций без аргументов в виде Python списка. "
        "Допустимые функции: "
        "'coingecko_current_price', 'coingecko_historical_prices', 'coingecko_top_coins', 'coinmarketcap_latest'. "
        "Пример ответа: ['coingecko_current_price', 'coingecko_historical_prices'] "
        "Возвращай только список функций, без лишнего текста."
        )

        llm_prompt = f"{system_prompt}\n\nПользовательский запрос: {user_query}"
        print(f"Запрос LLM:\n{llm_prompt}")

        try:
            llm_response = self.llm.chat([{"role": "user", "content": llm_prompt}])
            print (llm_response)
        except Exception as e:
            return f"LLM error: {str(e)}"

    # Шаг 2: безопасно преобразуем ответ LLM в список функций
        import ast
        try:
            functions_to_call = ast.literal_eval(llm_response)
        except Exception as e:
            return f"Ошибка обработки LLM-ответа: {e}\nОтвет LLM: {llm_response}"
        

        print (functions_to_call)
        import json

        results = []

        for func_name in functions_to_call:
            try:
                if func_name == "coingecko_current_price":
                    data = coingecko_current_price("bitcoin,ethereum")
                    self.data_store["current_prices"] = data
                    self.data_store["source"] = "coingecko"
                    print("=== Текущие цены ===")
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                
                elif func_name == "coingecko_historical_prices":
                    data = {coin: coingecko_historical_prices(coin, days=7) for coin in ["bitcoin", "ethereum"]}
                    self.data_store["historical_prices"] = data
                    self.data_store["source"] = "coingecko"
                    print("=== Исторические цены ===")
                    for coin, prices in data.items():
                        print(f"{coin}:")
                        print(json.dumps(prices, indent=4, ensure_ascii=False))
                
                elif func_name == "coingecko_top_coins":
                    data = coingecko_top_coins(limit=10)
                    self.data_store["top_coins"] = data
                    self.data_store["source"] = "coingecko"
                    print("=== Топ 10 монет CoinGecko ===")
                    for coin in data:
                        print(f"{coin['name']} ({coin['symbol']}): ${coin['current_price']}")
                
                elif func_name == "coinmarketcap_latest":
                    data = coinmarketcap_latest(limit=10)  # возвращает список монет
                    self.data_store["top_coins_cmc"] = data
                    self.data_store["source"] = "coinmarketcap"
                    print("=== Топ 10 монет CoinMarketCap ===")
                    for coin in data:  # здесь просто итерируем по списку
                        price = coin['quote']['USD']['price']
                        print(f"{coin['name']} ({coin['symbol']}): ${price:.2f}")
                
                else:
                    print(f"Неизвестная функция: {func_name}")
                    continue

                results.append({"function": func_name, "data": data})

            except Exception as e:
                print(f"Ошибка при вызове функции {func_name}: {e}")
            

    # Сохраняем для RAG
        self.data_store["rag_data"] = results

    # Шаг 3: форматируем для RAG
        return self.format_for_rag(user_query)

    def format_for_rag(self, user_query):
  
        import json
        import ast

        # 1. Сначала собираем все данные в общий список
        all_data = []
        source = self.data_store.get("source", "unknown")
        for key, value in self.data_store.items():
            if key == "source":
                continue
            all_data.append({
                "type": key,
                "source": source,
                "data": value
            })

        # 2. Подготавливаем запрос для LLM, чтобы отфильтровать данные
        system_prompt = (
            "Ты ассистент, который получает список крипто-данных и должен определить, "
            "какие элементы этого списка нужны для ответа на вопрос пользователя. "
            "Верни список индексов элементов исходного списка, которые нужно оставить. "
            "Возвращай только список индексов, например: [0, 2]."
        )
        llm_prompt = f"{system_prompt}\n\nПользовательский запрос: {user_query}\n\nДанные: {json.dumps(all_data)}"
        
        try:
            llm_response = self.llm.chat([{"role": "user", "content": llm_prompt}])
        except Exception as e:
            print(f"Ошибка LLM: {e}")
            return all_data  # если LLM упал, возвращаем всё

        # 3. Преобразуем ответ LLM в список индексов
        try:
            indices_to_keep = ast.literal_eval(llm_response)
            if not isinstance(indices_to_keep, list):
                raise ValueError("LLM вернула не список")
        except Exception as e:
            print(f"Ошибка обработки LLM-ответа: {e}\nОтвет LLM: {llm_response}")
            return all_data

        # 4. Фильтруем данные по указанным LLM индексам
        filtered_data = [all_data[i] for i in indices_to_keep if i < len(all_data)]
        print("=== Отфильтрованные данные для RAG ===")
        print(json.dumps(filtered_data, indent=4, ensure_ascii=False))
        return filtered_data

def main():
    # Создаем агента с LLM (Gemini, Groq или другой доступный)
    agent = CryptoRAGAgentLLM(llm_model="gemini")

    # Список тестовых запросов
    test_queries = [
        "Покажи текущие цены Bitcoin и Ethereum",
        "Покажи топ 5 монет CoinMarketCap",
        "Покажи исторические цены Bitcoin за последние 7 дней",
        "Покажи топ 10 монет по рыночной капитализации CoinGecko",
        "Сравни цены Bitcoin и Ethereum на прошлой неделе"
    ]

   
    result = agent.handle_query("Покажи текущие цены Bitcoin и Ethereum")
    print("Результат:")
    print(result)
       

if __name__ == "__main__":
    main()
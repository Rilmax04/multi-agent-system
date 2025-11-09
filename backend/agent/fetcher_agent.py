from agent.crypto_api import (
    coingecko_current_price,
    coingecko_historical_prices,
    coingecko_top_coins,
    coinmarketcap_latest
)
from llm import create_erag_api
import json
import ast


class FetcherAgent:

    def __init__(self):
        self.data_store = {}
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")

    def fetch_data(self, plan: dict,days):

        functions_to_call = plan.get("functions", [])
        coins_to_fetch = plan.get("coins", ["bitcoin"])

        results = []

        for func_name in functions_to_call:
            try:
                if func_name == "coingecko_current_price":
                    data = coingecko_current_price(",".join(coins_to_fetch))
                    self.data_store["current_prices"] = data
                    self.data_store["source"] = "coingecko"

                elif func_name == "coingecko_historical_prices":
                    data = {coin: coingecko_historical_prices(coin, days=days) for coin in coins_to_fetch}
                    self.data_store["historical_prices"] = data
                    self.data_store["source"] = "coingecko"

                elif func_name == "coingecko_top_coins":
                    data = coingecko_top_coins(limit=10)
                    self.data_store["top_coins"] = data
                    self.data_store["source"] = "coingecko"

                elif func_name == "coinmarketcap_latest":
                    data = coinmarketcap_latest(limit=10)
                    self.data_store["top_coins_cmc"] = data
                    self.data_store["source"] = "coinmarketcap"

                else:
                    continue

                results.append({"function": func_name, "data": data})

            except Exception as e:
                print(f"Ошибка при вызове {func_name}: {e}")

        self.data_store["rag_data"] = results
        return self.data_store
    
    def format_for_rag(self, user_query, selected_coins=None, period_days=7):

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

        if selected_coins:
            filtered_by_coin = []
            for entry in all_data:
                if isinstance(entry["data"], dict):
                    filtered = {
                        coin: data
                        for coin, data in entry["data"].items()
                        if coin in selected_coins
                    }
                    if filtered:
                        new_entry = entry.copy()
                        new_entry["data"] = filtered
                        filtered_by_coin.append(new_entry)
                else:
                    filtered_by_coin.append(entry)
            all_data = filtered_by_coin

        if all_data:
            print(json.dumps(all_data, indent=4, ensure_ascii=False))
            return all_data

        system_prompt = (
            "Ты аналитический ассистент, который должен определить, какие данные из предоставленного набора "
            "необходимы для ответа пользователю. "
            "У тебя есть исторические и текущие данные о криптовалютах с CoinGecko и CoinMarketCap. "
            "Ты должен выбрать только те данные, которые напрямую помогают ответить на запрос пользователя.\n\n"
            "Ты должен следовать Правила отбора:\n"
            "- Если запрос содержит слова вроде 'динамика', 'изменение', 'тренд', 'волатильность' — нужны исторические данные.\n"
            "- Если запрос связан с 'текущей ценой', 'рыночной капитализацией', 'лидерами' — нужны текущие данные.\n"
            "- Если пользователь спрашивает о сравнении монет — выбери данные именно для указанных монет.\n"
            "- Если упомянут период (например, 7 дней) — учитывай его при выборе исторических данных.\n"
            "- Если не ясно, какие данные выбрать — выбери и текущие, и исторические для всех запрошенных монет.\n\n"
            "Возвращай список индексов элементов исходного списка (например: [0, 2]), которые следует использовать."
        )

        llm_prompt = (
            f"{system_prompt}\n\n"
            f" Запрос пользователя: {user_query}\n"
            f" Запрошенные монеты: {selected_coins if selected_coins else 'не указаны'}\n"
            f" Предполагаемый период анализа: {period_days} дней\n\n"
            f" Доступные данные:\n{json.dumps(all_data, indent=4, ensure_ascii=False)}"
        )

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

        print(json.dumps(filtered_data, indent=4, ensure_ascii=False))
        return filtered_data

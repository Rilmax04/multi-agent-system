from llm import create_erag_api
import ast


class PlannerAgent:

    def __init__(self, llm_model="gemini"):
        self.llm = create_erag_api(api_type="gemini", model="gemini-2.5-flash")

    def analyze_query(self, user_query: str):

        system_prompt_functions = (
            "Ты агент, который определяет, какие функции нужно вызвать "
            "для сбора крипто-данных, чтобы ответить на запрос пользователя. "
            "Верни только Python список функций без аргументов. "
            "Допустимые функции: "
            "'coingecko_current_price', 'coingecko_historical_prices', "
            "'coingecko_top_coins', 'coinmarketcap_latest'.\n"
            "Пример ответа: ['coingecko_current_price', 'coingecko_historical_prices']\n"
            "Возвращай только список, без текста."
        )

        llm_prompt_functions = f"{system_prompt_functions}\n\nПользовательский запрос: {user_query}"

        try:
            llm_response_functions = self.llm.chat([{"role": "user", "content": llm_prompt_functions}])
            print(f"Ответ LLM (функции): {llm_response_functions}")
            functions_to_call = ast.literal_eval(llm_response_functions)
            if not isinstance(functions_to_call, list):
                raise ValueError("Ответ не является списком функций")
        except Exception as e:
            print(f"Ошибка при анализе функций: {e}")
            functions_to_call = []

        system_prompt_coins = (
            "Ты агент, который определяет, про какие криптовалюты нужно собрать данные "
            "на основе запроса пользователя. "
            "Верни список идентификаторов монет (CoinGecko IDs) в виде Python списка, например: ['bitcoin', 'ethereum'].\n"
            "Если конкретные монеты не указаны — верни ['bitcoin'].\n"
            "Возвращай только список, без лишнего текста.\n\n"
            "Список допустимых CoinGecko ID, которые можно использовать:\n"
            "['bitcoin', 'ethereum', 'tether', 'bnb', 'solana', 'ripple', 'dogecoin', 'cardano', 'tron', 'avalanche', "
            "'shiba-inu', 'polkadot', 'litecoin', 'chainlink', 'uniswap', 'stellar', 'monero', 'near', 'cosmos', "
            "'vechain', 'filecoin', 'aptos', 'hedera', 'maker', 'immutable', 'arbitrum', 'optimism', 'injective', "
            "'render-token', 'the-graph', 'quant-network', 'aave', 'algorand', 'elrond-erd-2', 'fantom', 'tezos', "
            "'theta-token', 'chiliz', 'flow', 'eos', 'neo', 'dash', 'kusama', 'iota', 'bitcoin-cash', 'internet-computer']\n\n"
            "Используй только эти ID — не выдумывай новые."
        )

        llm_prompt_coins = f"{system_prompt_coins}\n\nПользовательский запрос: {user_query}"

        try:
            llm_response_coins = self.llm.chat([{"role": "user", "content": llm_prompt_coins}])
            coins_to_fetch = ast.literal_eval(llm_response_coins)
            if not isinstance(coins_to_fetch, list):
                raise ValueError("Ответ не является списком монет")
        except Exception as e:
            print(f"Ошибка при анализе монет: {e}")
            coins_to_fetch = ["bitcoin"]
        plan = {"functions": functions_to_call, "coins": coins_to_fetch}
        return plan

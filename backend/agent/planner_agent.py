import json
import re
import logging
from typing import List

from agent.base_agent import BaseAgent
from agent.contracts import PlanResult, VALID_COINS, COIN_ALIASES, PERIOD_KEYWORDS, AllowedFunction

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner")

    def execute(self, user_query: str) -> PlanResult:
        logger.info(f"[Planner] Запрос: {user_query}")
        functions = self._determine_functions(user_query)
        coins = self._determine_coins(user_query)
        period = self._determine_period(user_query)

        try:
            plan = PlanResult(functions=functions, coins=coins,
                              period_days=period, original_query=user_query)
        except Exception as e:
            logger.warning(f"[Planner] Ошибка валидации: {e}, используем значения по умолчанию")
            plan = PlanResult(functions=["coingecko_current_price"],
                              coins=["bitcoin"], period_days=7, original_query=user_query)

        logger.info(f"[Planner] План: f={plan.functions}, c={plan.coins}, p={plan.period_days}д")
        return plan

    def _determine_functions(self, query: str) -> List[str]:
        allowed = [f.value for f in AllowedFunction]
        prompt = (
            f"Определи функции API для ответа на запрос.\n"
            f"ДОСТУПНЫЕ: {json.dumps(allowed)}\n"
            f"ПРАВИЛА:\n"
            f"- 'цена', 'стоит' → ['coingecko_current_price']\n"
            f"- 'динамика', 'история', 'тренд' → ['coingecko_historical_prices']\n"
            f"- 'топ', 'лидеры', 'рейтинг' → ['coingecko_top_coins']\n"
            f"- Верни ТОЛЬКО JSON-список\n\n"
            f"Запрос: {query}"
        )
        response = self._call_llm(prompt)
        functions = self._parse_list(response)
        valid = [f for f in functions if f in allowed]
        return valid or ["coingecko_current_price"]

    def _determine_coins(self, query: str) -> List[str]:
        query_lower = query.lower()
        found = set()
        for alias, coin_id in COIN_ALIASES.items():
            if alias in query_lower:
                found.add(coin_id)
        for coin in VALID_COINS:
            if coin in query_lower:
                found.add(coin)
        if found:
            return list(found)

        prompt = (
            f"Определи криптовалюты из запроса.\n"
            f"Допустимые: {json.dumps(VALID_COINS[:20])}...\n"
            f"Верни JSON-список. Если не ясно — [\"bitcoin\"].\n"
            f"Запрос: {query}"
        )
        try:
            response = self._call_llm(prompt)
            coins = self._parse_list(response)
            valid = [c for c in coins if c in VALID_COINS]
            return valid or ["bitcoin"]
        except Exception:
            return ["bitcoin"]

    def _determine_period(self, query: str) -> int:
        query_lower = query.lower()
        for kw, days in PERIOD_KEYWORDS.items():
            if kw in query_lower:
                return days
        match = re.search(r'(\d+)\s*(?:дн|день|дня)', query_lower)
        if match:
            d = int(match.group(1))
            if 0 < d <= 365: return d
        return 7

    @staticmethod
    def _parse_list(text: str) -> list:
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            s = match.group().replace("'", '"')
            try:
                r = json.loads(s)
                if isinstance(r, list):
                    return [str(i) for i in r]
            except json.JSONDecodeError:
                pass
        return []
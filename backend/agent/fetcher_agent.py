import logging
from typing import List

from agent.base_agent import BaseAgent
from agent.contracts import PlanResult, FetchedData, DataEntry
from agent.providers import ProviderManager, ProviderResponse, FetchStrategy

logger = logging.getLogger(__name__)

ROUTING = {
    "coingecko_current_price": {"method": "get_current_prices", "strategy": FetchStrategy.FALLBACK},
    "coinmarketcap_latest": {"method": "get_top_coins", "strategy": FetchStrategy.SPECIFIC, "provider": "coinmarketcap"},
    "coingecko_historical_prices": {"method": "get_historical_prices", "strategy": FetchStrategy.BEST_FOR},
    "coingecko_top_coins": {"method": "get_top_coins", "strategy": FetchStrategy.FALLBACK},
}


class FetcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("fetcher")
        self.provider = ProviderManager()

    def execute(self, plan: PlanResult) -> FetchedData:
        logger.info(f"[Fetcher] f={plan.functions}, c={plan.coins}, p={plan.period_days}д")
        entries, errors, source = [], [], "unknown"
        total, ok = len(plan.functions), 0

        for fn in plan.functions:
            route = ROUTING.get(fn)
            if not route:
                errors.append(f"Нет маршрута: {fn}")
                entries.append(DataEntry(function=fn, error=f"Нет маршрута: {fn}"))
                continue
            try:
                resp = self._dispatch(fn, route, plan)
                if not resp.success:
                    errors.append(f"{fn}: {resp.error}")
                    entries.append(DataEntry(function=fn, error=resp.error))
                    continue
                entries.append(DataEntry(function=fn, data=resp.data))
                ok += 1
                source = resp.source
                c = " (кеш)" if resp.cached else ""
                logger.info(f"[Fetcher] ✓ {fn} через {resp.source}{c} [{route['strategy'].value}]")
            except Exception as e:
                errors.append(f"{fn}: {e}")
                entries.append(DataEntry(function=fn, error=str(e)))

        return FetchedData(source=source, entries=entries, errors=errors,
                           completeness=ok / total if total else 0.0)

    def _dispatch(self, fn, route, plan) -> ProviderResponse:
        m, s, p = route["method"], route["strategy"], route.get("provider")

        if m == "get_current_prices":
            return self.provider.dispatch(m, s, preferred_provider=p, coin_ids=plan.coins)
        if m == "get_historical_prices":
            hist, last = {}, None
            for coin in plan.coins:
                r = self.provider.dispatch(m, s, preferred_provider=p,
                                           coin_id=coin, days=plan.period_days)
                if r.success:
                    hist[coin] = r.data
                    last = r
            if hist:
                return ProviderResponse(True, last.source if last else "unknown", hist)
            return ProviderResponse(False, "none", error="Нет исторических данных")
        if m == "get_top_coins":
            return self.provider.dispatch(m, s, preferred_provider=p, limit=10)
        return ProviderResponse(False, "none", error=f"Неизвестный метод: {m}")
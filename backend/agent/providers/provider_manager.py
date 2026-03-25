import logging
from typing import List, Optional

from agent.providers.base_provider import (
    CryptoDataProvider, ProviderResponse, ProviderStatus,
    DataCapability, FetchStrategy,
)
from agent.providers.coingecko_provider import CoinGeckoProvider
from agent.providers.coinmarketcap_provider import CoinMarketCapProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    def __init__(self, providers: Optional[List[CryptoDataProvider]] = None):
        self.providers = providers or [CoinGeckoProvider(), CoinMarketCapProvider()]
        self.providers.sort(key=lambda p: p.priority)
        self._by_name = {p.name: p for p in self.providers}
        logger.info(f"ProviderManager: {[p.name for p in self.providers]}")

    def dispatch(self, method_name, strategy, preferred_provider=None, **kwargs):
        logger.info(f"Диспетчер: {method_name}, стратегия={strategy.value}")

        if strategy == FetchStrategy.SPECIFIC:
            return self._specific(method_name, preferred_provider, **kwargs)
        if strategy == FetchStrategy.MERGE:
            return self._merge(method_name, **kwargs)
        if strategy == FetchStrategy.BEST_FOR:
            cap = self._method_to_cap(method_name)
            return self._fallback(method_name, required_cap=cap, **kwargs)
        return self._fallback(method_name, **kwargs)

    def _fallback(self, method_name, required_cap=None, **kwargs):
        last_error = None
        for p in self.providers:
            if required_cap and required_cap not in p.get_capabilities():
                continue
            status = p.get_status()
            if status in (ProviderStatus.UNAVAILABLE, ProviderStatus.NO_API_KEY):
                continue
            try:
                resp = getattr(p, method_name)(**kwargs)
                if resp.success:
                    logger.info(f"Fallback: {p.name} ✓")
                    return resp
                last_error = resp.error
            except Exception as e:
                last_error = str(e)
        return ProviderResponse(False, "none", error=f"Все провайдеры недоступны: {last_error}")

    def _specific(self, method_name, provider_name, **kwargs):
        p = self._by_name.get(provider_name)
        if not p:
            return ProviderResponse(False, provider_name or "unknown",
                                    error=f"Провайдер '{provider_name}' не найден")
        try:
            return getattr(p, method_name)(**kwargs)
        except Exception as e:
            return ProviderResponse(False, provider_name, error=str(e))

    def _merge(self, method_name, **kwargs):
        merged, sources = {}, []
        for p in self.providers:
            status = p.get_status()
            if status in (ProviderStatus.UNAVAILABLE, ProviderStatus.NO_API_KEY):
                continue
            try:
                resp = getattr(p, method_name)(**kwargs)
                if not resp.success: continue
                sources.append(p.name)
                if isinstance(resp.data, dict):
                    for cid, cd in resp.data.items():
                        if cid not in merged:
                            merged[cid] = cd
                        elif isinstance(cd, dict):
                            for f, v in cd.items():
                                if v is not None and merged[cid].get(f) is None:
                                    merged[cid][f] = v
            except Exception as e:
                logger.warning(f"Merge: {p.name} ошибка: {e}")
        if not merged:
            return ProviderResponse(False, "none", error="Нет данных")
        return ProviderResponse(True, "+".join(sources), merged)

    @staticmethod
    def _method_to_cap(method_name):
        return {"get_current_prices": DataCapability.CURRENT_PRICE,
                "get_historical_prices": DataCapability.HISTORICAL,
                "get_top_coins": DataCapability.TOP_COINS}.get(method_name)

    def get_all_statuses(self):
        return {p.name: {"status": p.get_status().value, "priority": p.priority,
                         "capabilities": [c.value for c in p.get_capabilities()]}
                for p in self.providers}
import os
import time
import hashlib
import logging
import requests
from typing import List, Set

from agent.providers.base_provider import (
    CryptoDataProvider, ProviderResponse, ProviderStatus, DataCapability,
)
from settings import settings

logger = logging.getLogger(__name__)
_cache = {}

CG_TO_CMC = {
    "bitcoin": "BTC", "ethereum": "ETH", "tether": "USDT",
    "bnb": "BNB", "solana": "SOL", "ripple": "XRP",
    "dogecoin": "DOGE", "cardano": "ADA", "tron": "TRX",
    "avalanche": "AVAX", "shiba-inu": "SHIB", "polkadot": "DOT",
    "litecoin": "LTC", "chainlink": "LINK", "uniswap": "UNI",
    "stellar": "XLM", "monero": "XMR", "near": "NEAR",
    "cosmos": "ATOM", "filecoin": "FIL", "aptos": "APT",
    "arbitrum": "ARB", "optimism": "OP", "aave": "AAVE",
    "algorand": "ALGO", "fantom": "FTM", "eos": "EOS",
    "bitcoin-cash": "BCH",
}
CMC_TO_CG = {v: k for k, v in CG_TO_CMC.items()}


def _get_cached(key, ttl):
    if key in _cache and time.time() - _cache[key]["time"] < ttl:
        return _cache[key]["data"]
    return None


def _set_cached(key, data):
    _cache[key] = {"data": data, "time": time.time()}


def _cache_key(prefix, *args):
    return hashlib.md5(f"{prefix}:{args}".encode()).hexdigest()


class CoinMarketCapProvider(CryptoDataProvider):
    BASE = "https://pro-api.coinmarketcap.com"

    def __init__(self):
        self.api_key = os.getenv("CMC_API_KEY")

    @property
    def name(self): return "coinmarketcap"

    @property
    def priority(self): return 2

    def get_capabilities(self) -> Set[DataCapability]:
        return {DataCapability.CURRENT_PRICE, DataCapability.TOP_COINS,
                DataCapability.CMC_RANK, DataCapability.GLOBAL_METRICS}

    def get_status(self) -> ProviderStatus:
        if not self.api_key: return ProviderStatus.NO_API_KEY
        try:
            r = requests.get(f"{self.BASE}/v1/key/info",
                             headers=self._headers(), timeout=5)
            if r.status_code == 200: return ProviderStatus.AVAILABLE
            if r.status_code == 429: return ProviderStatus.RATE_LIMITED
            return ProviderStatus.UNAVAILABLE
        except Exception:
            return ProviderStatus.UNAVAILABLE

    def _headers(self):
        return {"Accepts": "application/json", "X-CMC_PRO_API_KEY": self.api_key or ""}

    def _request(self, url, params=None):
        if not self.api_key: return {"_error": "CMC_API_KEY не настроен"}
        for attempt in range(settings.api_max_retries):
            try:
                r = requests.get(url, params=params, headers=self._headers(),
                                 timeout=settings.api_request_timeout)
                if r.status_code == 429:
                    time.sleep(settings.api_backoff_base * (2 ** attempt))
                    continue
                r.raise_for_status()
                return r.json()
            except Exception as e:
                if attempt == settings.api_max_retries - 1:
                    return {"_error": str(e)}
                time.sleep(settings.api_backoff_base * (2 ** attempt))
        return {"_error": "Превышено число попыток"}

    def get_current_prices(self, coin_ids, vs_currency="usd"):
        key = _cache_key("cmc_prices", ",".join(sorted(coin_ids)))
        cached = _get_cached(key, settings.cache_ttl_prices)
        if cached: return ProviderResponse(True, self.name, cached, cached=True)

        symbols, id_map = [], {}
        for cg_id in coin_ids:
            sym = CG_TO_CMC.get(cg_id, cg_id.upper())
            symbols.append(sym)
            id_map[sym] = cg_id

        raw = self._request(f"{self.BASE}/v1/cryptocurrency/quotes/latest",
                            {"symbol": ",".join(symbols), "convert": vs_currency.upper()})
        if "_error" in raw:
            return ProviderResponse(False, self.name, error=raw["_error"])
        if "data" not in raw:
            return ProviderResponse(False, self.name, error="Нет поля 'data'")

        curr = vs_currency.upper()
        result = {}
        for sym, cd in raw["data"].items():
            if isinstance(cd, list): cd = cd[0]
            q = cd.get("quote", {}).get(curr, {})
            cg_id = id_map.get(sym, sym.lower())
            result[cg_id] = {
                "price_usd": q.get("price", 0),
                "market_cap_usd": q.get("market_cap"),
                "volume_24h_usd": q.get("volume_24h"),
                "change_24h_percent": q.get("percent_change_24h"),
                "cmc_rank": cd.get("cmc_rank"),
                "circulating_supply": cd.get("circulating_supply"),
                "source": "coinmarketcap",
            }
        _set_cached(key, result)
        return ProviderResponse(True, self.name, result)

    def get_historical_prices(self, coin_id, vs_currency="usd", days=7):
        return ProviderResponse(False, self.name,
                                error="Исторические данные CMC только на платном тарифе")

    def get_top_coins(self, limit=10, vs_currency="usd"):
        key = _cache_key("cmc_top", limit, vs_currency)
        cached = _get_cached(key, settings.cache_ttl_top)
        if cached: return ProviderResponse(True, self.name, cached, cached=True)

        raw = self._request(f"{self.BASE}/v1/cryptocurrency/listings/latest",
                            {"start": "1", "limit": str(limit), "convert": vs_currency.upper()})
        if "_error" in raw:
            return ProviderResponse(False, self.name, error=raw["_error"])
        if "data" not in raw:
            return ProviderResponse(False, self.name, error="Нет поля 'data'")

        curr = vs_currency.upper()
        result = []
        for c in raw["data"]:
            q = c.get("quote", {}).get(curr, {})
            sym = c.get("symbol", "")
            result.append({
                "rank": c.get("cmc_rank", 0),
                "coin_id": CMC_TO_CG.get(sym, sym.lower()),
                "symbol": sym, "name": c.get("name", ""),
                "price_usd": q.get("price", 0),
                "market_cap_usd": q.get("market_cap", 0),
                "volume_24h_usd": q.get("volume_24h", 0),
                "change_24h_percent": q.get("percent_change_24h"),
                "cmc_rank": c.get("cmc_rank"),
                "source": "coinmarketcap",
            })
        _set_cached(key, result)
        return ProviderResponse(True, self.name, result)
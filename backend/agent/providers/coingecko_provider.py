import os
import time
import hashlib
import logging
import requests
from typing import List, Set

from agent.providers.base_provider import (
    CryptoDataProvider,
    ProviderResponse,
    ProviderStatus,
    DataCapability,
)
from settings import settings

logger = logging.getLogger(__name__)
_cache = {}


def _get_cached(key, ttl):
    if key in _cache and time.time() - _cache[key]["time"] < ttl:
        return _cache[key]["data"]
    return None


def _set_cached(key, data):
    _cache[key] = {"data": data, "time": time.time()}


def _cache_key(prefix, *args):
    return hashlib.md5(f"{prefix}:{args}".encode()).hexdigest()


class CoinGeckoProvider(CryptoDataProvider):
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")

        # Для demo-ключа используется обычный api.coingecko.com
        self.BASE = "https://api.coingecko.com/api/v3"

        if self.api_key:
            logger.info("CoinGecko: demo-режим (с demo API-ключом)")
        else:
            logger.info("CoinGecko: бесплатный режим (без ключа)")

    def _headers(self):
        """
        Заголовки для CoinGecko.
        Для demo-ключа нужен x-cg-demo-api-key.
        """
        if self.api_key:
            return {"x-cg-demo-api-key": self.api_key}
        return {}

    def _request(self, url, params=None):
        """
        HTTP GET с retry, backoff и подробным логированием ошибок.
        """
        for attempt in range(settings.api_max_retries):
            try:
                resp = requests.get(
                    url,
                    params=params,
                    headers=self._headers(),
                    timeout=settings.api_request_timeout,
                )

                if resp.status_code == 429:
                    wait = settings.api_backoff_base * (2 ** attempt)
                    logger.warning(
                        f"CoinGecko 429 Too Many Requests. "
                        f"Body: {resp.text}. Ожидание {wait:.1f}с"
                    )
                    time.sleep(wait)
                    continue

                if resp.status_code >= 400:
                    logger.error(
                        f"CoinGecko HTTP {resp.status_code}. "
                        f"URL={url}, params={params}, body={resp.text}"
                    )
                    return {"_error": f"HTTP {resp.status_code}: {resp.text}"}

                return resp.json()

            except requests.exceptions.Timeout:
                logger.warning(
                    f"CoinGecko таймаут ({attempt + 1}/{settings.api_max_retries})"
                )
            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    f"CoinGecko ошибка соединения "
                    f"({attempt + 1}/{settings.api_max_retries}): {e}"
                )
            except Exception as e:
                logger.error(f"CoinGecko unexpected error: {e}")
                return {"_error": str(e)}

            if attempt < settings.api_max_retries - 1:
                time.sleep(settings.api_backoff_base * (2 ** attempt))

        return {"_error": f"Превышено число попыток ({settings.api_max_retries})"}

    @property
    def name(self):
        return "coingecko"

    @property
    def priority(self):
        return 1

    def get_capabilities(self) -> Set[DataCapability]:
        return {
            DataCapability.CURRENT_PRICE,
            DataCapability.HISTORICAL,
            DataCapability.TOP_COINS,
            DataCapability.GLOBAL_METRICS,
        }

    def get_status(self) -> ProviderStatus:
        try:
            r = requests.get(
                f"{self.BASE}/ping",
                headers=self._headers(),
                timeout=5,
            )

            if r.status_code == 200:
                return ProviderStatus.AVAILABLE
            if r.status_code == 429:
                logger.warning(f"CoinGecko rate limited: {r.text}")
                return ProviderStatus.RATE_LIMITED

            logger.error(
                f"CoinGecko unavailable: {r.status_code}, body={r.text}"
            )
            return ProviderStatus.UNAVAILABLE

        except Exception as e:
            logger.error(f"CoinGecko status check failed: {e}")
            return ProviderStatus.UNAVAILABLE

    def get_current_prices(self, coin_ids, vs_currency="usd"):
        key = _cache_key("cg_prices", ",".join(sorted(coin_ids)), vs_currency)
        cached = _get_cached(key, settings.cache_ttl_prices)
        if cached:
            return ProviderResponse(True, self.name, cached, cached=True)

        raw = self._request(
            f"{self.BASE}/simple/price",
            {
                "ids": ",".join(coin_ids),
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            },
        )

        if "_error" in raw:
            return ProviderResponse(False, self.name, error=raw["_error"])

        result = {}
        for cid in coin_ids:
            if cid in raw:
                d = raw[cid]
                result[cid] = {
                    "price_usd": d.get(vs_currency, 0),
                    "market_cap_usd": d.get(f"{vs_currency}_market_cap"),
                    "volume_24h_usd": d.get(f"{vs_currency}_24h_vol"),
                    "change_24h_percent": d.get(f"{vs_currency}_24h_change"),
                    "source": "coingecko",
                }

        _set_cached(key, result)
        return ProviderResponse(True, self.name, result)

    def get_historical_prices(self, coin_id, vs_currency="usd", days=7):
        key = _cache_key("cg_hist", coin_id, vs_currency, days)
        cached = _get_cached(key, settings.cache_ttl_historical)
        if cached:
            return ProviderResponse(True, self.name, cached, cached=True)

        raw = self._request(
            f"{self.BASE}/coins/{coin_id}/market_chart",
            {
                "vs_currency": vs_currency,
                "days": days,
                "interval": "daily" if days > 1 else "hourly",
            },
        )

        if "_error" in raw:
            return ProviderResponse(False, self.name, error=raw["_error"])
        if "prices" not in raw:
            return ProviderResponse(False, self.name, error="Нет поля 'prices'")

        prices = [{"timestamp": int(ts), "price": float(p)} for ts, p in raw["prices"]]
        result = {
            "coin_id": coin_id,
            "period_days": days,
            "prices": prices,
            "source": "coingecko",
        }

        if len(prices) >= 2 and prices[0]["price"] != 0:
            result["change_percent"] = round(
                (prices[-1]["price"] - prices[0]["price"]) / prices[0]["price"] * 100,
                2,
            )

        _set_cached(key, result)
        return ProviderResponse(True, self.name, result)

    def get_top_coins(self, limit=10, vs_currency="usd"):
        key = _cache_key("cg_top", limit, vs_currency)
        cached = _get_cached(key, settings.cache_ttl_top)
        if cached:
            return ProviderResponse(True, self.name, cached, cached=True)

        raw = self._request(
            f"{self.BASE}/coins/markets",
            {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
            },
        )

        if isinstance(raw, dict) and "_error" in raw:
            return ProviderResponse(False, self.name, error=raw["_error"])
        if not isinstance(raw, list):
            return ProviderResponse(False, self.name, error="Ожидался список")

        result = [
            {
                "rank": c.get("market_cap_rank", 0),
                "coin_id": c.get("id", ""),
                "symbol": c.get("symbol", "").upper(),
                "name": c.get("name", ""),
                "price_usd": c.get("current_price", 0),
                "market_cap_usd": c.get("market_cap", 0),
                "volume_24h_usd": c.get("total_volume", 0),
                "change_24h_percent": c.get("price_change_percentage_24h"),
                "source": "coingecko",
            }
            for c in raw
        ]

        _set_cached(key, result)
        return ProviderResponse(True, self.name, result)
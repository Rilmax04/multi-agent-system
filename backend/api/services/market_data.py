from typing import List, Optional
import api.app as app_module
from agent.providers.base_provider import FetchStrategy


def _get_provider():
    p = app_module.provider
    if p is None: raise RuntimeError("ProviderManager не инициализирован")
    return p


def get_prices(coins: List[str], source: Optional[str] = None):
    p = _get_provider()
    if source:
        resp = p.dispatch("get_current_prices", FetchStrategy.SPECIFIC,
                          preferred_provider=source, coin_ids=coins)
    else:
        resp = p.dispatch("get_current_prices", FetchStrategy.FALLBACK, coin_ids=coins)
    if not resp.success: return None
    result = {}
    for cid, data in resp.data.items():
        result[cid] = {"coin_id": cid, "price_usd": data.get("price_usd", 0),
                        "market_cap_usd": data.get("market_cap_usd"),
                        "volume_24h_usd": data.get("volume_24h_usd"),
                        "change_24h_percent": data.get("change_24h_percent"),
                        "source": data.get("source", resp.source)}
    return result


def get_history(coin_id: str, days: int):
    p = _get_provider()
    resp = p.dispatch("get_historical_prices", FetchStrategy.BEST_FOR,
                      coin_id=coin_id, days=days)
    if not resp.success: return None
    d = resp.data
    return {"coin_id": d.get("coin_id", coin_id), "period_days": d.get("period_days", days),
            "prices": [{"timestamp": pt["timestamp"], "price": pt["price"]}
                       for pt in d.get("prices", [])],
            "change_percent": d.get("change_percent"),
            "source": d.get("source", resp.source)}


def get_top(limit: int, source: Optional[str] = None):
    p = _get_provider()
    if source:
        resp = p.dispatch("get_top_coins", FetchStrategy.SPECIFIC,
                          preferred_provider=source, limit=limit)
    else:
        resp = p.dispatch("get_top_coins", FetchStrategy.FALLBACK, limit=limit)
    if not resp.success: return None
    return [{"rank": c.get("rank", 0), "coin_id": c.get("coin_id", ""),
             "symbol": c.get("symbol", ""), "name": c.get("name", ""),
             "price_usd": c.get("price_usd", 0), "market_cap_usd": c.get("market_cap_usd", 0),
             "change_24h_percent": c.get("change_24h_percent"),
             "source": c.get("source", resp.source)} for c in resp.data]


def get_comparison(coins: List[str], period_days: int):
    p = _get_provider()
    prices_resp = p.dispatch("get_current_prices", FetchStrategy.MERGE, coin_ids=coins)
    comparison = {}
    for cid in coins:
        cd = {"coin_id": cid}
        if prices_resp.success and cid in prices_resp.data:
            d = prices_resp.data[cid]
            cd.update({"price_usd": d.get("price_usd"), "market_cap_usd": d.get("market_cap_usd"),
                        "change_24h_percent": d.get("change_24h_percent")})
        hr = p.dispatch("get_historical_prices", FetchStrategy.BEST_FOR,
                        coin_id=cid, days=period_days)
        if hr.success:
            cd["change_period_percent"] = hr.data.get("change_percent")
        comparison[cid] = cd
    return {"coins": comparison, "period_days": period_days,
            "sources": prices_resp.source if prices_resp.success else "none"}


def get_provider_statuses():
    try:
        return _get_provider().get_all_statuses()
    except Exception:
        return {}

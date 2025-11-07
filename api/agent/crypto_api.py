import requests
import os

CMC_API_KEY = os.getenv("CMC_API_KEY")

# ----------------------------
# CoinGecko functions
# ----------------------------

def coingecko_current_price(coin_ids="bitcoin,ethereum", vs_currency="usd"):
    """Текущие цены, капитализация, объем и изменение за 24 часа."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_ids,
        "vs_currencies": vs_currency,
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true"
    }
    response = requests.get(url, params=params)
    try:
        data = response.json()
        if not isinstance(data, dict):
            return {"error": f"Unexpected response: {data}"}
        return data
    except Exception as e:
        return {"error": str(e)}


def coingecko_historical_prices(coin_id="bitcoin", vs_currency="usd", days=7, interval="daily"):
    """Исторические цены и объемы."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": interval
    }
    response = requests.get(url, params=params)
    try:
        data = response.json()
        if not isinstance(data, dict):
            return {"error": f"Unexpected response: {data}"}
        return data
    except Exception as e:
        return {"error": str(e)}


def coingecko_top_coins(limit=50, vs_currency="usd"):
    """Топ монет по капитализации и изменение за 24 часа."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h"
    }
    response = requests.get(url, params=params)
    try:
        data = response.json()
        if not isinstance(data, list):
            return {"error": f"Unexpected response: {data}"}
        return data
    except Exception as e:
        return {"error": str(e)}


# ----------------------------
# CoinMarketCap functions
# ----------------------------

def coinmarketcap_latest(limit=10, convert="USD"):
    """Топ монет по капитализации и текущей цене."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }
    params = {
        "start": "1",
        "limit": str(limit),
        "convert": convert
    }
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if "data" not in data:
            return {"error": f"Unexpected response: {data}"}
        return data["data"]
    except Exception as e:
        return {"error": str(e)}


def coinmarketcap_historical(symbols="BTC,ETH", time_start="2025-10-31T00:00:00", time_end="2025-11-07T00:00:00", interval="daily"):
    """Исторические котировки через CoinMarketCap API (Pro)."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }
    params = {
        "symbol": symbols,
        "time_start": time_start,
        "time_end": time_end,
        "interval": interval
    }
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if "data" not in data:
            return {"error": f"Unexpected response: {data}"}
        return data["data"]
    except Exception as e:
        return {"error": str(e)}

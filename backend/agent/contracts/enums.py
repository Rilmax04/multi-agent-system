from enum import Enum


class AllowedFunction(str, Enum):
    COINGECKO_CURRENT_PRICE = "coingecko_current_price"
    COINGECKO_HISTORICAL = "coingecko_historical_prices"
    COINGECKO_TOP_COINS = "coingecko_top_coins"
    COINMARKETCAP_LATEST = "coinmarketcap_latest"


class AgentStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
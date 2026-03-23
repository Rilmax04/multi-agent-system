from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set, Any
from enum import Enum


class FetchStrategy(Enum):
    FALLBACK = "fallback"
    SPECIFIC = "specific"
    BEST_FOR = "best_for"
    MERGE = "merge"


class DataCapability(Enum):
    CURRENT_PRICE = "current_price"
    HISTORICAL = "historical"
    TOP_COINS = "top_coins"
    CMC_RANK = "cmc_rank"
    GLOBAL_METRICS = "global_metrics"


class ProviderStatus(Enum):
    AVAILABLE = "available"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    NO_API_KEY = "no_api_key"


@dataclass
class ProviderResponse:
    success: bool
    source: str
    data: Any = None
    error: Optional[str] = None
    cached: bool = False


class CryptoDataProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        pass

    @abstractmethod
    def get_capabilities(self) -> Set[DataCapability]:
        pass

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        pass

    @abstractmethod
    def get_current_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> ProviderResponse:
        pass

    @abstractmethod
    def get_historical_prices(self, coin_id: str, vs_currency: str = "usd", days: int = 7) -> ProviderResponse:
        pass

    @abstractmethod
    def get_top_coins(self, limit: int = 10, vs_currency: str = "usd") -> ProviderResponse:
        pass
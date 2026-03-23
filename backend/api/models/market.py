from pydantic import BaseModel, Field
from typing import Optional, List


class CoinPriceResponse(BaseModel):
    coin_id: str
    price_usd: float
    market_cap_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    change_24h_percent: Optional[float] = None
    source: Optional[str] = None


class HistoricalPricePoint(BaseModel):
    timestamp: int
    price: float


class HistoricalResponse(BaseModel):
    coin_id: str
    period_days: int
    prices: List[HistoricalPricePoint]
    change_percent: Optional[float] = None
    source: Optional[str] = None


class TopCoinResponse(BaseModel):
    rank: int
    coin_id: str
    symbol: str
    name: str
    price_usd: float
    market_cap_usd: float
    change_24h_percent: Optional[float] = None
    source: Optional[str] = None


class CompareRequest(BaseModel):
    coins: List[str] = Field(..., min_length=2, max_length=10)
    period_days: int = Field(default=7, ge=1, le=365)
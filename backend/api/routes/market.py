import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Query
from api.models.market import (CoinPriceResponse, HistoricalResponse,
                                HistoricalPricePoint, TopCoinResponse, CompareRequest)
from api.services.market_data import get_prices, get_history, get_top, get_comparison

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/prices", response_model=Dict[str, CoinPriceResponse])
async def market_prices(coins: str = Query("bitcoin,ethereum"), source: Optional[str] = Query(None)):
    coin_list = [c.strip() for c in coins.split(",") if c.strip()]
    if not coin_list: raise HTTPException(400, "Не указаны монеты")
    result = get_prices(coin_list, source)
    if result is None: raise HTTPException(502, "Провайдеры недоступны")
    return result


@router.get("/history/{coin_id}", response_model=HistoricalResponse)
async def market_history(coin_id: str, days: int = Query(7, ge=1, le=365)):
    result = get_history(coin_id, days)
    if result is None: raise HTTPException(502, "Не удалось получить данные")
    return result


@router.get("/top", response_model=List[TopCoinResponse])
async def market_top(limit: int = Query(10, ge=1, le=100), source: Optional[str] = Query(None)):
    result = get_top(limit, source)
    if result is None: raise HTTPException(502, "Провайдеры недоступны")
    return result


@router.post("/compare")
async def market_compare(request: CompareRequest):
    return get_comparison(request.coins, request.period_days)
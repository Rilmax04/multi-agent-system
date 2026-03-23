import logging
import traceback
from fastapi import APIRouter, HTTPException
from api.models.ask import AskRequest, AskResponse
from api.services.analysis import get_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        result = get_analysis(request.question)
        return AskResponse(answer=result["answer"],
                           total_time_ms=result.get("total_time_ms"),
                           trace=result.get("trace"))
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, detail=str(e))
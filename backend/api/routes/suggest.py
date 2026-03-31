import logging
import traceback

from fastapi import APIRouter, HTTPException

from api.models.suggest import SuggestRequest, SuggestResponse
from api.services.suggestions import get_followup_suggestions

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SuggestResponse)
async def suggest_followups(request: SuggestRequest):
    try:
        suggestions = get_followup_suggestions(request.past_questions)
        return SuggestResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, detail=str(e))

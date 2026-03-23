from pydantic import BaseModel, Field
from typing import Optional, List


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    status: str = "ok"
    total_time_ms: Optional[float] = None
    trace: Optional[List[dict]] = None
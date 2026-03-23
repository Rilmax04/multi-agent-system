from pydantic import BaseModel
from typing import Dict, Any, Optional


class HealthResponse(BaseModel):
    status: str
    controller_ready: bool
    providers: Optional[Dict[str, Any]] = None
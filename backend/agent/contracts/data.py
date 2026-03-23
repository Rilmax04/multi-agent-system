from pydantic import BaseModel, Field
from typing import List, Any, Optional


class DataEntry(BaseModel):
    function: str
    data: Any = None
    error: Optional[str] = None


class FetchedData(BaseModel):
    source: str = "unknown"
    entries: List[DataEntry] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)
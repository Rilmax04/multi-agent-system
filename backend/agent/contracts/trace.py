from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from agent.contracts.enums import AgentStatus


class StepTrace(BaseModel):
    step: str
    status: AgentStatus = AgentStatus.SUCCESS
    time_ms: float = 0
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PipelineTrace(BaseModel):
    steps: List[StepTrace] = Field(default_factory=list)
    total_time_ms: float = 0
from pydantic import BaseModel, Field, field_validator
from typing import List
from agent.contracts.enums import AllowedFunction
from agent.contracts.constants import VALID_COINS


class PlanResult(BaseModel):
    functions: List[str] = Field(..., min_length=1)
    coins: List[str] = Field(default=["bitcoin"], min_length=1)
    period_days: int = Field(default=7, gt=0, le=365)
    original_query: str = Field(default="")

    @field_validator("functions")
    @classmethod
    def validate_functions(cls, v):
        allowed = {f.value for f in AllowedFunction}
        invalid = [f for f in v if f not in allowed]
        if invalid:
            raise ValueError(f"Неизвестные функции: {invalid}")
        return v

    @field_validator("coins")
    @classmethod
    def validate_coins(cls, v):
        invalid = [c for c in v if c not in VALID_COINS]
        if invalid:
            raise ValueError(f"Неизвестные монеты: {invalid}")
        return v
from typing import List

from pydantic import BaseModel, Field, field_validator


class SuggestRequest(BaseModel):
    past_questions: List[str] = Field(default_factory=list, max_length=25)

    @field_validator("past_questions")
    @classmethod
    def normalize_questions(cls, v: List[str]) -> List[str]:
        out: List[str] = []
        for q in v:
            s = (q or "").strip()[:500]
            if s:
                out.append(s)
        return out[:25]


class SuggestResponse(BaseModel):
    suggestions: List[str] = Field(..., min_length=3, max_length=3)

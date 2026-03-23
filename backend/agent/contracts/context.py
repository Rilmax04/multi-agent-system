from pydantic import BaseModel, Field


class FormattedContext(BaseModel):
    context_str: str
    total_chars: int = 0
    was_truncated: bool = False
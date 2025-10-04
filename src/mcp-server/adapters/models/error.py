from pydantic import BaseModel, Field
from typing import Any, Dict

class ErrorResponse(BaseModel):
    """Ошибка исполнения запроса/функции."""
    status_code: int = Field(description="Код ошибки")
    error: str = Field(description="Описание ошибки")
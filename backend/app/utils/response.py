from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[list[str]] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success") -> "ApiResponse":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, errors: Optional[list[str]] = None) -> "ApiResponse":
        return cls(success=False, message=message, errors=errors)

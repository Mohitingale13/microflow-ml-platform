from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    environment: str
    timestamp: datetime

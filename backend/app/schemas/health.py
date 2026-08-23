from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall backend application status")
    database: str = Field(default="connected", description="Database connection status")
    version: Optional[str] = Field(default="1.0.0", description="Application version")
    app_name: Optional[str] = Field(default=None, description="Application name")

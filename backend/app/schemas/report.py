from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inspection_id: int
    report_path: str
    report_type: str = "PDF"
    generated_at: datetime

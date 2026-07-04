from typing import Any

from pydantic import BaseModel, ConfigDict


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_filename: str
    status: str
    total_rows: int
    processed_rows: int
    imported_count: int
    skipped_count: int
    duplicate_count: int
    error_count: int
    errors: Any | None = None
    created_at: str
    completed_at: str | None = None

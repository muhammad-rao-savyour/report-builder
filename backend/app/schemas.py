from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemIn(BaseModel):
    name: str
    description: str = ""


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    created_at: datetime


class UploadStartIn(BaseModel):
    filename: str


class UploadStartOut(BaseModel):
    upload_id: str
    upload_url: str  # the browser PUTs the file straight here


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    status: str
    row_count: int
    processed_rows: int
    error: str

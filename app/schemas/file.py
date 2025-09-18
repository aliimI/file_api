from pydantic import  BaseModel, Field
from datetime import datetime
from pydantic.config import ConfigDict


class FinalizeRequest(BaseModel):
    key: str
    filename: str
    content_type: str | None = None


class FileResponse(BaseModel):
    id: int
    key: str = Field(serialization_alias="key", alias="storage_key")
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    etag: str | None = None
    thumbnail_url: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class PresignUpload(BaseModel):
    upload_url: str
    key: str

class DownloadURL(BaseModel):
    url: str

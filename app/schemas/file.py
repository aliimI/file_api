from pydantic import  BaseModel
from datetime import datetime



class FileResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class PresignUpload(BaseModel):
    upload_url: str
    key: str

class DownloadURL(BaseModel):
    url: str

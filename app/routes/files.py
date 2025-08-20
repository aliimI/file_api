from uuid import uuid4
from fastapi import APIRouter, Depends

from app.core.roles import require_role
from app.schemas.file import FileResponse, PresignUpload, DownloadURL
from app.storage.s3 import S3Storage


router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

s3 = S3Storage()

# -------------Upload files -----------------

@router.post("/presign-upload", response_model=PresignUpload)
async def presign_upload(
    filename: str,
    content_type: str | None = None,
    user = Depends(require_role("viewer")),

):
    # for namespacing
    key = f"{user.id}/{uuid4().hex}-{filename}"
    url = s3.presigned_put(key=key, content_type=content_type or "application/octet-stream")
    return {"upload_url": url, "key": key}
    





@router.get("/admin/all", response_model=list[FileResponse])
async def admin_list_all(
   
):
    pass

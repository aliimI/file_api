from uuid import uuid4
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.rbac import require_role
from app.database import get_async_session
from app.core.deps import get_current_user
from app.schemas.file import FileResponse, PresignUpload, DownloadURL
from app.storage.s3 import S3Storage
from app.models.file import File
from app.core.deps_file import get_file_or_404


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

@router.post("/finalize", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def finalize_upload(
    key: str, 
    filename: str,
    content_type: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    user = Depends(require_role("viewer")),
):
    try:
        head = s3.head(key=key)
    except Exception:
        raise HTTPException(status_code=400, detail="Object not found in S3")
    
    size = int(head.get("ContentLength", 0))
    ctype = content_type or head.get("ContentType") or "application/octet-stream"

    new = File(
        owner_id=user.id,
        filename=filename,
        content_type=ctype,
        size=size,
        storage_key=key,
    )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new
    

#-----------List my files-----------------

@router.get("/me", response_model=list[FileResponse])
async def my_ffiles(
    session: AsyncSession = Depends(get_async_session),
    user = Depends(require_role("viewer")),
):
    query = await session.execute(select(File).where(File.owner_id == user.id).order_by(File.uploaded_at.desc()))
    return query.scalars().all()


#-----------Donwload url------------------

@router.get("/download-url/{file_id}", response_model=DownloadURL)
async def download_url(
    db_file: File = Depends(get_file_or_404)
):
    try:
        url = s3.presigned_get(key=db_file.storage_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create download URL")
    
    return DownloadURL(url=url)

#-----------Delete-------------

@router.delete("/{file_id}", status_code=204)
async def delete_file(
    db_file: File = Depends(get_file_or_404),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        s3.delete(key=db_file.storage_key)
    except Exception:
        pass
    
    await session.delete(db_file)
    await session.commit()
    

#-----------Admin utilities--------------------

@router.get("/admin/all", response_model=list[FileResponse])
async def admin_list_all(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    user = Depends(require_role("admin")),
   
):
    query = await session.execute(
        select(File).order_by(File.uploaded_at.desc()).limit(limit).offset(offset)
    )
    return query.scalars().all()

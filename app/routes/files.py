from uuid import uuid4
from fastapi import APIRouter, Depends, status, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.rbac import require_role
from app.database import get_async_session
from app.schemas.file import FileResponse, PresignUpload, DownloadURL, FinalizeRequest
from app.storage.s3 import S3Storage
from app.models.file import File
from app.core.deps_file import get_file_or_404
from app.tasks.thumbnails import resize_image
from botocore.exceptions import ClientError


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
    print(f"Key before finalize: {key}")
    return {"upload_url": url, "key": key}

@router.post("/finalize", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def finalize_upload(
    payload: FinalizeRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    user = Depends(require_role("viewer")),
):
    key = payload.key
    #check key ownership
    if not key.startswith(f"{user.id}/"):
        raise HTTPException(status_code=403, detail="Key not owned by curent user")
    print("FINALIZE key=", key)
    print("Objects under prefix:", s3.list_prefix("2/"))
    try:
        head = s3.head(key=key)
    except ClientError as e:
        raise HTTPException(status_code=404, detail="Object not found in S3")
       
    
    size = int(head.get("ContentLength", 0))
    etag = (head.get("ETag") or "").strip('"')
    ctype = payload.content_type or head.get("ContentType") or "application/octet-stream"

    created = False

    existing = await session.execute(select(File).where(File.storage_key == key))
    db_file = existing.scalar_one_or_none()
    if db_file:
        db_file.filename = payload.filename
        db_file.content_type = ctype
        db_file.size = size
        db_file.etag = etag
    else:
        db_file = File(
            owner_id=user.id,
            storage_key=key,
            filename=payload.filename,
            content_type=ctype,
            size=size,
            etag=etag,
        )
        session.add(db_file)
        created = True

    await session.flush()

    #thumbnail job in queue
    if ctype.startswith("image/"):
        thumb_key = f"{db_file.storage_key}@thumb_256.jpg"
        get_url = s3.presigned_get(key=db_file.storage_key, expires_in=600)
        put_url = s3.presigned_put(key=thumb_key, content_type="image/jpeg", expires_in=600)

        db_file.thumbnail_key = thumb_key
        resize_image.delay(db_file.id, get_url, put_url, thumb_key)

    await session.commit()
    await session.refresh(db_file)

    #biuld response
    thumb_url = (
        s3.presigned_get(key=db_file.thumbnail_key) 
        if getattr(db_file, "thumbnail_key", None) 
        else None
    )

    if not created:
        response.status_code = status.HTTP_200_OK

    return FileResponse(
        id=db_file.id,
        key=db_file.storage_key,
        filename=db_file.filename,
        content_type=db_file.content_type,
        size=db_file.size,
        etag=db_file.etag,
        thumbnail_url=thumb_url,
        uploaded_at=db_file.uploaded_at
    )

    

    
    

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

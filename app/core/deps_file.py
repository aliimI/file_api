from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.core.deps import get_current_user
from app.models.file import File



async def get_file_or_404(
        file_id: int, 
        session: AsyncSession = Depends(get_async_session),
        user = Depends(get_current_user),
) -> File:
    db_file = await session.get(File, file_id)

    if not db_file or (user.role != "admin" and db_file.owner_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
    return db_file
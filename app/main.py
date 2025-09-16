from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_async_session
from app.routes.auth import router as auth_router
from app.routes.files import router as file_router
from app.tasks.celery_app import celery_app

app = FastAPI()

app.include_router(auth_router) 
app.include_router(file_router)

@app.get("/")
async def root():
    return {"message": "Secure File Vault API is running"}

@app.get("/test-db")
async def test_db(session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()
        return {"db_connection": value}
    except Exception as e:
        return {"error": str(e)}
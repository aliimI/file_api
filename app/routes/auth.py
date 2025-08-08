from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/register", response_model=UserRead)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    # check if user already exists
    query = select(User).where(User.email == user_data.email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        email=user_data.email,
        hashed_password = hash_password(user_data.password)
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/login")
async def login(user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.email == user_data.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
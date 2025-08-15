from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.core.security import hash_password, verify_password, create_access_token, new_jti, create_refresh_token, decode_token
from app.models.refresh_token import RefreshToken

from app.core.deps import get_current_user

from datetime import datetime, timedelta, timezone

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
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: AsyncSession = Depends(get_async_session)
    ):
    email = form_data.username
    password = form_data.password

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    jti = new_jti()
    refresh_token = create_refresh_token(user.id, jti)


    rt = RefreshToken(
        jti=jti,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    )
    session.add(rt)
    await session.commit()

    # add HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60*60*24*settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth",
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    sub = payload.get("sub")
    jti = payload.get("jti")


    # check if the token in db
    result = await session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.revoked or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token is not valid")
    
    db_token.revoked = True

    new_access = create_access_token({"sub": sub})
    new_jti_val = new_jti()
    new_refresh = create_refresh_token(int(sub), new_jti_val)

    session.add(RefreshToken(
        jti=new_jti_val,
        user_id=int(sub),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    ))
    await session.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,  
        samesite="lax",
        max_age=60*60*24*settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth",
    )
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    print("Cookie refresh token: ", refresh_token)
    
    if refresh_token:
        payload = decode_token(refresh_token)
        print("Decoded payload =", payload)

        if payload and payload.get("type") == "refresh":
            result = await session.execute(select(RefreshToken).where(RefreshToken.jti == payload["jti"]))
            db_token = result.scalar_one_or_none()
            if db_token and not db_token.revoked:
                db_token.revoked = True
                await session.commit()

    # clear cookie
    response.delete_cookie("refresh_token", path="/auth")
    return {"detail": "Logged out"}


@router.get("/me")
async def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
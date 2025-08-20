# from typing import Callable
# from fastapi import Depends, HTTPException, status
# from app.core.deps import get_current_user
# from app.models.user import User

# def require_role(*allowed: str) -> Callable:
#     async def role_checker(current_user: User = Depends(get_current_user)) -> User:
#         if current_user.role not in allowed:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
#         return current_user
#     return role_checker
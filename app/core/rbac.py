from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user

ROLE_RANK = {"viewer": 1, "editor": 2, "admin": 3}

def require_role(min_role: str):
    def _dep(user = Depends(get_current_user)):
        if ROLE_RANK.get(user.role, 0) < ROLE_RANK[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")
        return user
    return _dep
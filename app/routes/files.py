from fastapi import APIRouter, Depends
from app.core.roles import require_role

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

@router.post("/admin-only")
async def admin_only(_: any = Depends(require_role("admin"))):
    return {"ok": True}

@router.get("/viewer_or_above")
async def viewer_or_above(_: any = Depends(require_role("viewer", "editor", "admin"))):
    return {"ok": True}
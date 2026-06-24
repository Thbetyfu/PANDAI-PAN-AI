from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..deps import get_ui_path


router = APIRouter()


@router.get("/")
async def root_ui():
    ui_path = get_ui_path()
    if ui_path.exists():
        return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))
    return {"success": True, "message": "UI file not found. Open /docs for API documentation."}


@router.get("/ui")
async def ui():
    ui_path = get_ui_path()
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="UI file not found.")
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))


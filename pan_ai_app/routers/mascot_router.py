from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..deps import get_mascot_dir


router = APIRouter()


@router.get("/api/mascot/siswa/expressions")
async def get_siswa_mascot_expressions():
    mascot_dir = get_mascot_dir()
    expressions = []
    for svg_file in mascot_dir.glob("*.svg"):
        expressions.append(svg_file.stem)
    return {"success": True, "expressions": sorted(expressions)}


@router.get("/api/mascot/siswa/{expression}")
async def get_siswa_mascot(expression: str):
    mascot_dir = get_mascot_dir()
    svg_file = mascot_dir / f"{expression}.svg"

    if not svg_file.exists():
        svg_file = mascot_dir / "Happy.svg"
        if not svg_file.exists():
            raise HTTPException(status_code=404, detail=f"Mascot dengan ekspresi '{expression}' tidak ditemukan.")

    return FileResponse(
        path=str(svg_file),
        media_type="image/svg+xml",
        filename=f"pandai-siswa-{expression.lower()}.svg",
    )


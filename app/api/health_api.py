from fastapi import APIRouter
from app.db.mongo import db

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "MongoDB connected"}
    except Exception:
        return {"status": "MongoDB failed"}
from fastapi import APIRouter
from app.db.mongo import db

router = APIRouter()

@router.get("/health")
def health_check():
    try:
        db.command("ping")
        return {"status": "MongoDB connected"}
    except:
        return {"status": "MongoDB failed"}
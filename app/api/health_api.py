from fastapi import APIRouter
from pymongo.errors import PyMongoError
from app.db.mongo import db

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "MongoDB connected"}
    except PyMongoError:
        return {"status": "MongoDB failed"}
from pymongo import ASCENDING, AsyncMongoClient

from app.core.config import settings

client = AsyncMongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]


async def create_indexes():
    await db.admins.create_index("email", unique=True)
    await db.detections.create_index(
        [("admin_id", ASCENDING), ("detected_at", ASCENDING)],
    )
    await db.detections.create_index("review_status")
    await db.revoked_tokens.create_index(
        "expires_at",
        expireAfterSeconds=0,
    )

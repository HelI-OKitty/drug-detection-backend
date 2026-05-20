from pymongo import AsyncMongoClient

from app.core.config import settings

client = AsyncMongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

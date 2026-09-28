from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.models.user import User


client = AsyncMongoClient(settings.mongodb_uri)


async def init_db():
    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[User],
    )
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


client = AsyncIOMotorClient(settings.mongodb_uri)


async def init_db():
    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[],
    )
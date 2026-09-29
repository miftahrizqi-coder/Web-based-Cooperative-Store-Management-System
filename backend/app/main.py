from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.procurement import router as procurement_router
from app.core.database import client, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await client.close()


app = FastAPI(title="Koprom API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(procurement_router)
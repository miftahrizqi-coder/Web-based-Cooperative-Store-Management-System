import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from app.api.activity import router as activity_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.expenses import router as expenses_router
from app.api.inventory import router as inventory_router
from app.api.members import router as members_router
from app.api.procurement import router as procurement_router
from app.api.products import router as products_router
from app.api.reports import router as reports_router
from app.api.returns import router as returns_router
from app.api.sales import router as sales_router
from app.api.supplier_products import router as supplier_products_router
from app.api.suppliers import router as suppliers_router
from app.api.users import router as users_router
from app.core.config import settings
from app.core.database import client, init_db


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await client.close()


app = FastAPI(title="Sistem Informasi Toko Koperasi API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)


@app.exception_handler(DuplicateKeyError)
async def duplicate_key_handler(request: Request, exc: DuplicateKeyError):
    # Jaring pengaman race-condition: validasi unik di aplikasi bisa lolos
    # bersamaan, index unik MongoDB yang menolak.
    return JSONResponse(
        status_code=409,
        content={"detail": "Data dengan nilai unik yang sama sudah ada."},
    )


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(suppliers_router)
app.include_router(supplier_products_router)
app.include_router(members_router)
app.include_router(procurement_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(returns_router)
app.include_router(expenses_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)
app.include_router(activity_router, prefix="/api")

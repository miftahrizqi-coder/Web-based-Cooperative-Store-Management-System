"""Utilitas umum yang dipakai lintas modul."""

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from bson import ObjectId
from fastapi import HTTPException, Query, Response, status
from pymongo import ReturnDocument

from app.core.config import settings


LOCAL_TZ = ZoneInfo(settings.app_timezone)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Mongo mengembalikan datetime naive (UTC). Normalisasi ke aware."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def local_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Batas [awal, akhir) satu hari lokal, dikonversi ke UTC."""
    start = datetime.combine(day, time.min, tzinfo=LOCAL_TZ)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def local_range_bounds(
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    """Konversi rentang tanggal lokal inklusif menjadi [start, end) UTC."""
    start = local_day_bounds(date_from)[0] if date_from else None
    end = local_day_bounds(date_to)[1] if date_to else None
    return start, end


def to_local_date(value: datetime) -> date:
    return as_utc(value).astimezone(LOCAL_TZ).date()


def parse_object_id(value: str, label: str = "ID") -> ObjectId:
    if not value or not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} tidak valid.",
        )
    return ObjectId(value)


def search_regex(term: str) -> dict:
    """Regex case-insensitive yang aman dari injeksi pola regex."""
    return {"$regex": re.escape(term.strip()), "$options": "i"}


def money(value: float) -> float:
    """Pembulatan nominal rupiah ke 2 desimal agar tidak drift float."""
    return round(float(value) + 0.0, 2)


async def next_document_number(prefix: str, width: int = 4) -> str:
    """
    Nomor dokumen harian berbasis counter atomik, mis.:
    TRX-20260928-0001, PO-20260928-0001, GR-..., PUR-..., RET-..., EXP-...
    """
    from app.core.database import get_database

    today = datetime.now(LOCAL_TZ).strftime("%Y%m%d")
    key = f"{prefix}-{today}"

    counter = await get_database()["document_counters"].find_one_and_update(
        {"_id": key},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    return f"{prefix}-{today}-{counter['value']:0{width}d}"


class Pagination:
    """
    Dependency pagination. Jika `page` tidak dikirim dan `default_page_size`
    None, seluruh data dikembalikan (kompatibel dengan halaman lama).
    Total selalu dikirim lewat header `X-Total-Count`.
    """

    def __init__(self, default_page_size: int | None = None, max_page_size: int = 200):
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size

    def __call__(
        self,
        response: Response,
        page: int | None = Query(default=None, ge=1),
        page_size: int | None = Query(default=None, ge=1, alias="pageSize"),
    ) -> "PageParams":
        size = page_size or self.default_page_size
        if size is not None:
            size = min(size, self.max_page_size)
        return PageParams(page=page or 1, size=size, response=response)


class PageParams:
    def __init__(self, page: int, size: int | None, response: Response):
        self.page = page
        self.size = size
        self.response = response

    @property
    def skip(self) -> int:
        return 0 if self.size is None else (self.page - 1) * self.size

    def set_total(self, total: int) -> None:
        self.response.headers["X-Total-Count"] = str(total)
        if self.size is not None:
            self.response.headers["X-Page"] = str(self.page)
            self.response.headers["X-Page-Size"] = str(self.size)

    async def apply(self, find_query):
        """Terapkan ke Beanie FindMany; mengembalikan list dokumen."""
        total = await find_query.count()
        self.set_total(total)
        if self.size is not None:
            find_query = find_query.skip(self.skip).limit(self.size)
        return await find_query.to_list()

    def slice(self, items: list) -> list:
        self.set_total(len(items))
        if self.size is None:
            return items
        return items[self.skip:self.skip + self.size]


async def inc_embedded_item(
    collection,
    doc_id: ObjectId,
    product_id: str,
    field: str,
    delta: float,
    session=None,
    retries: int = 5,
) -> None:
    """
    Tambah nilai field numerik pada elemen `items` dengan productId tertentu.

    Implementasi read-modify-write dengan compare-and-set pada array `items`
    (bukan operator posisional `$`) agar portabel lintas server kompatibel
    MongoDB, tetap aman terhadap update bersamaan.
    """
    for _ in range(retries):
        doc = await collection.find_one({"_id": doc_id}, {"items": 1}, session=session)
        if doc is None:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")
        items = doc.get("items", [])
        new_items = []
        found = False
        for item in items:
            item = dict(item)
            if not found and item.get("productId") == product_id:
                item[field] = (item.get(field) or 0) + delta
                found = True
            new_items.append(item)
        if not found:
            raise HTTPException(status_code=422, detail="Item tidak ditemukan pada dokumen.")
        result = await collection.update_one(
            {"_id": doc_id, "items": items},
            {"$set": {"items": new_items}},
            session=session,
        )
        if result.modified_count == 1:
            return
    raise HTTPException(status_code=409, detail="Dokumen sedang diubah pengguna lain. Ulangi.")

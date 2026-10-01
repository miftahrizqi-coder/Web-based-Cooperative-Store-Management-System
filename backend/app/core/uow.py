"""
Unit of Work untuk operasi yang melibatkan beberapa dokumen penting
(penjualan, penerimaan barang, retur, pembayaran, stock opname).

- Jika MongoDB mendukung transaksi (replica set / sharded cluster),
  semua operasi berjalan dalam satu transaksi: COMMIT jika sukses,
  ROLLBACK otomatis jika ada exception (PRD §35 Reliability).
- Jika tidak (MongoDB standalone saat development), setiap operasi
  mendaftarkan aksi kompensasi. Saat terjadi exception, kompensasi
  dijalankan terbalik sehingga data kembali konsisten sebisa mungkin.
  Perubahan stok tetap memakai update kondisional atomik ($inc + filter
  stok >= qty) sehingga stok tidak pernah negatif walau tanpa transaksi.
"""

import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from app.core.database import client, transactions_supported


logger = logging.getLogger("koperasi.uow")

Compensation = Callable[[], Awaitable[object]]


class UnitOfWork:
    def __init__(self, session=None):
        self.session = session
        self._compensations: list[Compensation] = []

    @property
    def transactional(self) -> bool:
        return self.session is not None

    def on_rollback(self, action: Compensation) -> None:
        """Daftarkan kompensasi (hanya dipakai pada mode non-transaksi)."""
        if not self.transactional:
            self._compensations.append(action)

    async def insert(self, document):
        """Insert dokumen Beanie dan daftarkan kompensasinya."""
        await document.insert(session=self.session)
        self.on_rollback(lambda doc=document: doc.delete())
        return document

    async def compensate(self) -> None:
        for action in reversed(self._compensations):
            try:
                await action()
            except Exception:  # pragma: no cover - best effort
                logger.exception("Kompensasi gagal dijalankan")
        self._compensations.clear()


@asynccontextmanager
async def unit_of_work():
    if transactions_supported():
        async with client.start_session() as session:
            async with await session.start_transaction():
                yield UnitOfWork(session)
        return

    uow = UnitOfWork(None)
    try:
        yield uow
    except BaseException:
        await uow.compensate()
        raise

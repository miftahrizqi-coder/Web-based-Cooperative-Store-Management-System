# Koprom — Sistem Informasi Toko Koperasi

<<<<<<< HEAD
Sistem Informasi Toko Koperasi
React + FastAPI + MongoDB. Praktikum Big Data dan NoSQL.
Prasyarat
Python 3.10+
Node.js 18+
MongoDB berjalan di `mongodb://localhost:27017`
1. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # opsional

python -m app.seed --demo        # data awal + riwayat penjualan 14 hari
uvicorn app.main:app --reload    # http://127.0.0.1:8000/docs
```
Opsi seed: tanpa `--demo` hanya data master dan stok awal; `--reset` mengosongkan database lebih dulu.
2. Frontend
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```
Vite meneruskan `/api` ke `http://127.0.0.1:8000`.
Desain NoSQL
Collection	Isi	Pola
products	master produk	reference `categoryId`, nama kategori disalin
sales	transaksi	`items[]` embedded + snapshot nama/SKU/harga
supplies	barang masuk	`items[]` embedded + `supplier` snapshot
stock_movements	log SUPPLY / SALE / ADJUSTMENT	reference `productId`, `referenceId`
counters	nomor invoice per hari	`$inc` atomik
Dashboard memakai aggregation pipeline (`$group`, `$unwind`, `$dateToString`) pada `sales`.
Integritas stok (BR-06)
Pengurangan stok memakai `find_one_and_update` dengan filter `stock >= qty`, sehingga stok tidak
bisa negatif walau ada request bersamaan. Jika langkah berikutnya gagal, stok, movement, dan sales
dikembalikan (rollback manual). MongoDB standalone tidak mendukung multi-document transaction;
jika memakai replica set, blok tersebut bisa dibungkus `session.with_transaction`.
Skenario uji
Supply: `POST /api/supplies` untuk Buku Tulis 100 unit, stok bertambah 100 dan ada movement `SUPPLY`.
Jual 2 Buku Tulis, stok berkurang 2 dan ada movement `SALE`.
Stok 6 (Tisu), beli 7: ditolak dan stok tetap.
Setelah checkout halaman `/invoice/:id` terbuka, transaksi muncul di `/history`, dan grafik dashboard berubah.
Catatan
API CRUD produk, kategori, dan supplier sudah lengkap (lihat `/docs`). Antarmuka pengelolaan master data
belum dibuat karena di luar halaman yang diminta.
=======
Aplikasi web untuk operasional toko koperasi: master data, pengadaan (PO → penerimaan → pembelian → invoice → hutang → pembayaran), inventory, POS, retur, pengeluaran, laporan, dan audit log. Spesifikasi lengkap ada di `PRD.md`; hasil audit & daftar perubahan ada di [`docs/AUDIT.md`](docs/AUDIT.md).

| Lapisan  | Teknologi |
|----------|-----------|
| Backend  | Python 3.11+, FastAPI, Beanie (ODM), PyMongo async |
| Database | MongoDB 6+ (replica set disarankan) |
| Frontend | Vue 3 + TypeScript + Tailwind CSS 4 (Vite) |
| Auth     | JWT Bearer, password Argon2id |

## Menjalankan secara lokal

### 1. MongoDB

Standalone sudah cukup untuk development. Untuk **transaksi multi-dokumen** (PRD §35) jalankan sebagai replica set satu node:

```bash
mongod --replSet rs0 --dbpath ./data
mongosh --eval 'rs.initiate()'
# MONGODB_URI=mongodb://127.0.0.1:27017/?replicaSet=rs0
```

Tanpa replica set, backend otomatis memakai **mode kompensasi** (rollback manual per langkah) dan mencatatnya di log startup.

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # WAJIB ganti JWT_SECRET_KEY
python -m app.seed --demo       # admin awal + data & akun contoh
uvicorn app.main:app --reload --port 8000
```

Dokumentasi API interaktif: http://127.0.0.1:8000/docs

Akun dari `python -m app.seed --demo` (segera ganti password):

| Role     | Username | Password         |
|----------|----------|------------------|
| Admin    | admin    | Admin12345!      |
| Kasir    | kasir    | Kasir12345!      |
| Pengurus | pengurus | Pengurus12345!   |
| Anggota  | anggota  | Anggota12345!    |

Tanpa `--demo`, hanya akun admin yang dibuat (kredensial dari env `SEED_ADMIN_*`).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> :8000)
npm run build      # vue-tsc + vite build
```

## Pengujian

Uji end-to-end memakai database kosong khusus uji:

```bash
cd backend
pip install -r requirements-dev.txt
export MONGODB_DATABASE=koperasi_e2e
python -m app.seed --demo
uvicorn app.main:app --port 8001 &
E2E_BASE_URL=http://127.0.0.1:8001 python tests/e2e_flow.py
```

`tests/e2e_flow.py` memverifikasi ±160 pemeriksaan: autentikasi & otorisasi per role, rate limit login, CRUD master data, alur PO sampai pelunasan (termasuk penerimaan sebagian dan retur pembelian), POS, retur penjualan, pembatalan, adjustment & stock opname, laporan, audit log, serta uji konkurensi penjualan paralel (BR-02).

Uji tambahan:

```bash
MONGODB_DATABASE=koperasi_uow_test MONGODB_TRANSACTIONS=off python tests/uow_compensation.py
MONGODB_DATABASE=koperasi_migration_test python tests/legacy_migration.py
```

## Catatan operasional

- **Migrasi data lama** berjalan otomatis saat startup: field produk snake_case → camelCase (PRD §10), skema `sales` lama → skema PRD §23, tanda `quantity` stock movement penjualan, dan cache `paidAmount` invoice.
- **Index unik** (SKU, barcode, username, email, kode supplier, nomor anggota, nomor dokumen) dibuat saat startup. Jika data lama duplikat, index tidak dibuat dan peringatan dicatat di log — bersihkan duplikat lalu restart.
- **Production**: jalankan di belakang HTTPS (reverse proxy), set `JWT_SECRET_KEY` acak, batasi `CORS_ORIGINS`. Rate limit login bersifat in-memory per proses; untuk multi-worker gunakan penyimpanan terpusat.
- **Backup**: jadwalkan `mongodump --uri "$MONGODB_URI" --db koperasi_db --out /backup/$(date +%F)` harian dan uji restore berkala.
- **HPP / laporan laba**: memakai harga beli yang di-snapshot saat penjualan (harga beli terakhir dari penerimaan barang). Tetapkan metode HPP resmi koperasi sebelum laporan laba dipakai sebagai laporan resmi (PRD §28.6).
>>>>>>> origin/main

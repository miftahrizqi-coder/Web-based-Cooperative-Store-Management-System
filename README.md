# Koprom (Koperasi Romantis)

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
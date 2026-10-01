# Audit & Perbaikan terhadap PRD

Dokumen ini mencatat hasil audit aplikasi terhadap `PRD.md` (v1.0), perbaikan yang dilakukan, cara verifikasinya, dan hal yang masih terbuka. Baseline = kode sebelum perbaikan.

## 1. Ringkasan

Baseline sudah memiliki fondasi yang cukup baik untuk auth, user, produk, supplier, produk supplier, PO, dan halaman inventory. Namun ada **bug yang merusak data**, **modul PRD yang tidak ada sama sekali** (kategori, retur, pengeluaran, laporan, audit log, UI anggota, riwayat penjualan), **UI penerimaan barang yang ternyata salinan form produk**, dan beberapa aturan bisnis PRD yang tidak dijalankan.

## 2. Temuan kritis (bug)

| # | Temuan | Dampak | Perbaikan |
|---|--------|--------|-----------|
| 1 | `GoodsReceiptFormPage.vue` identik byte-per-byte dengan `ProductFormPage.vue`; `createGoodsReceipt` tidak pernah dipanggil dari UI. Tombol "Terima Barang" ke `/goods-receipts/create` bahkan tidak punya rute. | Penerimaan barang (inti alur pengadaan & penambah stok) tidak bisa dilakukan dari aplikasi. | Form penerimaan baru: pilih PO, sisa per item, datang/diterima baik/ditolak + alasan, penerimaan sebagian. Rute `/goods-receipts/create` dan `/create/:id`. |
| 2 | Penerimaan barang menulis `updatedAt` & membaca `int(stock)` pada koleksi produk yang memakai `updated_at` & stok float. | Dokumen produk berisi dua field tanggal; stok desimal terpotong. | Skema produk diseragamkan camelCase (PRD §10) + migrasi otomatis. Semua perubahan stok lewat satu primitif (`services/stock.py`). |
| 3 | Penjualan memakai `session.start_transaction()` tanpa fallback. | Di MongoDB standalone setiap transaksi POS gagal (500). | `core/uow.py`: transaksi bila didukung, selain itu kompensasi terurut. |
| 4 | `stockBefore` penjualan diambil dari snapshot sebelum transaksi; `quantity` SALE positif. | Kartu stok salah saat ada penjualan bersamaan; tidak sesuai PRD §20 (keluar = negatif). | Stok diubah dengan `find_one_and_update` kondisional; `stockBefore/After` dari hasil atomik; quantity bertanda. Data lama dimigrasi. |
| 5 | Tidak ada cara membuat user pertama (semua endpoint user butuh admin). | Aplikasi tidak bisa dipakai dari nol. | `python -m app.seed [--demo]`. |
| 6 | Pencarian memakai regex mentah dari input pengguna. | Regex injection / ReDoS. | `search_regex()` meng-escape input. |
| 7 | Edit produk bisa mengubah `stock` langsung. | Stok berubah tanpa jejak kartu stok. | Stok hanya lewat transaksi/adjustment/opname; stok awal dicatat sebagai movement. |
| 8 | PO menerima `productId/sku/name` dari klien tanpa dicek terhadap `supplierProductId`. | PO bisa berisi produk yang tidak sesuai supplier; nama/SKU palsu tersimpan. | Server mengambil snapshot dari master; minimum order ditegakkan. |
| 9 | Pembayaran supplier: cek sisa hutang lalu tulis (race). Invoice tidak pernah `OVERDUE`. | Bisa overpay bila dua pembayaran bersamaan; status jatuh tempo tidak muncul. | Guard atomik `paidAmount`; status OVERDUE diturunkan dari jatuh tempo. |
| 10 | Frontend memakai metode bayar supplier `GIRO` (backend menolak), field `invoice.shipping`/`purchaseId` yang tidak ada, dan menampilkan ID mentah supplier. | Form pembayaran error 422; kolom kosong. | Disesuaikan ke kontrak API; nama supplier ditampilkan. |
| 11 | `GoodsReceiptListPage` memakai `reduce` pada `unknown[]` tanpa tipe. | `vue-tsc` gagal sehingga `npm run build` gagal. | `reduce<number>()`. |
| 12 | `requirements.txt` berformat UTF-16. | `pip install -r` gagal di sebagian lingkungan. | Dikonversi ke UTF-8. |
| 13 | Label role di layout memakai key huruf besar (`ADMIN`) padahal role huruf kecil. | Label role tampil mentah. | Pakai `ROLE_LABELS`. |
| 14 | Logout hanya menghapus token di klien; ganti password tidak mencabut token lama. | Token curian tetap berlaku hingga kedaluwarsa. | Denylist `jti` saat logout; `tokenVersion` saat ganti/reset password, ubah role, atau nonaktif. |

## 3. Cakupan modul PRD

| Modul (PRD §4.1/§7) | Sebelum | Sesudah |
|---|---|---|
| Authentication (login, logout, me, ubah & reset password, rate limit) | sebagian | lengkap (reset oleh admin) |
| User & role/permission | ada | + tautan akun anggota, proteksi admin terakhir, audit |
| Dashboard | placeholder "—" | KPI PRD §9, grafik 14 hari, stok menipis/habis, invoice jatuh tempo, terlaris |
| Kategori | tidak ada | CRUD + nonaktif, filter produk per kategori |
| Produk | ada | camelCase, kategori dropdown, harga beli disembunyikan dari kasir, hapus permanen hanya bila tanpa riwayat |
| Supplier & produk supplier | ada (riwayat placeholder) | + DELETE, sub-resource riwayat PO/penerimaan/pembelian/invoice/pembayaran/hutang, satu supplier preferred per produk |
| Anggota | API saja | halaman daftar/form/detail, nomor otomatis, total belanja, riwayat transaksi, self-service anggota |
| PO | ada | + tolak approval, selesaikan (COMPLETED), qty diterima/sisa, validasi minimum order |
| Penerimaan barang | **UI rusak** | form baru, penerimaan sebagian, optimistic lock PO |
| Pembelian, invoice, hutang, pembayaran | ada | due date default dari termin supplier, OVERDUE, kredit retur, guard overpay |
| Inventory, movement, adjustment, opname | ada | opname multi-produk tersimpan (`stock_opnames`), cek stok berubah, kartu stok dengan filter & pagination |
| POS / pembayaran | ada | metode PRD §24, diskon, referensi non-tunai, struk |
| Riwayat penjualan | tidak ada | daftar + detail + cetak struk + pembatalan |
| Retur penjualan & pembelian | tidak ada | pengajuan → approval → stok & refund/koreksi hutang |
| Pengeluaran | tidak ada | CRUD + filter periode/kategori |
| Laporan (6) | tidak ada | penjualan, pembelian, inventory, supplier, hutang (+aging), laba dasar; ekspor CSV & cetak |
| Audit log | hanya activity pengadaan | koleksi `audit_logs`, halaman admin dengan filter & ekspor |

Semua endpoint pada PRD §33 tersedia (lihat `/docs`).

## 4. Business rules

| Aturan | Implementasi |
|---|---|
| BR-01 Stok (beli/jual/retur) | `apply_stock_change` dengan movement PURCHASE, SALE, SALE_RETURN, PURCHASE_RETURN |
| BR-02 Stok tidak minus | update kondisional `stock >= qty` di MongoDB (atomik), bukan cek-lalu-tulis |
| BR-03 Harga historis | `price` & `costPrice` di-snapshot di item penjualan |
| BR-04 Invoice unik `TRX-YYYYMMDD-NNNN` | counter atomik per hari (zona `Asia/Jakarta`) + index unik |
| BR-05 PO tidak menambah stok | stok hanya dari `acceptedQuantity` penerimaan |
| BR-06 Penerimaan sebagian | `receivedQuantity`/`remainingQuantity` per item PO, status PARTIALLY_RECEIVED |
| BR-07 Pembatalan | status CANCELLED + movement pembalik (hanya qty yang belum diretur) + refund; tidak ada DELETE penjualan |
| BR-08 Pembayaran supplier | sisa = total − retur − bayar; PAID / PARTIALLY_PAID (+OVERDUE) |
| BR-09 Produk tidak dihapus permanen | DELETE = nonaktif; permanen hanya bila belum pernah dipakai |

Segregation of duties: pembuat PO tidak dapat menyetujui PO-nya sendiri; pengaju retur tidak dapat menyetujui returnya sendiri.

## 5. Keamanan (PRD §35)

Argon2id, JWT dengan `jti` + `tokenVersion`, logout mencabut token, rate limit login (5 gagal/5 menit per IP+username, HTTP 429), validasi input Pydantic, regex di-escape, CORS terbatas, data sensitif (harga beli/HPP) disembunyikan dari kasir, audit untuk login/gagal login/logout/perubahan data/penjualan/pembatalan/adjustment/opname/approval/pembayaran.

## 6. Verifikasi yang dilakukan

- **Backend**: `tests/e2e_flow.py` — 156 pemeriksaan lulus terhadap server kompatibel MongoDB (tanpa transaksi, sehingga jalur kompensasi ikut teruji); `tests/uow_compensation.py` — rollback saat gagal di tengah transaksi; `tests/legacy_migration.py` — migrasi data lama.
- **Frontend**: seluruh script & ekspresi template SFC di-typecheck (TypeScript strict, `noUnusedLocals`) dengan harness yang meniru `vue-tsc`; lulus tanpa error.

## 7. Batasan & hal yang masih terbuka

1. **Belum diverifikasi di lingkungan ini**: `npm run build` (vue-tsc + Vite) dan uji konkurensi terhadap MongoDB asli — registry npm/PyPI dan binary MongoDB tidak dapat diakses dari sandbox pengerjaan. Jalankan keduanya sebelum rilis (lihat README). Bagian `[11] Konkurensi` pada e2e bergantung pada atomisitas update dokumen MongoDB asli.
2. **Pengaturan (PRD §6.1 "Pengaturan")** tidak didefinisikan detailnya di PRD; belum ada halaman pengaturan (nama toko di struk, pilihan metode HPP). Metode HPP saat ini tetap: harga beli terakhir yang di-snapshot saat penjualan.
3. **Reset password mandiri via email** tidak diimplementasikan (butuh infrastruktur email); reset dilakukan admin.
4. **Rate limit** in-memory per proses; untuk multi-worker perlu penyimpanan terpusat (Redis).
5. **Laporan** diagregasi di aplikasi (Python) agar portabel; untuk data sangat besar pindahkan ke aggregation pipeline (satu titik di `services/reports.py`).
6. Halaman lama pengadaan/supplier masih memanggil API dengan pola `fetch` + token sendiri; halaman baru memakai `services/api.ts` (401 → login ulang otomatis). Konsolidasi penuh bisa dilakukan bertahap.
7. `koperasi.zip` di root repo adalah salinan lama proyek (berisi `.git`); sebaiknya dihapus dari repositori.

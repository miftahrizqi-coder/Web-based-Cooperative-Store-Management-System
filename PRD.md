# PRD — Sistem Informasi Toko Koperasi

**Versi:** 1.0  
**Status:** Draft  
**Platform:** Web Application  
**Database:** MongoDB  
**Backend:** Python Fast API 
**Frontend:** Vue 3 + TypeScript + Tailwind CSS  
**ORM/ODM:** Beanie
**API:** REST API  
**Authentication:** JWT / session-based authentication  
**Bahasa:** Indonesia

---

## 1. Ringkasan Produk

Sistem Informasi Toko Koperasi adalah aplikasi berbasis web untuk mengelola seluruh aktivitas operasional toko koperasi, mulai dari pengelolaan pengguna, anggota, barang, kategori, supplier, pengadaan, penerimaan barang, persediaan, penjualan, pembayaran, retur, pengeluaran, hingga laporan.

Sistem menggunakan MongoDB sebagai database utama karena struktur data transaksi memiliki detail yang dapat disimpan sebagai embedded document, sementara data master dan histori operasional dapat dihubungkan menggunakan ObjectId reference.

Sistem dirancang agar dapat digunakan oleh beberapa jenis pengguna dengan hak akses berbeda, yaitu Admin, Kasir, Pengurus, dan Anggota.

---

# 2. Latar Belakang

Pengelolaan toko koperasi yang masih menggunakan pencatatan manual atau spreadsheet dapat menyebabkan beberapa masalah:

- Data barang sulit diperbarui secara konsisten.
- Stok tidak selalu sesuai dengan kondisi fisik.
- Riwayat pembelian dan penjualan sulit ditelusuri.
- Pengelolaan supplier belum terintegrasi.
- Purchase Order, penerimaan barang, invoice, hutang, dan pembayaran supplier sulit dipantau.
- Laporan penjualan dan stok membutuhkan proses rekap manual.
- Aktivitas pengguna sulit ditelusuri.
- Pengurus kesulitan memperoleh informasi kondisi toko secara cepat.

Sistem ini dibuat untuk mengintegrasikan proses tersebut dalam satu aplikasi.

---

# 3. Tujuan Produk

## 3.1 Tujuan Utama

1. Digitalisasi operasional toko koperasi.
2. Mengelola persediaan secara terstruktur.
3. Mempercepat proses transaksi penjualan.
4. Mengelola supplier dan proses pengadaan.
5. Menyediakan informasi hutang dan pembayaran supplier.
6. Menyediakan laporan operasional dan keuangan dasar.
7. Menyediakan kontrol akses berdasarkan role.
8. Menyediakan audit trail terhadap aktivitas penting.

## 3.2 Indikator Keberhasilan

Sistem dianggap berhasil apabila:

- Pengguna dapat melakukan login sesuai role.
- Data barang dapat dikelola secara terpusat.
- Pembelian dapat menambah stok secara otomatis setelah barang diterima.
- Penjualan dapat mengurangi stok secara otomatis.
- Sistem mencegah penjualan melebihi stok.
- Purchase Order dapat dipantau sampai penerimaan.
- Penerimaan sebagian dapat ditangani.
- Invoice dan hutang supplier dapat dicatat.
- Pembayaran supplier dapat mengurangi saldo hutang.
- Pengurus dapat melihat laporan.
- Aktivitas penting dapat dilacak melalui audit log.

---

# 4. Ruang Lingkup

## 4.1 In Scope

- Authentication
- User management
- Role & permission
- Dashboard
- Master barang
- Kategori barang
- Supplier
- Produk supplier
- Anggota koperasi
- Purchase Order
- Penerimaan barang
- Pembelian
- Invoice supplier
- Hutang supplier
- Pembayaran supplier
- Inventory
- Stock opname
- Penjualan/POS
- Pembayaran pelanggan
- Retur penjualan
- Retur pembelian
- Pengeluaran
- Laporan
- Audit log

## 4.2 Out of Scope untuk MVP

- Akuntansi double-entry penuh
- Payroll
- Manajemen SHU kompleks
- Integrasi ERP
- Marketplace eksternal
- Multi-cabang kompleks
- Forecasting AI
- Integrasi perbankan otomatis

Fitur tersebut dapat menjadi pengembangan tahap berikutnya.

---

# 5. Target Pengguna

| Role | Deskripsi |
|---|---|
| Admin | Mengelola sistem, pengguna, master data, dan konfigurasi |
| Kasir | Mengelola transaksi penjualan |
| Pengurus | Memantau operasional, pengadaan, stok, dan laporan |
| Anggota | Melihat profil dan riwayat transaksi pribadi |

---

# 6. Hak Akses

## 6.1 Admin

Admin memiliki akses penuh terhadap:

- Dashboard
- User
- Role & permission
- Produk
- Kategori
- Supplier
- Produk supplier
- Anggota
- Purchase Order
- Penerimaan barang
- Pembelian
- Invoice supplier
- Pembayaran supplier
- Inventory
- Stock opname
- Penjualan
- Retur
- Pengeluaran
- Laporan
- Audit log
- Pengaturan

## 6.2 Kasir

Kasir dapat:

- Melihat produk aktif.
- Mencari produk.
- Scan barcode.
- Membuat transaksi penjualan.
- Memilih anggota.
- Memproses pembayaran.
- Mencetak struk.
- Melihat transaksi yang dibuat sendiri.

Kasir tidak dapat:

- Mengubah harga produk.
- Menghapus produk.
- Mengubah stok secara manual.
- Menghapus transaksi.
- Mengelola supplier.

## 6.3 Pengurus

Pengurus dapat:

- Melihat dashboard.
- Mengelola/memantau supplier.
- Membuat dan menyetujui Purchase Order.
- Memproses penerimaan barang.
- Melihat pembelian.
- Melihat stok.
- Melakukan stock opname.
- Melihat penjualan.
- Melihat pengeluaran.
- Melihat laporan.
- Memantau hutang supplier.

## 6.4 Anggota

Anggota dapat:

- Melihat profil.
- Melihat nomor anggota.
- Melihat status keanggotaan.
- Melihat riwayat transaksi.
- Melihat detail transaksi pribadi.

---

# 7. Modul Sistem

```text
SISTEM TOKO KOPERASI
│
├── Authentication
├── Dashboard
├── User Management
│
├── Master Data
│   ├── Produk
│   ├── Kategori
│   ├── Supplier
│   ├── Produk Supplier
│   └── Anggota
│
├── Pengadaan
│   ├── Purchase Order
│   ├── Penerimaan Barang
│   ├── Pembelian
│   ├── Invoice Supplier
│   ├── Hutang Supplier
│   └── Pembayaran Supplier
│
├── Inventory
│   ├── Stok
│   ├── Stock Movement
│   ├── Stock Adjustment
│   └── Stock Opname
│
├── Penjualan
│   ├── POS/Kasir
│   ├── Pembayaran
│   ├── Riwayat Penjualan
│   └── Retur Penjualan
│
├── Retur Pembelian
├── Pengeluaran
├── Laporan
└── Audit Log
```

---

# 8. Authentication

## Fitur

- Login
- Logout
- Get current user
- Ubah password
- Reset password
- Role-based authorization

## Login

Input:

```json
{
  "username": "admin",
  "password": "password"
}
```

Output:

```json
{
  "user": {
    "id": "...",
    "name": "Administrator",
    "role": "admin"
  },
  "token": "..."
}
```

## Acceptance Criteria

- Username dan password harus divalidasi.
- Password tidak disimpan dalam plaintext.
- User nonaktif tidak dapat login.
- Token hanya dapat mengakses resource sesuai permission.

---

# 9. Dashboard

Dashboard Admin/Pengurus menampilkan:

- Penjualan hari ini.
- Jumlah transaksi hari ini.
- Total produk.
- Total anggota.
- Produk stok menipis.
- Produk habis.
- Purchase Order aktif.
- Hutang supplier.
- Invoice jatuh tempo.
- Pengeluaran.
- Grafik penjualan.
- Produk terlaris.

Contoh:

```text
┌──────────────────────────────────────────┐
│ Dashboard Toko Koperasi                  │
├────────────┬────────────┬────────────────┤
│ Penjualan  │ Transaksi  │ Produk         │
│ Rp 8,5 Jt  │ 325        │ 450            │
├────────────┴────────────┴────────────────┤
│ Grafik Penjualan                          │
├───────────────────────┬──────────────────┤
│ Stok Menipis          │ Hutang Supplier  │
│ Buku      5           │ Rp12.000.000     │
│ Pulpen    8           │                  │
└───────────────────────┴──────────────────┘
```

---

# 10. Master Produk

## Fitur

- Tambah produk
- Edit produk
- Detail produk
- Nonaktifkan produk
- Pencarian
- Filter kategori
- Filter stok
- Barcode
- SKU
- Harga beli
- Harga jual
- Stok minimum

## Data Produk

```json
{
  "_id": "ObjectId",
  "sku": "ATK-001",
  "barcode": "8991234567890",
  "name": "Buku Tulis",
  "categoryId": "ObjectId",
  "unit": "pcs",
  "purchasePrice": 3000,
  "sellingPrice": 4000,
  "stock": 50,
  "minimumStock": 10,
  "isActive": true,
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

## Business Rules

- SKU harus unik.
- Barcode harus unik jika digunakan.
- Harga tidak boleh negatif.
- Stok tidak boleh negatif.
- Produk yang memiliki transaksi sebaiknya dinonaktifkan, bukan dihapus permanen.

---

# 11. Kategori Produk

## Fitur

- Tambah kategori
- Edit kategori
- Nonaktifkan kategori
- Daftar produk berdasarkan kategori

## Collection `categories`

```json
{
  "_id": "ObjectId",
  "name": "ATK",
  "description": "Alat tulis kantor",
  "isActive": true,
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

---

# 12. Supplier

Supplier merupakan pihak yang menyediakan barang kepada koperasi.

## Fitur

- Tambah supplier
- Edit supplier
- Detail supplier
- Nonaktifkan supplier
- Produk yang disuplai
- Riwayat PO
- Riwayat penerimaan
- Riwayat pembelian
- Riwayat invoice
- Riwayat pembayaran
- Informasi hutang

## Data Supplier

```json
{
  "_id": "ObjectId",
  "supplierCode": "SUP-001",
  "name": "PT Supplier ABC",
  "companyName": "PT Supplier ABC Indonesia",
  "contactPerson": "Budi",
  "phone": "08123456789",
  "email": "supplier@example.com",
  "address": {
    "street": "Jl. Soekarno Hatta No. 10",
    "city": "Bandung",
    "province": "Jawa Barat",
    "postalCode": "40286"
  },
  "paymentTerm": {
    "type": "CREDIT",
    "days": 30
  },
  "bankAccount": {
    "bankName": "BCA",
    "accountNumber": "1234567890",
    "accountName": "PT Supplier ABC"
  },
  "status": "ACTIVE",
  "notes": "Supplier ATK",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

## Status Supplier

```text
ACTIVE
INACTIVE
BLACKLISTED
```

---

# 13. Produk Supplier

Satu produk dapat mempunyai lebih dari satu supplier.

Contoh:

```text
Buku Tulis
├── Supplier A → Rp3.000
├── Supplier B → Rp2.900
└── Supplier C → Rp3.100
```

## Collection `supplier_products`

```json
{
  "_id": "ObjectId",
  "supplierId": "ObjectId",
  "productId": "ObjectId",
  "supplierSku": "BUKU-ABC-001",
  "purchasePrice": 3000,
  "minimumOrder": 10,
  "leadTimeDays": 3,
  "isPreferred": true,
  "isActive": true,
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

---

# 14. Purchase Order

Purchase Order digunakan untuk memesan barang kepada supplier.

## Alur

```text
Buat PO
  ↓
Approval
  ↓
PO Dikirim
  ↓
Supplier Mengirim Barang
  ↓
Penerimaan Barang
```

## Collection `purchase_orders`

```json
{
  "_id": "ObjectId",
  "poNumber": "PO-20260928-0001",
  "supplierId": "ObjectId",
  "items": [
    {
      "productId": "ObjectId",
      "sku": "ATK-001",
      "name": "Buku Tulis",
      "quantity": 100,
      "unitPrice": 3000,
      "subtotal": 300000
    }
  ],
  "subtotal": 300000,
  "discount": 0,
  "tax": 0,
  "shippingCost": 20000,
  "grandTotal": 320000,
  "status": "ORDERED",
  "expectedDeliveryDate": "2026-10-01",
  "createdBy": "ObjectId",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

## Status PO

```text
DRAFT
PENDING_APPROVAL
APPROVED
ORDERED
PARTIALLY_RECEIVED
RECEIVED
COMPLETED
CANCELLED
```

---

# 15. Penerimaan Barang

Penerimaan barang harus terpisah dari PO karena supplier dapat mengirim barang secara sebagian.

Contoh:

```text
PO:
100 Buku

Diterima:
80 Buku

Sisa:
20 Buku
```

## Collection `goods_receipts`

```json
{
  "_id": "ObjectId",
  "receiptNumber": "GR-20260928-0001",
  "purchaseOrderId": "ObjectId",
  "supplierId": "ObjectId",
  "items": [
    {
      "productId": "ObjectId",
      "name": "Buku Tulis",
      "orderedQuantity": 100,
      "receivedQuantity": 80,
      "acceptedQuantity": 78,
      "rejectedQuantity": 2,
      "rejectionReason": "2 barang rusak"
    }
  ],
  "receivedBy": "ObjectId",
  "receivedAt": "Date",
  "notes": "2 buku mengalami kerusakan"
}
```

## Business Rule

Hanya `acceptedQuantity` yang menambah stok.

```text
Stok baru = Stok lama + acceptedQuantity
```

---

# 16. Pembelian

Pembelian merupakan transaksi pengadaan yang tercatat setelah proses penerimaan/pembelian sesuai prosedur koperasi.

## Fitur

- Buat pembelian
- Detail pembelian
- Riwayat pembelian
- Filter supplier
- Filter tanggal
- Status pembayaran

## Collection `purchases`

```json
{
  "_id": "ObjectId",
  "purchaseNumber": "PUR-20260928-0001",
  "supplierId": "ObjectId",
  "purchaseOrderId": "ObjectId",
  "items": [
    {
      "productId": "ObjectId",
      "name": "Buku Tulis",
      "quantity": 78,
      "price": 3000,
      "subtotal": 234000
    }
  ],
  "subtotal": 234000,
  "discount": 0,
  "total": 234000,
  "paymentStatus": "UNPAID",
  "createdBy": "ObjectId",
  "createdAt": "Date"
}
```

---

# 17. Invoice Supplier

Invoice digunakan untuk mencatat tagihan supplier.

## Collection `supplier_invoices`

```json
{
  "_id": "ObjectId",
  "invoiceNumber": "INV-SUP-00125",
  "supplierId": "ObjectId",
  "purchaseOrderId": "ObjectId",
  "receiptId": "ObjectId",
  "invoiceDate": "Date",
  "dueDate": "Date",
  "subtotal": 300000,
  "tax": 33000,
  "shippingCost": 20000,
  "total": 353000,
  "paymentStatus": "UNPAID",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

## Status Pembayaran

```text
UNPAID
PARTIALLY_PAID
PAID
OVERDUE
```

---

# 18. Hutang Supplier

Sistem harus dapat menghitung hutang supplier.

```text
Hutang =
Total Invoice
- Total Pembayaran
```

Contoh:

```text
Invoice       Rp10.000.000
Bayar 1       Rp 5.000.000
---------------------------
Sisa Hutang   Rp 5.000.000
```

---

# 19. Pembayaran Supplier

## Collection `supplier_payments`

```json
{
  "_id": "ObjectId",
  "supplierId": "ObjectId",
  "invoiceId": "ObjectId",
  "paymentNumber": "PAY-SUP-0001",
  "amount": 5000000,
  "method": "BANK_TRANSFER",
  "paymentDate": "Date",
  "referenceNumber": "TRF-123456",
  "createdBy": "ObjectId",
  "notes": "Pembayaran sebagian"
}
```

## Metode

```text
CASH
BANK_TRANSFER
DEBIT
OTHER
```

---

# 20. Inventory

Inventory mengelola kondisi stok.

## Jenis Stock Movement

```text
PURCHASE
SALE
SALE_RETURN
PURCHASE_RETURN
ADJUSTMENT
STOCK_OPNAME
```

## Collection `stock_movements`

```json
{
  "_id": "ObjectId",
  "productId": "ObjectId",
  "type": "SALE",
  "quantity": -2,
  "stockBefore": 50,
  "stockAfter": 48,
  "referenceType": "SALE",
  "referenceId": "ObjectId",
  "createdBy": "ObjectId",
  "createdAt": "Date"
}
```

## Business Rules

Pembelian/penerimaan:

```text
stockAfter = stockBefore + quantity
```

Penjualan:

```text
stockAfter = stockBefore - quantity
```

Sistem tidak boleh mengizinkan stok menjadi negatif.

---

# 21. Stock Opname

Stock opname digunakan untuk mencocokkan stok sistem dengan stok fisik.

## Alur

```text
Mulai Stock Opname
        ↓
Ambil Stok Sistem
        ↓
Hitung Stok Fisik
        ↓
Bandingkan
        ↓
Selisih?
   ┌────┴────┐
  Tidak      Ya
   ↓          ↓
Selesai    Adjustment
```

Data:

```json
{
  "productId": "ObjectId",
  "systemStock": 50,
  "physicalStock": 48,
  "difference": -2,
  "reason": "Barang rusak/tidak ditemukan",
  "createdBy": "ObjectId",
  "createdAt": "Date"
}
```

---

# 22. Anggota Koperasi

## Fitur

- Tambah anggota
- Edit anggota
- Detail anggota
- Status anggota
- Riwayat transaksi
- Total belanja

## Collection `members`

```json
{
  "_id": "ObjectId",
  "memberNumber": "KOP-001",
  "name": "Nama Anggota",
  "phone": "08123456789",
  "email": "member@example.com",
  "address": "Bandung",
  "joinedAt": "Date",
  "status": "ACTIVE",
  "createdAt": "Date",
  "updatedAt": "Date"
}
```

Status:

```text
ACTIVE
INACTIVE
```

---

# 23. Penjualan / POS

POS merupakan modul utama untuk kasir.

## Alur

```text
Scan/Cari Produk
      ↓
Masukkan Keranjang
      ↓
Pilih Anggota (opsional)
      ↓
Hitung Total
      ↓
Pembayaran
      ↓
Transaksi Selesai
      ↓
Stok Berkurang
      ↓
Cetak Struk
```

## Collection `sales`

```json
{
  "_id": "ObjectId",
  "invoiceNumber": "TRX-20260928-0001",
  "cashierId": "ObjectId",
  "memberId": "ObjectId",
  "items": [
    {
      "productId": "ObjectId",
      "sku": "ATK-001",
      "name": "Buku Tulis",
      "quantity": 2,
      "price": 4000,
      "subtotal": 8000
    }
  ],
  "subtotal": 8000,
  "discount": 0,
  "total": 8000,
  "payment": {
    "method": "CASH",
    "amount": 10000,
    "change": 2000
  },
  "status": "COMPLETED",
  "createdAt": "Date"
}
```

## Status

```text
COMPLETED
CANCELLED
```

Transaksi tidak boleh dihapus secara fisik setelah selesai.

---

# 24. Pembayaran Penjualan

Metode:

```text
CASH
TRANSFER
QRIS
DEBIT
E_WALLET
```

Data:

```json
{
  "method": "CASH",
  "amount": 20000,
  "change": 10000,
  "paidAt": "Date"
}
```

---

# 25. Retur Penjualan

## Alur

```text
Cari Transaksi
      ↓
Pilih Item
      ↓
Jumlah Retur
      ↓
Alasan
      ↓
Approval
      ↓
Stok Bertambah
```

Alasan:

```text
BARANG_RUSAK
SALAH_BARANG
SALAH_JUMLAH
LAINNYA
```

---

# 26. Retur Pembelian

Retur pembelian digunakan ketika koperasi mengembalikan barang kepada supplier.

## Alur

```text
Barang Diterima
      ↓
Pemeriksaan
      ↓
Barang Rusak
      ↓
Retur Supplier
      ↓
Stok Berkurang
      ↓
Koreksi Hutang/Invoice jika diperlukan
```

---

# 27. Pengeluaran

Pengeluaran digunakan untuk mencatat biaya operasional.

Contoh:

- Listrik
- Air
- Internet
- Transportasi
- ATK
- Perawatan
- Biaya operasional lainnya

## Collection `expenses`

```json
{
  "_id": "ObjectId",
  "category": "ELECTRICITY",
  "description": "Pembayaran listrik toko",
  "amount": 500000,
  "date": "Date",
  "createdBy": "ObjectId",
  "createdAt": "Date"
}
```

---

# 28. Laporan

## 28.1 Laporan Penjualan

Filter:

- Per hari
- Per minggu
- Per bulan
- Custom date range
- Kasir
- Produk
- Kategori
- Anggota

Menampilkan:

- Jumlah transaksi
- Total barang terjual
- Total penjualan
- Diskon
- Pendapatan

## 28.2 Laporan Pembelian

Menampilkan:

- Supplier
- Jumlah PO
- Jumlah barang
- Total pembelian
- Pembelian berdasarkan periode

## 28.3 Laporan Inventory

Menampilkan:

- Stok saat ini
- Barang hampir habis
- Barang habis
- Stok masuk
- Stok keluar
- Stock adjustment

## 28.4 Laporan Supplier

Menampilkan:

- Total pembelian supplier
- Jumlah PO
- Barang yang disuplai
- Invoice
- Hutang
- Total pembayaran
- Sisa hutang

## 28.5 Laporan Hutang

```text
Supplier | Invoice | Total | Dibayar | Sisa | Jatuh Tempo
```

## 28.6 Laporan Keuangan Dasar

```text
Total Penjualan
- HPP
= Laba Kotor

Laba Kotor
- Pengeluaran
= Laba Bersih
```

Metode HPP harus ditetapkan oleh pengelola sistem sebelum laporan laba digunakan sebagai laporan resmi.

---

# 29. Audit Log

Aktivitas penting dicatat untuk keamanan dan pelacakan.

## Collection `audit_logs`

```json
{
  "_id": "ObjectId",
  "userId": "ObjectId",
  "action": "UPDATE",
  "module": "PRODUCT",
  "referenceId": "ObjectId",
  "description": "Mengubah harga produk",
  "createdAt": "Date"
}
```

Contoh action:

```text
LOGIN
LOGOUT
CREATE
UPDATE
DELETE
SALE
PURCHASE
STOCK_ADJUSTMENT
STOCK_OPNAME
RETURN
APPROVE
PAYMENT
```

---

# 30. Database MongoDB

## Daftar Collection

```text
koperasi_db
│
├── users
├── categories
├── products
├── suppliers
├── supplier_products
├── members
│
├── purchase_orders
├── goods_receipts
├── purchases
├── supplier_invoices
├── supplier_payments
│
├── sales
├── payments
│
├── stock_movements
├── stock_opnames
│
├── returns
├── expenses
└── audit_logs
```

---

# 31. Strategi Embedded vs Reference MongoDB

## Gunakan Embedded Document

Untuk data yang merupakan bagian langsung dari transaksi:

```text
sales.items
purchase_orders.items
purchases.items
goods_receipts.items
```

Contoh:

```json
{
  "items": [
    {
      "productId": "ObjectId",
      "name": "Buku",
      "quantity": 2,
      "price": 4000
    }
  ]
}
```

## Gunakan Reference

Untuk data master:

```text
supplierId
productId
categoryId
memberId
userId
cashierId
```

Alasan utama:

- Data master sering digunakan lintas transaksi.
- Transaksi membutuhkan referensi terhadap master.
- Snapshot nama, SKU, dan harga tetap disimpan dalam item transaksi agar histori tidak berubah.

---

# 32. Index MongoDB

Index yang disarankan:

## `products`

```text
sku: unique
barcode: unique
categoryId: index
name: text
```

## `users`

```text
username: unique
email: unique
role: index
```

## `members`

```text
memberNumber: unique
name: index
```

## `suppliers`

```text
supplierCode: unique
name: index
```

## `sales`

```text
invoiceNumber: unique
cashierId: index
memberId: index
createdAt: index
```

## `purchase_orders`

```text
poNumber: unique
supplierId: index
status: index
createdAt: index
```

## `supplier_invoices`

```text
invoiceNumber: unique
supplierId: index
paymentStatus: index
dueDate: index
```

---

# 33. REST API

## Authentication

```http
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
PUT  /api/auth/password
```

## Users

```http
GET    /api/users
POST   /api/users
GET    /api/users/:id
PUT    /api/users/:id
DELETE /api/users/:id
```

## Products

```http
GET    /api/products
POST   /api/products
GET    /api/products/:id
PUT    /api/products/:id
DELETE /api/products/:id
GET    /api/products/barcode/:barcode
```

## Categories

```http
GET    /api/categories
POST   /api/categories
PUT    /api/categories/:id
DELETE /api/categories/:id
```

## Suppliers

```http
GET    /api/suppliers
POST   /api/suppliers
GET    /api/suppliers/:id
PUT    /api/suppliers/:id
DELETE /api/suppliers/:id
GET    /api/suppliers/:id/products
GET    /api/suppliers/:id/purchase-orders
GET    /api/suppliers/:id/invoices
GET    /api/suppliers/:id/payments
```

## Supplier Products

```http
GET    /api/supplier-products
POST   /api/supplier-products
PUT    /api/supplier-products/:id
DELETE /api/supplier-products/:id
```

## Members

```http
GET    /api/members
POST   /api/members
GET    /api/members/:id
PUT    /api/members/:id
DELETE /api/members/:id
GET    /api/members/:id/transactions
```

## Purchase Orders

```http
GET  /api/purchase-orders
POST /api/purchase-orders
GET  /api/purchase-orders/:id
PUT  /api/purchase-orders/:id
POST /api/purchase-orders/:id/approve
POST /api/purchase-orders/:id/cancel
```

## Goods Receipt

```http
GET  /api/goods-receipts
POST /api/goods-receipts
GET  /api/goods-receipts/:id
```

## Purchases

```http
GET  /api/purchases
POST /api/purchases
GET  /api/purchases/:id
```

## Supplier Invoices

```http
GET  /api/supplier-invoices
POST /api/supplier-invoices
GET  /api/supplier-invoices/:id
```

## Supplier Payments

```http
GET  /api/supplier-payments
POST /api/supplier-payments
```

## Inventory

```http
GET  /api/inventory
GET  /api/inventory/:productId
GET  /api/inventory/movements
POST /api/inventory/adjustment
POST /api/inventory/stock-opname
```

## Sales

```http
GET  /api/sales
POST /api/sales
GET  /api/sales/:id
POST /api/sales/:id/cancel
```

## Returns

```http
GET  /api/returns
POST /api/returns/sales
POST /api/returns/purchases
GET  /api/returns/:id
```

## Expenses

```http
GET    /api/expenses
POST   /api/expenses
GET    /api/expenses/:id
PUT    /api/expenses/:id
DELETE /api/expenses/:id
```

## Reports

```http
GET /api/reports/dashboard
GET /api/reports/sales
GET /api/reports/purchases
GET /api/reports/inventory
GET /api/reports/suppliers
GET /api/reports/payables
GET /api/reports/profit
```

---

# 34. Business Rules

## BR-01 — Stok

Pembelian/penerimaan:

```text
stok = stok lama + acceptedQuantity
```

Penjualan:

```text
stok = stok lama - quantity
```

Retur penjualan:

```text
stok = stok lama + quantity
```

Retur pembelian:

```text
stok = stok lama - quantity
```

## BR-02 — Stok Tidak Boleh Minus

Jika:

```text
stock = 5
quantity = 6
```

transaksi penjualan harus ditolak.

## BR-03 — Harga Historis

Harga transaksi harus disimpan di transaksi.

Jika harga produk berubah dari Rp5.000 menjadi Rp6.000, transaksi lama tetap menyimpan harga Rp5.000.

## BR-04 — Invoice Unik

Format invoice:

```text
TRX-YYYYMMDD-NNNN
```

Contoh:

```text
TRX-20260928-0001
```

## BR-05 — Purchase Order

Membuat PO tidak langsung menambah stok.

Stok hanya bertambah setelah barang diterima dan dinyatakan diterima/accepted.

## BR-06 — Penerimaan Sebagian

Jika:

```text
Ordered = 100
Received = 80
```

maka:

```text
Received = 80
Remaining = 20
Status = PARTIALLY_RECEIVED
```

## BR-07 — Pembatalan Penjualan

Transaksi selesai tidak boleh dihapus.

Gunakan:

```text
status = CANCELLED
```

dan buat stock movement pembalik jika stok sudah dikurangi.

## BR-08 — Pembayaran Supplier

```text
Sisa Hutang =
Total Invoice - Total Pembayaran
```

Jika sisa = 0:

```text
paymentStatus = PAID
```

Jika sisa > 0:

```text
paymentStatus = PARTIALLY_PAID
```

## BR-09 — Produk Tidak Dihapus Permanen

Produk yang pernah digunakan transaksi sebaiknya:

```text
isActive = false
```

bukan hard delete.

---

# 35. Non-Functional Requirements

## Performance

Target:

- API normal < 500 ms.
- Pencarian produk < 500 ms.
- Dashboard < 2 detik pada dataset normal.
- Pagination wajib digunakan pada data besar.

## Security

- Password menggunakan bcrypt/Argon2.
- Authentication menggunakan token/session yang aman.
- Authorization berbasis role.
- Validasi input.
- Rate limit login.
- Audit log.
- HTTPS pada production.
- Jangan menyimpan password plaintext.
- Data sensitif tidak ditampilkan kepada role yang tidak berhak.

## Reliability

Transaksi penjualan dan perubahan stok harus diproses secara konsisten.

Untuk operasi yang melibatkan beberapa dokumen penting, gunakan MongoDB transaction/session bila deployment MongoDB mendukungnya.

Contoh transaksi penjualan:

```text
START TRANSACTION
    ↓
Validasi stok
    ↓
Simpan sales
    ↓
Kurangi stock
    ↓
Simpan stock movement
    ↓
Simpan audit log
    ↓
COMMIT
```

Jika salah satu proses gagal:

```text
ROLLBACK
```

---

# 36. UI Pages

```text
/login

/dashboard

/users
/users/create
/users/:id/edit

/products
/products/create
/products/:id
/products/:id/edit

/categories

/suppliers
/suppliers/create
/suppliers/:id
/suppliers/:id/edit
/suppliers/:id/products

/members
/members/create
/members/:id
/members/:id/edit

/purchase-orders
/purchase-orders/create
/purchase-orders/:id

/goods-receipts
/goods-receipts/create
/goods-receipts/:id

/purchases
/purchases/:id

/supplier-invoices
/supplier-invoices/:id

/supplier-payments

/inventory
/inventory/movements
/inventory/stock-opname

/pos

/sales
/sales/:id

/returns

/expenses

/reports/sales
/reports/purchases
/reports/inventory
/reports/suppliers
/reports/payables
/reports/profit

/audit-logs

/profile
```

---

# 37. Alur Bisnis Utama

## 37.1 Pengadaan Barang

```text
Pengurus
   ↓
Pilih Supplier
   ↓
Buat PO
   ↓
Approval
   ↓
PO dikirim
   ↓
Supplier mengirim barang
   ↓
Barang diterima
   ↓
Pemeriksaan
   ↓
Barang diterima baik
   ↓
Stok bertambah
   ↓
Invoice
   ↓
Hutang
   ↓
Pembayaran
```

## 37.2 Penjualan

```text
Kasir
  ↓
Scan Produk
  ↓
Keranjang
  ↓
Validasi Stok
  ↓
Pembayaran
  ↓
Sales Created
  ↓
Stock Decreased
  ↓
Stock Movement
  ↓
Struk
```

## 37.3 Retur Supplier

```text
Barang Rusak
     ↓
Identifikasi PO/Receipt
     ↓
Buat Retur
     ↓
Approval
     ↓
Stok Berkurang
     ↓
Supplier menerima retur
     ↓
Koreksi invoice/hutang bila diperlukan
```

---

# 38. Struktur Arsitektur

```text
┌─────────────────────────────────────┐
│             FRONTEND                │
│                                     │
│       Vue 3 + TypeScript            │
│           Tailwind CSS              │
│                                     │
└────────────────┬────────────────────┘
                 │
                 │ REST API / JSON
                 ▼
┌─────────────────────────────────────┐
│              BACKEND                │
│                                     │
│       Python + FAST API             │
│                                     │
│ ┌───────────┐ ┌──────────────────┐ │
│ │Auth       │ │Authorization     │ │
│ ├───────────┤ ├──────────────────┤ │
│ │Products   │ │Procurement       │ │
│ │Sales      │ │Inventory         │ │
│ │Reports    │ │Supplier          │ │
│ └───────────┘ └──────────────────┘ │
│                                     │
└────────────────┬────────────────────┘
                 │
              Mongoose
                 │
                 ▼
┌─────────────────────────────────────┐
│              MongoDB                │
│                                     │
│ users                               │
│ products                            │
│ suppliers                           │
│ purchase_orders                     │
│ goods_receipts                      │
│ sales                               │
│ stock_movements                     │
│ invoices                            │
│ payments                            │
│ etc.                                │
└─────────────────────────────────────┘
```


# 40. Struktur Frontend yang Disarankan

```text
frontend/
├── src/
│   ├── components/
│   ├── layouts/
│   ├── pages/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── suppliers/
│   │   ├── members/
│   │   ├── purchases/
│   │   ├── inventory/
│   │   ├── sales/
│   │   ├── reports/
│   │   └── users/
│   │
│   ├── services/
│   │   └── api.ts
│   ├── stores/
│   ├── router/
│   ├── types/
│   └── utils/
│
└── main.ts
```

---

# 41. Prioritas Pengembangan

## Phase 1 — Foundation

- [ ] Project setup
- [ ] MongoDB connection
- [ ] Authentication
- [ ] User
- [ ] Role & permission
- [ ] Layout
- [ ] Dashboard dasar

## Phase 2 — Master Data

- [ ] Produk
- [ ] Kategori
- [ ] Supplier
- [ ] Produk Supplier
- [ ] Anggota

## Phase 3 — Procurement

- [ ] Purchase Order
- [ ] Approval PO
- [ ] Goods Receipt
- [ ] Pembelian
- [ ] Supplier Invoice
- [ ] Hutang
- [ ] Supplier Payment

## Phase 4 — Inventory

- [ ] Stock movement
- [ ] Stock adjustment
- [ ] Stock opname
- [ ] Stok minimum
- [ ] Notifikasi stok

## Phase 5 — Sales

- [ ] POS
- [ ] Cart
- [ ] Barcode
- [ ] Pembayaran
- [ ] Struk
- [ ] Riwayat penjualan

## Phase 6 — Retur & Keuangan

- [ ] Retur penjualan
- [ ] Retur pembelian
- [ ] Pengeluaran
- [ ] Hutang supplier

## Phase 7 — Reporting

- [ ] Dashboard analytics
- [ ] Laporan penjualan
- [ ] Laporan pembelian
- [ ] Laporan inventory
- [ ] Laporan supplier
- [ ] Laporan hutang
- [ ] Laporan laba dasar
- [ ] Export PDF/Excel

## Phase 8 — Security & Audit

- [ ] Audit log
- [ ] Permission refinement
- [ ] Rate limiting
- [ ] Security validation
- [ ] Backup strategy

---

# 42. Acceptance Criteria MVP

## Authentication

- [ ] User dapat login.
- [ ] User dapat logout.
- [ ] Role membatasi akses halaman dan API.
- [ ] Password tersimpan secara aman.

## Master Data

- [ ] Admin dapat CRUD produk.
- [ ] Admin dapat CRUD kategori.
- [ ] Admin dapat CRUD supplier.
- [ ] Admin dapat CRUD anggota.
- [ ] Produk memiliki SKU/barcode unik.

## Procurement

- [ ] Pengurus dapat membuat PO.
- [ ] PO memiliki status.
- [ ] PO dapat di-approve.
- [ ] Barang dapat diterima sebagian.
- [ ] Hanya barang yang diterima baik yang menambah stok.
- [ ] Invoice supplier dapat dibuat.
- [ ] Hutang supplier dapat dihitung.
- [ ] Pembayaran supplier dapat dicatat.

## Inventory

- [ ] Stok bertambah ketika barang diterima.
- [ ] Stok berkurang ketika barang terjual.
- [ ] Stock movement tercatat.
- [ ] Stock opname dapat dilakukan.
- [ ] Sistem mencegah stok minus.

## Sales

- [ ] Kasir dapat mencari produk.
- [ ] Kasir dapat melakukan transaksi.
- [ ] Kasir dapat memilih anggota.
- [ ] Sistem menghitung total.
- [ ] Sistem memproses pembayaran.
- [ ] Sistem menghitung kembalian.
- [ ] Stok otomatis berkurang.
- [ ] Struk dapat dicetak.

## Reporting

- [ ] Pengurus dapat melihat penjualan.
- [ ] Pengurus dapat melihat pembelian.
- [ ] Pengurus dapat melihat stok.
- [ ] Pengurus dapat melihat supplier.
- [ ] Pengurus dapat melihat hutang.
- [ ] Pengurus dapat melihat laporan laba dasar.

## Audit

- [ ] Login tercatat.
- [ ] Perubahan data penting tercatat.
- [ ] Penyesuaian stok tercatat.
- [ ] Pembatalan transaksi tercatat.
- [ ] Pembayaran supplier tercatat.

---

# 43. Pengembangan Lanjutan

Setelah MVP stabil, sistem dapat dikembangkan dengan:

- Barcode scanner fisik.
- QRIS.
- Printer thermal.
- Export Excel.
- Export PDF.
- Notifikasi stok minimum.
- Notifikasi invoice jatuh tempo.
- Multi-gudang.
- Multi-cabang.
- Integrasi akuntansi.
- Perhitungan SHU.
- Membership/loyalty.
- Dashboard analitik.
- Forecasting kebutuhan stok.
- Supplier performance monitoring.
- Mobile application.
- Progressive Web App.

---

# 44. Kesimpulan

Sistem Informasi Toko Koperasi dirancang sebagai sistem terintegrasi yang menangani dua alur utama:

### Alur Pengadaan

```text
Supplier
   ↓
Purchase Order
   ↓
Penerimaan Barang
   ↓
Inventory
   ↓
Invoice
   ↓
Hutang
   ↓
Pembayaran
```

### Alur Penjualan

```text
Inventory
   ↓
POS
   ↓
Penjualan
   ↓
Pembayaran
   ↓
Stock Movement
   ↓
Laporan
```

MongoDB digunakan dengan pendekatan **hybrid embedding dan referencing**. Detail item transaksi di-embed untuk menjaga snapshot historis, sedangkan data master seperti produk, supplier, user, anggota, dan kategori menggunakan reference.

Desain ini memungkinkan sistem dikembangkan secara bertahap dari toko koperasi sederhana menjadi sistem pengelolaan koperasi yang lebih lengkap.

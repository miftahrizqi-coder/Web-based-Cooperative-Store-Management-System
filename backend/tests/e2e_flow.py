"""
Uji end-to-end alur bisnis utama terhadap API yang sedang berjalan.

Prasyarat:
  1. Database kosong khusus uji, mis. MONGODB_DATABASE=koperasi_e2e
  2. python -m app.seed --demo
  3. uvicorn app.main:app --port 8001
  4. E2E_BASE_URL=http://127.0.0.1:8001 python tests/e2e_flow.py

Setiap langkah memverifikasi acceptance criteria PRD §42 dan business rule
BR-01..BR-09. Skrip berhenti di assertion pertama yang gagal.
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone

import httpx


BASE = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8001")
PASSWORDS = {
    "admin": os.getenv("SEED_ADMIN_PASSWORD", "Admin12345!"),
    "kasir": "Kasir12345!",
    "pengurus": "Pengurus12345!",
    "anggota": "Anggota12345!",
}

passed = 0


def check(condition: bool, message: str, detail=None) -> None:
    global passed
    if not condition:
        print(f"  FAIL  {message}")
        if detail is not None:
            print(f"        {detail}")
        sys.exit(1)
    passed += 1
    print(f"  ok    {message}")


class Api:
    def __init__(self, token: str | None = None):
        self.client = httpx.Client(base_url=BASE, timeout=30)
        self.token = token

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def get(self, path, **params):
        return self.client.get(path, params=params or None, headers=self._headers())

    def post(self, path, json=None):
        return self.client.post(path, json=json, headers=self._headers())

    def put(self, path, json=None):
        return self.client.put(path, json=json, headers=self._headers())

    def delete(self, path, **params):
        return self.client.delete(path, params=params or None, headers=self._headers())


def login(username: str, password: str | None = None) -> Api:
    api = Api()
    response = api.post("/api/auth/login", {"username": username, "password": password or PASSWORDS[username]})
    check(response.status_code == 200, f"login {username}", response.text)
    body = response.json()
    check(
        set(body) >= {"user", "token"} and {"id", "name", "role"} <= set(body["user"]),
        f"format respons login {username} (PRD §8)",
    )
    api.token = body["token"]
    return api


def now_iso(days: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def stock_of(api: Api, product_id: str) -> float:
    return api.get(f"/api/products/{product_id}").json()["stock"]


def main() -> None:
    print(f"E2E terhadap {BASE}")

    # ------------------------------------------------------------------
    print("\n[1] Authentication & otorisasi")
    admin = login("admin")
    kasir = login("kasir")
    pengurus = login("pengurus")
    anggota = login("anggota")

    r = Api().post("/api/auth/login", {"username": "admin", "password": "salah"})
    check(r.status_code == 401, "password salah ditolak")
    check(Api().get("/api/auth/me").status_code == 401, "tanpa token ditolak")
    check(kasir.get("/api/users").status_code == 403, "kasir tidak boleh akses user management")
    check(anggota.get("/api/products").status_code == 403, "anggota tidak boleh akses produk")
    check(pengurus.get("/api/audit-logs").status_code == 403, "pengurus tidak boleh akses audit log")

    for _ in range(5):
        Api().post("/api/auth/login", {"username": "ratelimit-user", "password": "x"})
    r = Api().post("/api/auth/login", {"username": "ratelimit-user", "password": "x"})
    check(r.status_code == 429, "rate limit login setelah 5 kali gagal (PRD §35)")

    temp = login("admin")
    check(temp.post("/api/auth/logout").status_code == 200, "logout")
    check(temp.get("/api/auth/me").status_code == 401, "token yang sudah logout tidak berlaku")

    # user baru + ubah password + reset password
    r = admin.post("/api/users", {"username": "kasir2", "email": "kasir2@example.com", "password": "Kasir2Pass!", "name": "Kasir Dua", "role": "kasir"})
    check(r.status_code == 201, "admin membuat user", r.text)
    kasir2_id = r.json()["id"]
    r = admin.post("/api/users", {"username": "x-anggota", "email": "xa@example.com", "password": "Anggota12345!", "name": "X", "role": "anggota"})
    check(r.status_code == 422, "akun anggota wajib ditautkan ke data anggota")
    kasir2 = login("kasir2", "Kasir2Pass!")
    r = kasir2.put("/api/auth/password", {"current_password": "Kasir2Pass!", "new_password": "Kasir2Baru!"})
    check(r.status_code == 200 and "token" in r.json(), "ubah password")
    check(kasir2.get("/api/auth/me").status_code == 401, "token lama tidak berlaku setelah ubah password")
    r = admin.post(f"/api/users/{kasir2_id}/reset-password", {"new_password": "Kasir2Reset!"})
    check(r.status_code == 200, "admin reset password")
    kasir2 = login("kasir2", "Kasir2Reset!")

    # ------------------------------------------------------------------
    print("\n[2] Master data: kategori & produk")
    r = admin.post("/api/categories", {"name": "Kebersihan", "description": "Sabun dll"})
    check(r.status_code == 201, "tambah kategori", r.text)
    category_id = r.json()["id"]
    check(admin.post("/api/categories", {"name": "kebersihan"}).status_code == 409, "nama kategori unik (case-insensitive)")

    product_payload = {
        "sku": "KBR-001", "barcode": "8990000000001", "name": "Sabun Cuci", "categoryId": category_id,
        "unit": "pcs", "purchasePrice": 5000, "sellingPrice": 6500, "minimumStock": 5, "stock": 20,
    }
    r = admin.post("/api/products", product_payload)
    check(r.status_code == 201, "tambah produk dengan stok awal", r.text)
    product = r.json()
    pid = product["id"]
    check(product["stock"] == 20, "stok awal tersimpan")
    moves = admin.get("/api/inventory/movements", productId=pid).json()
    check(len(moves) == 1 and moves[0]["type"] == "ADJUSTMENT" and moves[0]["quantity"] == 20, "stok awal tercatat sebagai stock movement")

    check(admin.post("/api/products", {**product_payload, "barcode": "8990000000009"}).status_code == 409, "SKU unik (BR)")
    check(admin.post("/api/products", {**product_payload, "sku": "KBR-999"}).status_code == 409, "barcode unik (BR)")
    check(admin.post("/api/products", {**product_payload, "sku": "KBR-998", "barcode": None, "sellingPrice": -1}).status_code == 422, "harga negatif ditolak")
    check(kasir.post("/api/products", {**product_payload, "sku": "KBR-997", "barcode": None}).status_code == 403, "kasir tidak boleh tambah produk")
    check(kasir.put(f"/api/products/{pid}", {**product_payload, "sellingPrice": 1}).status_code == 403, "kasir tidak boleh ubah harga")
    check(kasir.delete(f"/api/products/{pid}").status_code == 403, "kasir tidak boleh hapus produk")

    r = admin.put(f"/api/products/{pid}", {**product_payload, "stock": 999, "sellingPrice": 7000, "isActive": True})
    check(r.status_code == 200 and r.json()["stock"] == 20 and r.json()["sellingPrice"] == 7000, "edit produk tidak mengubah stok (stok hanya via movement)")

    r = kasir.get(f"/api/products/{pid}")
    check(r.json()["purchasePrice"] is None, "harga beli disembunyikan dari kasir")
    r = kasir.get(f"/api/products/barcode/8990000000001")
    check(r.status_code == 200 and r.json()["id"] == pid, "cari produk via barcode")
    r = kasir.get("/api/products", search="sabun")
    check(any(p["id"] == pid for p in r.json()), "pencarian produk")
    r = admin.get("/api/products", categoryId=category_id)
    check([p["id"] for p in r.json()] == [pid], "filter produk per kategori")
    r = admin.get("/api/products", page=1, pageSize=2)
    check(len(r.json()) <= 2 and int(r.headers["X-Total-Count"]) >= 5, "pagination + X-Total-Count")
    check(admin.delete(f"/api/products/{pid}", permanent="true").status_code == 409, "produk dengan riwayat tidak bisa dihapus permanen (BR-09)")

    # ------------------------------------------------------------------
    print("\n[3] Supplier & produk supplier")
    suppliers = pengurus.get("/api/suppliers").json()
    supplier = next(s for s in suppliers if s["supplierCode"] == "SUP-001")
    sid = supplier["id"]
    check(kasir.get("/api/suppliers").status_code == 403, "kasir tidak boleh kelola supplier")

    r = pengurus.post("/api/supplier-products", {
        "supplierId": sid, "productId": pid, "supplierSku": "ABC-SBN", "purchasePrice": 4800,
        "minimumOrder": 10, "leadTimeDays": 2, "isPreferred": True,
    })
    check(r.status_code == 201, "hubungkan produk ke supplier", r.text)
    sp_id = r.json()["id"]
    check(len(pengurus.get(f"/api/suppliers/{sid}/products").json()) >= 1, "GET /suppliers/:id/products")

    # ------------------------------------------------------------------
    print("\n[4] Pengadaan: PO -> approval -> penerimaan sebagian -> invoice -> pembayaran")
    r = pengurus.post("/api/purchase-orders", {"supplierId": sid, "items": [{"supplierProductId": sp_id, "quantity": 5}]})
    check(r.status_code == 422, "qty di bawah minimum order ditolak")
    r = pengurus.post("/api/purchase-orders", {
        "supplierId": sid, "items": [{"supplierProductId": sp_id, "productId": pid, "sku": "PALSU", "name": "PALSU", "quantity": 100}],
        "shippingCost": 20000, "expectedDeliveryDate": now_iso(3),
    })
    check(r.status_code == 201, "pengurus membuat PO", r.text)
    po = r.json()
    po_id = po["id"]
    check(re.fullmatch(r"PO-\d{8}-\d{4}", po["poNumber"]) is not None, "format nomor PO")
    check(po["items"][0]["sku"] == "KBR-001" and po["items"][0]["unitPrice"] == 4800, "snapshot SKU & harga dari master (payload client diabaikan)")
    check(po["grandTotal"] == 100 * 4800 + 20000, "grand total PO")
    check(po["status"] == "DRAFT", "PO awal DRAFT")
    check(stock_of(admin, pid) == 20, "membuat PO tidak menambah stok (BR-05)")

    check(pengurus.post(f"/api/purchase-orders/{po_id}/approve").status_code == 409, "PO DRAFT tidak bisa langsung approve")
    check(pengurus.post(f"/api/purchase-orders/{po_id}/submit").json()["status"] == "PENDING_APPROVAL", "submit PO")
    check(pengurus.post(f"/api/purchase-orders/{po_id}/approve").status_code == 403, "pembuat PO tidak bisa approve PO sendiri")
    check(admin.post(f"/api/purchase-orders/{po_id}/approve").json()["status"] == "APPROVED", "admin approve PO")
    r = pengurus.post("/api/goods-receipts", {"purchaseOrderId": po_id, "items": [{"productId": pid, "receivedQuantity": 1, "acceptedQuantity": 1, "rejectedQuantity": 0}]})
    check(r.status_code == 409, "barang tidak bisa diterima sebelum PO ORDERED")
    check(pengurus.post(f"/api/purchase-orders/{po_id}/order").json()["status"] == "ORDERED", "PO dikirim ke supplier")

    r = pengurus.post("/api/goods-receipts", {"purchaseOrderId": po_id, "items": [
        {"productId": pid, "receivedQuantity": 80, "acceptedQuantity": 78, "rejectedQuantity": 2}
    ]})
    check(r.status_code == 422, "barang ditolak wajib ada alasan")
    r = pengurus.post("/api/goods-receipts", {"purchaseOrderId": po_id, "notes": "2 buku rusak", "items": [
        {"productId": pid, "receivedQuantity": 80, "acceptedQuantity": 78, "rejectedQuantity": 2, "rejectionReason": "2 barang rusak"}
    ]})
    check(r.status_code == 201, "penerimaan sebagian", r.text)
    gr1 = r.json()
    check(stock_of(admin, pid) == 20 + 78, "hanya acceptedQuantity yang menambah stok (PRD §15)")
    po = pengurus.get(f"/api/purchase-orders/{po_id}").json()
    check(po["status"] == "PARTIALLY_RECEIVED" and po["items"][0]["remainingQuantity"] == 20, "BR-06: status PARTIALLY_RECEIVED, sisa 20")

    r = pengurus.post("/api/goods-receipts", {"purchaseOrderId": po_id, "items": [
        {"productId": pid, "receivedQuantity": 21, "acceptedQuantity": 21, "rejectedQuantity": 0}
    ]})
    check(r.status_code == 422, "penerimaan melebihi sisa PO ditolak")
    check(pengurus.post(f"/api/purchase-orders/{po_id}/cancel").status_code == 409, "PO yang sudah ada penerimaan tidak bisa dibatalkan")

    r = pengurus.post("/api/goods-receipts", {"purchaseOrderId": po_id, "items": [
        {"productId": pid, "receivedQuantity": 20, "acceptedQuantity": 20, "rejectedQuantity": 0}
    ]})
    check(r.status_code == 201, "penerimaan sisa")
    gr2 = r.json()
    check(pengurus.get(f"/api/purchase-orders/{po_id}").json()["status"] == "RECEIVED", "PO RECEIVED")
    check(stock_of(admin, pid) == 118, "stok setelah penerimaan kedua")

    r = pengurus.post("/api/purchases", {"receiptId": gr1["id"]})
    check(r.status_code == 201 and r.json()["total"] == 78 * 4800, "pembelian dari GR1 (qty accepted)", r.text)
    check(pengurus.post("/api/purchases", {"receiptId": gr1["id"]}).status_code == 409, "pembelian ganda ditolak")
    r = pengurus.post("/api/supplier-invoices", {"receiptId": gr1["id"], "invoiceNumber": "INV-SUP-00125", "invoiceDate": now_iso(), "tax": 0, "shippingCost": 20000})
    check(r.status_code == 201, "invoice supplier", r.text)
    invoice = r.json()
    inv_id = invoice["id"]
    check(invoice["total"] == 78 * 4800 + 20000 and invoice["outstanding"] == invoice["total"], "total invoice & hutang")
    due_diff = datetime.fromisoformat(invoice["dueDate"]) - datetime.fromisoformat(invoice["invoiceDate"])
    check(abs(due_diff.days - 30) <= 1, "jatuh tempo default = termin supplier (30 hari)")

    total = invoice["total"]
    check(pengurus.post("/api/supplier-payments", {"invoiceId": inv_id, "amount": total + 1, "method": "BANK_TRANSFER", "paymentDate": now_iso()}).status_code == 422, "pembayaran melebihi hutang ditolak")
    r = pengurus.post("/api/supplier-payments", {"invoiceId": inv_id, "amount": 200000, "method": "BANK_TRANSFER", "paymentDate": now_iso(), "referenceNumber": "TRF-1"})
    check(r.status_code == 201 and re.fullmatch(r"PAY-SUP-\d{8}-\d{4}", r.json()["paymentNumber"]) is not None, "pembayaran sebagian", r.text)
    inv = pengurus.get(f"/api/supplier-invoices/{inv_id}").json()
    check(inv["paymentStatus"] == "PARTIALLY_PAID" and inv["outstanding"] == total - 200000, "BR-08: sisa hutang & PARTIALLY_PAID")

    # Retur pembelian 3 pcs dari GR1 -> stok berkurang, hutang terkoreksi
    r = pengurus.post("/api/returns/purchases", {"receiptId": gr1["id"], "items": [{"productId": pid, "quantity": 79}], "reason": "BARANG_RUSAK"})
    check(r.status_code == 422, "retur pembelian melebihi qty diterima ditolak")
    r = pengurus.post("/api/returns/purchases", {"receiptId": gr1["id"], "items": [{"productId": pid, "quantity": 3}], "reason": "BARANG_RUSAK", "notes": "rusak saat pemeriksaan"})
    check(r.status_code == 201 and r.json()["status"] == "PENDING_APPROVAL", "pengajuan retur pembelian")
    rtp = r.json()
    check(stock_of(admin, pid) == 118, "stok belum berubah sebelum approval retur")
    check(pengurus.post(f"/api/returns/{rtp['id']}/approve").status_code == 403, "pengaju retur tidak bisa approve sendiri")
    r = admin.post(f"/api/returns/{rtp['id']}/approve")
    check(r.status_code == 200 and r.json()["status"] == "APPROVED", "admin approve retur pembelian", r.text)
    check(stock_of(admin, pid) == 115, "retur pembelian mengurangi stok (BR-01)")
    inv = pengurus.get(f"/api/supplier-invoices/{inv_id}").json()
    check(inv["returnedAmount"] == 3 * 4800 and inv["outstanding"] == total - 200000 - 3 * 4800, "hutang terkoreksi oleh retur pembelian")

    r = pengurus.post("/api/supplier-payments", {"invoiceId": inv_id, "amount": inv["outstanding"], "method": "CASH", "paymentDate": now_iso()})
    check(r.status_code == 201, "pelunasan")
    inv = pengurus.get(f"/api/supplier-invoices/{inv_id}").json()
    check(inv["paymentStatus"] == "PAID" and inv["outstanding"] == 0, "BR-08: PAID saat sisa = 0")
    check(pengurus.get(f"/api/purchases", supplierId=sid).json()[0]["paymentStatus"] in {"PAID", "UNPAID"}, "filter pembelian per supplier")
    check(pengurus.post(f"/api/purchase-orders/{po_id}/complete").json()["status"] == "COMPLETED", "PO diselesaikan (COMPLETED)")
    summary = pengurus.get(f"/api/suppliers/{sid}/summary").json()
    check(summary["outstanding"] == 0 and summary["totalPaid"] > 0, "ringkasan hutang supplier")

    # ------------------------------------------------------------------
    print("\n[5] Penjualan / POS")
    members = kasir.get("/api/members", search="Siti").json()
    member_id = members[0]["id"]
    before = stock_of(admin, pid)

    r = kasir.post("/api/sales", {"items": [{"productId": pid, "quantity": before + 1}], "payment": {"method": "CASH", "amount": 10**9}})
    check(r.status_code == 409, "BR-02: penjualan melebihi stok ditolak")
    check(stock_of(admin, pid) == before, "stok tidak berubah saat transaksi ditolak")
    r = kasir.post("/api/sales", {"items": [{"productId": pid, "quantity": 2}], "payment": {"method": "CASH", "amount": 1000}})
    check(r.status_code == 400, "uang tunai kurang ditolak")
    r = kasir.post("/api/sales", {"items": [{"productId": pid, "quantity": 2}], "payment": {"method": "QRIS", "amount": 1}})
    check(r.status_code == 400, "non-tunai harus sama dengan total")
    check(pengurus.post("/api/sales", {"items": [{"productId": pid, "quantity": 1}], "payment": {"method": "QRIS"}}).status_code == 403, "pengurus tidak membuat transaksi POS")

    r = kasir.post("/api/sales", {
        "items": [{"productId": pid, "quantity": 2}, {"productId": pid, "quantity": 1}],
        "memberId": member_id, "discount": 1000,
        "payment": {"method": "CASH", "amount": 50000},
    })
    check(r.status_code == 201, "transaksi penjualan dengan anggota", r.text)
    sale = r.json()
    check(re.fullmatch(r"TRX-\d{8}-\d{4}", sale["invoiceNumber"]) is not None, "BR-04: format invoice TRX-YYYYMMDD-NNNN")
    check(len(sale["items"]) == 1 and sale["items"][0]["quantity"] == 3, "item duplikat di keranjang digabung")
    check(sale["subtotal"] == 21000 and sale["total"] == 20000, "hitung subtotal & diskon")
    check(sale["payment"]["change"] == 30000, "hitung kembalian")
    check(sale["status"] == "COMPLETED" and sale["items"][0]["costPrice"] is None, "status COMPLETED; HPP tidak tampil ke kasir")
    check(stock_of(admin, pid) == before - 3, "stok berkurang otomatis")
    moves = admin.get("/api/inventory/movements", referenceId=sale["id"]).json()
    check(moves and moves[0]["type"] == "SALE" and moves[0]["quantity"] == -3 and moves[0]["stockAfter"] == moves[0]["stockBefore"] - 3, "stock movement penjualan (quantity negatif)")

    # BR-03: harga historis
    admin.put(f"/api/products/{pid}", {**product_payload, "sellingPrice": 9000, "isActive": True})
    check(kasir.get(f"/api/sales/{sale['id']}").json()["items"][0]["price"] == 7000, "BR-03: harga lama tetap di transaksi")

    r = kasir2.post("/api/sales", {"items": [{"productId": pid, "quantity": 1}], "payment": {"method": "QRIS"}})
    check(r.status_code == 201, "transaksi kasir lain (QRIS)")
    other_sale = r.json()
    check(all(s["cashierId"] == sale["cashierId"] for s in kasir.get("/api/sales").json()), "kasir hanya melihat transaksi sendiri")
    check(kasir.get(f"/api/sales/{other_sale['id']}").status_code == 403, "kasir tidak bisa buka transaksi kasir lain")

    # Retur penjualan
    r = kasir.post("/api/returns/sales", {"invoiceNumber": sale["invoiceNumber"], "items": [{"productId": pid, "quantity": 4}], "reason": "BARANG_RUSAK"})
    check(r.status_code == 422, "retur melebihi qty terjual ditolak")
    r = kasir.post("/api/returns/sales", {"saleId": sale["id"], "items": [{"productId": pid, "quantity": 1}], "reason": "SALAH_BARANG"})
    check(r.status_code == 201, "kasir mengajukan retur penjualan", r.text)
    rts = r.json()
    check(kasir.post(f"/api/returns/{rts['id']}/approve").status_code == 403, "kasir tidak bisa approve retur")
    check(admin.post(f"/api/sales/{sale['id']}/cancel").status_code == 409, "batal ditolak saat ada retur pending")
    s_before = stock_of(admin, pid)
    r = pengurus.post(f"/api/returns/{rts['id']}/approve")
    check(r.status_code == 200, "pengurus approve retur penjualan", r.text)
    check(stock_of(admin, pid) == s_before + 1, "retur penjualan menambah stok (BR-01)")
    check(rts["totalAmount"] == round(7000 * 20000 / 21000, 2), "nilai refund memperhitungkan diskon")

    # Pembatalan (BR-07)
    check(kasir.post(f"/api/sales/{sale['id']}/cancel").status_code == 403, "kasir tidak bisa membatalkan/menghapus transaksi")
    s_before = stock_of(admin, pid)
    r = pengurus.post(f"/api/sales/{sale['id']}/cancel", {"reason": "salah input"})
    check(r.status_code == 200 and r.json()["status"] == "CANCELLED", "pembatalan transaksi", r.text)
    check(stock_of(admin, pid) == s_before + 2, "stock movement pembalik hanya untuk qty yang belum diretur")
    check(pengurus.post(f"/api/sales/{sale['id']}/cancel").status_code == 409, "tidak bisa dibatalkan dua kali")
    check(admin.get(f"/api/sales/{sale['id']}").status_code == 200, "transaksi batal tetap tersimpan (tidak dihapus)")

    # ------------------------------------------------------------------
    print("\n[6] Inventory: adjustment & stock opname")
    s_now = stock_of(admin, pid)
    check(kasir.post("/api/inventory/adjustment", {"productId": pid, "quantity": 1, "reason": "test"}).status_code == 403, "kasir tidak boleh ubah stok manual")
    check(admin.post("/api/inventory/adjustment", {"productId": pid, "quantity": -(s_now + 1), "reason": "hilang"}).status_code == 409, "adjustment tidak boleh membuat stok minus")
    r = admin.post("/api/inventory/adjustment", {"productId": pid, "quantity": -2, "reason": "rusak di gudang"})
    check(r.status_code == 201 and r.json()["stockAfter"] == s_now - 2, "stock adjustment")
    s_now -= 2
    r = pengurus.post("/api/inventory/stock-opname", {"items": [{"productId": pid, "physicalStock": s_now - 1, "systemStock": s_now}]})
    check(r.status_code == 422, "selisih opname wajib ada alasan")
    r = pengurus.post("/api/inventory/stock-opname", {"items": [{"productId": pid, "physicalStock": 1, "systemStock": s_now + 5, "reason": "x"}]})
    check(r.status_code == 409, "opname ditolak jika stok sistem berubah sejak dihitung")
    r = pengurus.post("/api/inventory/stock-opname", {"notes": "Opname bulanan", "items": [{"productId": pid, "physicalStock": s_now - 1, "systemStock": s_now, "reason": "hilang"}]})
    check(r.status_code == 201 and r.json()["itemsWithDifference"] == 1 and r.json()["items"][0]["difference"] == -1, "stock opname dengan selisih", r.text)
    check(stock_of(admin, pid) == s_now - 1, "stok disesuaikan oleh opname")
    check(len(pengurus.get("/api/inventory/stock-opname").json()) >= 1, "riwayat stock opname")
    alerts = pengurus.get("/api/inventory/alerts").json()
    check(any(a["status"] == "OUT_OF_STOCK" for a in alerts) and any(a["status"] == "LOW_STOCK" for a in alerts), "notifikasi stok menipis/habis")

    # ------------------------------------------------------------------
    print("\n[7] Pengeluaran")
    r = admin.post("/api/expenses", {"category": "ELECTRICITY", "description": "Listrik toko", "amount": 500000, "date": now_iso()})
    check(r.status_code == 201, "catat pengeluaran")
    exp_id = r.json()["id"]
    check(pengurus.post("/api/expenses", {"category": "WATER", "description": "Air", "amount": 1, "date": now_iso()}).status_code == 403, "pengurus hanya melihat pengeluaran")
    check(len(pengurus.get("/api/expenses").json()) >= 1, "pengurus melihat pengeluaran")
    r = admin.put(f"/api/expenses/{exp_id}", {"category": "ELECTRICITY", "description": "Listrik toko Sep", "amount": 450000, "date": now_iso()})
    check(r.status_code == 200 and r.json()["amount"] == 450000, "ubah pengeluaran")

    # ------------------------------------------------------------------
    print("\n[8] Anggota (self-service)")
    me = anggota.get("/api/members/me").json()
    check(me["memberNumber"] == "KOP-001" and me["status"] == "ACTIVE", "anggota melihat profil & nomor anggota")
    txs = anggota.get("/api/members/me/transactions").json()
    check(any(t["id"] == sale["id"] for t in txs), "anggota melihat riwayat transaksi pribadi")
    check(anggota.get(f"/api/members/me/transactions/{other_sale['id']}").status_code == 404, "anggota tidak bisa melihat transaksi orang lain")
    check(anggota.get("/api/sales").status_code == 403, "anggota tidak bisa melihat semua penjualan")
    r = admin.post("/api/members", {"name": "Anggota Baru", "phone": "0812"})
    check(r.status_code == 201 and r.json()["memberNumber"] == "KOP-002", "nomor anggota otomatis")

    # ------------------------------------------------------------------
    print("\n[9] Laporan & dashboard")
    dash = pengurus.get("/api/reports/dashboard").json()
    check(dash["todayTransactions"] >= 1 and dash["totalProducts"] >= 5 and dash["lowStockCount"] >= 1, "dashboard pengurus", dash)
    check("totalProducts" not in kasir.get("/api/reports/dashboard").json(), "dashboard kasir terbatas")
    sales_rep = pengurus.get("/api/reports/sales", groupBy="day").json()
    check(sales_rep["summary"]["transactionCount"] >= 1 and sales_rep["summary"]["cancelledCount"] >= 1, "laporan penjualan", sales_rep["summary"])
    check(pengurus.get("/api/reports/sales", productId=pid).status_code == 200, "laporan penjualan filter produk")
    check(pengurus.get("/api/reports/purchases").json()["summary"]["purchaseCount"] >= 1, "laporan pembelian")
    inv_rep = pengurus.get("/api/reports/inventory").json()
    check(inv_rep["summary"]["stockIn"] > 0 and inv_rep["summary"]["stockOut"] > 0, "laporan inventory (stok masuk/keluar)")
    check(any(s["supplierId"] == sid for s in pengurus.get("/api/reports/suppliers").json()["suppliers"]), "laporan supplier")
    pay_rep = pengurus.get("/api/reports/payables").json()
    check(any(r["invoiceNumber"] == "INV-SUP-00125" for r in pay_rep["invoices"]), "laporan hutang")
    profit = pengurus.get("/api/reports/profit").json()
    p = profit["summary"]
    check(p["netProfit"] == round(p["grossProfit"] - p["expenses"], 2) and p["expenses"] >= 450000, "laporan laba dasar", p)
    check(kasir.get("/api/reports/sales").status_code == 403, "kasir tidak bisa lihat laporan")

    # ------------------------------------------------------------------
    print("\n[10] Audit log")
    logs = admin.get("/api/audit-logs", pageSize=200).json()
    actions = {log["action"] for log in logs}
    for required in ["LOGIN", "SALE", "CANCEL", "PAYMENT", "STOCK_ADJUSTMENT", "STOCK_OPNAME", "APPROVE", "RETURN"]:
        check(required in actions, f"audit log mencatat {required}")
    price_logs = admin.get("/api/audit-logs", module="PRODUCT", search="harga").json()
    check(len(price_logs) >= 1, "perubahan harga produk tercatat")

    # ------------------------------------------------------------------
    if os.getenv("E2E_CONCURRENCY", "1") == "1":
        concurrency_checks(admin, kasir, product_payload)

    print(f"\nSEMUA LULUS: {passed} pemeriksaan")


def concurrency_checks(admin: Api, kasir: Api, product_payload: dict) -> None:
    """
    Butuh MongoDB asli: bergantung pada atomisitas update satu dokumen.
    (Server kompatibel seperti FerretDB+SQLite tidak menjaminnya; set
    E2E_CONCURRENCY=0 untuk melewati bagian ini pada server semacam itu.)
    """
    print("\n[11] Konkurensi: penjualan paralel tidak membuat stok minus (BR-02)")
    from concurrent.futures import ThreadPoolExecutor

    r = admin.post("/api/products", {**product_payload, "sku": "KBR-RACE", "barcode": None, "stock": 5})
    race_id = r.json()["id"]

    def buy(_):
        client = Api(kasir.token)
        return client.post("/api/sales", {"items": [{"productId": race_id, "quantity": 1}], "payment": {"method": "QRIS"}}).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(buy, range(12)))
    check(codes.count(201) == 5, f"tepat 5 dari 12 transaksi paralel berhasil (hasil: {sorted(codes)})")
    check(stock_of(admin, race_id) == 0, "stok akhir 0, tidak pernah negatif")
    moves = admin.get("/api/inventory/movements", productId=race_id, type="SALE").json()
    check(len(moves) == 5 and all(m["stockAfter"] >= 0 for m in moves), "jumlah stock movement = transaksi berhasil")
    numbers = [s["invoiceNumber"] for s in kasir.get("/api/sales", pageSize=100).json()]
    check(len(numbers) == len(set(numbers)), "nomor invoice unik walau paralel")


if __name__ == "__main__":
    main()

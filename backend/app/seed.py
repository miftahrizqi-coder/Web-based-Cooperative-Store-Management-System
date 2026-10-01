"""
Inisialisasi data awal.

    python -m app.seed                      # buat admin awal saja
    python -m app.seed --demo               # + data contoh & akun tiap role

Kredensial admin awal diambil dari env SEED_ADMIN_USERNAME /
SEED_ADMIN_PASSWORD / SEED_ADMIN_EMAIL (default: admin / Admin12345!).
Tanpa skrip ini tidak ada cara membuat user pertama.
"""

import argparse
import asyncio
import os

from app.core.database import client, init_db
from app.core.security import hash_password
from app.models.category import Category
from app.models.member import Member
from app.models.product import Product
from app.models.supplier import (
    Supplier,
    SupplierAddress,
    SupplierBankAccount,
    SupplierPaymentTerm,
    SupplierPaymentTermType,
)
from app.models.supplier_product import SupplierProduct
from app.models.user import User, UserRole


async def ensure_user(username: str, password: str, name: str, role: UserRole, email: str, member_id=None) -> User:
    user = await User.find_one(User.username == username)
    if user:
        print(f"  - user '{username}' sudah ada, dilewati")
        return user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=role,
        memberId=member_id,
    )
    await user.insert()
    print(f"  + user '{username}' ({role.value}) password: {password}")
    return user


async def seed_demo() -> None:
    categories = {}
    for name, desc in [("ATK", "Alat tulis kantor"), ("Makanan", "Makanan ringan"), ("Minuman", "Minuman kemasan")]:
        category = await Category.find_one(Category.name == name)
        if not category:
            category = Category(name=name, description=desc)
            await category.insert()
        categories[name] = category

    products = []
    for sku, barcode, name, cat, unit, buy, sell, stock, minimum in [
        ("ATK-001", "8991234567890", "Buku Tulis", "ATK", "pcs", 3000, 4000, 50, 10),
        ("ATK-002", "8991234567891", "Pulpen Hitam", "ATK", "pcs", 1500, 2500, 8, 10),
        ("MKN-001", "8991234567892", "Keripik Singkong", "Makanan", "pcs", 5000, 7000, 30, 5),
        ("MNM-001", "8991234567893", "Air Mineral 600ml", "Minuman", "botol", 2500, 4000, 0, 12),
    ]:
        product = await Product.find_one(Product.sku == sku)
        if not product:
            # Stok awal demo langsung diset (data contoh). Di aplikasi,
            # stok awal via API tercatat sebagai stock movement.
            product = Product(
                sku=sku, barcode=barcode, name=name, categoryId=str(categories[cat].id),
                unit=unit, purchasePrice=buy, sellingPrice=sell, stock=stock, minimumStock=minimum,
            )
            await product.insert()
        products.append(product)

    supplier = await Supplier.find_one(Supplier.supplierCode == "SUP-001")
    if not supplier:
        supplier = Supplier(
            supplierCode="SUP-001",
            name="PT Supplier ABC",
            companyName="PT Supplier ABC Indonesia",
            contactPerson="Budi",
            phone="08123456789",
            email="supplier@example.com",
            address=SupplierAddress(street="Jl. Soekarno Hatta No. 10", city="Bandung",
                                    province="Jawa Barat", postalCode="40286"),
            paymentTerm=SupplierPaymentTerm(type=SupplierPaymentTermType.CREDIT, days=30),
            bankAccount=SupplierBankAccount(bankName="BCA", accountNumber="1234567890",
                                            accountName="PT Supplier ABC"),
            notes="Supplier contoh",
        )
        await supplier.insert()

    for index, product in enumerate(products):
        if not await SupplierProduct.find_one({"supplierId": str(supplier.id), "productId": str(product.id)}):
            await SupplierProduct(
                supplierId=str(supplier.id), productId=str(product.id),
                supplierSku=f"ABC-{index + 1:03d}", purchasePrice=product.purchasePrice,
                minimumOrder=10, leadTimeDays=3, isPreferred=True,
            ).insert()

    member = await Member.find_one(Member.memberNumber == "KOP-001")
    if not member:
        member = Member(memberNumber="KOP-001", name="Siti Anggota", phone="081200000001",
                        email="anggota@example.com", address="Bandung")
        await member.insert()

    await ensure_user("kasir", "Kasir12345!", "Kasir Toko", UserRole.KASIR, "kasir@example.com")
    await ensure_user("pengurus", "Pengurus12345!", "Pengurus Koperasi", UserRole.PENGURUS, "pengurus@example.com")
    await ensure_user("anggota", "Anggota12345!", "Siti Anggota", UserRole.ANGGOTA, "anggota.user@example.com",
                      member_id=str(member.id))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed data awal Sistem Toko Koperasi")
    parser.add_argument("--demo", action="store_true", help="Tambahkan data contoh & akun tiap role")
    args = parser.parse_args()

    await init_db()
    print("Seeding...")
    await ensure_user(
        os.getenv("SEED_ADMIN_USERNAME", "admin"),
        os.getenv("SEED_ADMIN_PASSWORD", "Admin12345!"),
        "Administrator",
        UserRole.ADMIN,
        os.getenv("SEED_ADMIN_EMAIL", "admin@example.com"),
    )
    if args.demo:
        await seed_demo()
    print("Selesai. Segera ganti password default setelah login.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())

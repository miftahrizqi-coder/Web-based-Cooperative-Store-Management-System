from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.models.supplier import Supplier, SupplierStatus
from app.models.user import User, UserRole
from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierResponse,
    SupplierStatusRequest,
    SupplierUpdateRequest,
)


router = APIRouter(
    prefix="/api/suppliers",
    tags=["Suppliers"],
)


def require_supplier_manager(
    user: User = Depends(get_current_user),
) -> User:
    if user.role not in {
        UserRole.ADMIN,
        UserRole.PENGURUS,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supplier management access denied",
        )

    return user


def supplier_response(
    supplier: Supplier,
) -> SupplierResponse:
    return SupplierResponse(
        id=str(supplier.id),
        supplierCode=supplier.supplierCode,
        name=supplier.name,
        companyName=supplier.companyName,
        contactPerson=supplier.contactPerson,
        phone=supplier.phone,
        email=supplier.email,
        address=supplier.address,
        paymentTerm=supplier.paymentTerm,
        bankAccount=supplier.bankAccount,
        status=supplier.status,
        notes=supplier.notes,
        createdAt=supplier.createdAt,
        updatedAt=supplier.updatedAt,
    )


@router.get(
    "",
    response_model=list[SupplierResponse],
)
async def list_suppliers(
    user: User = Depends(require_supplier_manager),
):
    suppliers = (
        await Supplier.find_all()
        .sort("name")
        .to_list()
    )

    return [
        supplier_response(supplier)
        for supplier in suppliers
    ]


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def get_supplier(
    supplier_id: str,
    user: User = Depends(require_supplier_manager),
):
    supplier = await Supplier.get(supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier tidak ditemukan.",
        )

    return supplier_response(supplier)


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_supplier(
    data: SupplierCreateRequest,
    user: User = Depends(require_supplier_manager),
):
    existing_code = await Supplier.find_one(
        Supplier.supplierCode == data.supplierCode,
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier code sudah digunakan.",
        )

    existing_email = await Supplier.find_one(
        Supplier.email == data.email,
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email supplier sudah digunakan.",
        )

    if (
        data.paymentTerm.type.value == "CASH"
        and data.paymentTerm.days != 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment term CASH harus memiliki 0 hari.",
        )

    supplier = Supplier(
        **data.model_dump(),
    )

    await supplier.insert()

    return supplier_response(supplier)


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdateRequest,
    user: User = Depends(require_supplier_manager),
):
    supplier = await Supplier.get(supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier tidak ditemukan.",
        )

    existing_email = await Supplier.find_one(
        Supplier.email == data.email,
    )

    if (
        existing_email
        and str(existing_email.id) != supplier_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email supplier sudah digunakan.",
        )

    if (
        data.paymentTerm.type.value == "CASH"
        and data.paymentTerm.days != 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment term CASH harus memiliki 0 hari.",
        )

    supplier.name = data.name
    supplier.companyName = data.companyName
    supplier.contactPerson = data.contactPerson
    supplier.phone = data.phone
    supplier.email = data.email
    supplier.address = data.address
    supplier.paymentTerm = data.paymentTerm
    supplier.bankAccount = data.bankAccount
    supplier.notes = data.notes
    supplier.updatedAt = datetime.now(timezone.utc)

    await supplier.save()

    return supplier_response(supplier)


@router.patch(
    "/{supplier_id}/status",
    response_model=SupplierResponse,
)
async def update_supplier_status(
    supplier_id: str,
    data: SupplierStatusRequest,
    user: User = Depends(require_supplier_manager),
):
    supplier = await Supplier.get(supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier tidak ditemukan.",
        )

    supplier.status = data.status
    supplier.updatedAt = datetime.now(timezone.utc)

    await supplier.save()

    return supplier_response(supplier)
from datetime import date, datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.deps import ADMIN, ADMIN_PENGURUS, client_ip, require_role
from app.core.utils import (
    Pagination,
    PageParams,
    local_range_bounds,
    next_document_number,
    parse_object_id,
    search_regex,
    utc_now,
)
from app.models.audit_log import AuditAction, AuditModule
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from app.services.audit import log_audit


router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


class ExpenseRequest(BaseModel):
    category: ExpenseCategory
    description: str = Field(min_length=1, max_length=500)
    amount: float = Field(gt=0)
    date: datetime


class ExpenseResponse(BaseModel):
    id: str
    expenseNumber: str
    category: ExpenseCategory
    description: str
    amount: float
    date: datetime
    createdBy: str
    createdByName: str | None = None
    createdAt: datetime
    updatedAt: datetime


async def build_responses(expenses: list[Expense]) -> list[ExpenseResponse]:
    ids = [ObjectId(e.createdBy) for e in expenses if ObjectId.is_valid(e.createdBy)]
    users = {str(u.id): u.name for u in await User.find({"_id": {"$in": ids}}).to_list()} if ids else {}
    return [
        ExpenseResponse(
            id=str(e.id),
            expenseNumber=e.expenseNumber,
            category=e.category,
            description=e.description,
            amount=e.amount,
            date=e.date,
            createdBy=e.createdBy,
            createdByName=users.get(e.createdBy),
            createdAt=e.createdAt,
            updatedAt=e.updatedAt,
        )
        for e in expenses
    ]


async def get_expense_or_404(expense_id: str) -> Expense:
    expense = await Expense.get(parse_object_id(expense_id, "ID pengeluaran"))
    if expense is None:
        raise HTTPException(status_code=404, detail="Pengeluaran tidak ditemukan.")
    return expense


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    category: ExpenseCategory | None = Query(default=None),
    search: str | None = Query(default=None),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    query: dict = {}
    if category:
        query["category"] = category.value
    if search and search.strip():
        query["description"] = search_regex(search)
    start, end = local_range_bounds(date_from, date_to)
    if start or end:
        query["date"] = {}
        if start:
            query["date"]["$gte"] = start
        if end:
            query["date"]["$lt"] = end

    expenses = await pagination.apply(Expense.find(query).sort("-date"))
    return await build_responses(expenses)


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    current_user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    return (await build_responses([await get_expense_or_404(expense_id)]))[0]


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    expense = Expense(
        expenseNumber=await next_document_number("EXP"),
        category=payload.category,
        description=payload.description.strip(),
        amount=payload.amount,
        date=payload.date,
        createdBy=str(current_user.id),
    )
    await expense.insert()

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.EXPENSE,
        description=f"Mencatat pengeluaran {expense.expenseNumber} Rp{expense.amount:,.0f}",
        user=current_user,
        reference_id=str(expense.id),
        ip_address=client_ip(request),
    )
    return (await build_responses([expense]))[0]


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    payload: ExpenseRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    expense = await get_expense_or_404(expense_id)
    before = {"amount": expense.amount, "category": expense.category.value}

    expense.category = payload.category
    expense.description = payload.description.strip()
    expense.amount = payload.amount
    expense.date = payload.date
    expense.updatedBy = str(current_user.id)
    expense.updatedAt = utc_now()
    await expense.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.EXPENSE,
        description=f"Mengubah pengeluaran {expense.expenseNumber}",
        user=current_user,
        reference_id=str(expense.id),
        metadata={"before": before, "after": {"amount": expense.amount, "category": expense.category.value}},
        ip_address=client_ip(request),
    )
    return (await build_responses([expense]))[0]


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    expense = await get_expense_or_404(expense_id)
    snapshot = {
        "expenseNumber": expense.expenseNumber,
        "category": expense.category.value,
        "description": expense.description,
        "amount": expense.amount,
        "date": expense.date.isoformat(),
    }
    await expense.delete()

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.EXPENSE,
        description=f"Menghapus pengeluaran {expense.expenseNumber} Rp{expense.amount:,.0f}",
        user=current_user,
        reference_id=expense_id,
        metadata={"deleted": snapshot},
        ip_address=client_ip(request),
    )

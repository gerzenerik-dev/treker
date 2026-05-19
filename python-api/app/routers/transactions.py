from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_user
from app.enums import TransactionType
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    BalanceSummary,
    CategoryBreakdown,
    TransactionCreate,
    TransactionPublic,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _get_owned_transaction(transaction_id: int, user_id: int, db: Session) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return tx


def _validate_category_ownership(category_id: int, user_id: int, db: Session) -> None:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post("/", response_model=TransactionPublic, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Transaction:
    if payload.category_id is not None:
        _validate_category_ownership(payload.category_id, current_user.id, db)

    tx = Transaction(
        user_id=current_user.id,
        category_id=payload.category_id,
        type=payload.type.value,
        amount=payload.amount,
        description=payload.description,
        date=payload.date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/balance", response_model=BalanceSummary)
def get_balance(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> BalanceSummary:
    base = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if start_date:
        base = base.filter(Transaction.date >= start_date)
    if end_date:
        base = base.filter(Transaction.date <= end_date)

    def _sum(tx_type: TransactionType) -> Decimal:
        result = base.filter(Transaction.type == tx_type.value).with_entities(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).scalar()
        return Decimal(str(result))

    income = _sum(TransactionType.INCOME)
    expenses = _sum(TransactionType.EXPENSE)

    rows = (
        base.filter(Transaction.category_id.isnot(None))
        .join(Category, Transaction.category_id == Category.id)
        .with_entities(
            Category.id,
            Category.name,
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by(Category.id, Category.name, Transaction.type)
        .order_by(Category.name)
        .all()
    )

    by_category = [
        CategoryBreakdown(
            category_id=row[0],
            category_name=row[1],
            type=TransactionType(row[2]),
            total=Decimal(str(row[3])),
        )
        for row in rows
    ]

    return BalanceSummary(
        income=income,
        expenses=expenses,
        balance=income - expenses,
        by_category=by_category,
    )


@router.get("/", response_model=list[TransactionPublic])
def list_transactions(
    type: Optional[TransactionType] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> list[Transaction]:
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if type is not None:
        query = query.filter(Transaction.type == type.value)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionPublic)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Transaction:
    return _get_owned_transaction(transaction_id, current_user.id, db)


@router.patch("/{transaction_id}", response_model=TransactionPublic)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Transaction:
    tx = _get_owned_transaction(transaction_id, current_user.id, db)

    if payload.category_id is not None:
        _validate_category_ownership(payload.category_id, current_user.id, db)
        tx.category_id = payload.category_id
    if payload.type is not None:
        tx.type = payload.type.value
    if payload.amount is not None:
        tx.amount = payload.amount
    if payload.description is not None:
        tx.description = payload.description
    if payload.date is not None:
        tx.date = payload.date

    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> None:
    tx = _get_owned_transaction(transaction_id, current_user.id, db)
    db.delete(tx)
    db.commit()

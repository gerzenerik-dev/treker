from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_user
from app.enums import DebtDirection, DebtStatus
from app.models.debt import Debt
from app.models.user import User
from app.schemas.debt import DebtCreate, DebtPublic, DebtSummary, DebtUpdate

router = APIRouter(prefix="/debts", tags=["debts"])


def _get_owned_debt(debt_id: int, user_id: int, db: Session) -> Debt:
    debt = db.query(Debt).filter(Debt.id == debt_id).first()
    if debt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found")
    if debt.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return debt


@router.post("/", response_model=DebtPublic, status_code=status.HTTP_201_CREATED)
def create_debt(
    payload: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Debt:
    debt = Debt(
        user_id=current_user.id,
        direction=payload.direction.value,
        person=payload.person,
        amount=payload.amount,
        due_date=payload.due_date,
        comment=payload.comment,
        status=DebtStatus.ACTIVE.value,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


# IMPORTANT: /summary must be declared BEFORE /{debt_id} to avoid path collision
@router.get("/summary", response_model=DebtSummary)
def get_debt_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> DebtSummary:
    base = db.query(Debt).filter(
        Debt.user_id == current_user.id,
        Debt.status == DebtStatus.ACTIVE.value,
    )

    def _sum(direction: DebtDirection) -> Decimal:
        result = (
            base.filter(Debt.direction == direction.value)
            .with_entities(func.coalesce(func.sum(Debt.amount), 0))
            .scalar()
        )
        return Decimal(str(result))

    def _count(direction: DebtDirection) -> int:
        return base.filter(Debt.direction == direction.value).count()

    return DebtSummary(
        total_owed_by_me=_sum(DebtDirection.OWED_BY_ME),
        total_owed_to_me=_sum(DebtDirection.OWED_TO_ME),
        count_owed_by_me=_count(DebtDirection.OWED_BY_ME),
        count_owed_to_me=_count(DebtDirection.OWED_TO_ME),
    )


@router.get("/", response_model=list[DebtPublic])
def list_debts(
    direction: Optional[DebtDirection] = None,
    status: Optional[DebtStatus] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> list[Debt]:
    query = db.query(Debt).filter(Debt.user_id == current_user.id)
    if direction is not None:
        query = query.filter(Debt.direction == direction.value)
    if status is not None:
        query = query.filter(Debt.status == status.value)
    return query.order_by(Debt.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{debt_id}", response_model=DebtPublic)
def get_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Debt:
    return _get_owned_debt(debt_id, current_user.id, db)


@router.patch("/{debt_id}", response_model=DebtPublic)
def update_debt(
    debt_id: int,
    payload: DebtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Debt:
    debt = _get_owned_debt(debt_id, current_user.id, db)

    if payload.status is not None:
        debt.status = payload.status.value
        if payload.status == DebtStatus.CLOSED:
            debt.closed_at = datetime.now(timezone.utc)
        else:
            debt.closed_at = None
    if payload.person is not None:
        debt.person = payload.person
    if payload.amount is not None:
        debt.amount = payload.amount
    if payload.due_date is not None:
        debt.due_date = payload.due_date
    if payload.comment is not None:
        debt.comment = payload.comment

    db.commit()
    db.refresh(debt)
    return debt


@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> None:
    debt = _get_owned_debt(debt_id, current_user.id, db)
    db.delete(debt)
    db.commit()

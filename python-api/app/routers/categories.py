from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_active_user
from app.enums import TransactionType
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryPublic, CategoryUpdate
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])


def _get_owned_category(category_id: int, user_id: int, db: Session) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return category


@router.post("/", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Category:
    category = Category(
        user_id=current_user.id,
        name=payload.name,
        type=payload.type.value,
    )
    db.add(category)
    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists",
        )
    return category


@router.get("/", response_model=list[CategoryPublic])
def list_categories(
    type: Optional[TransactionType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> list[Category]:
    query = db.query(Category).filter(Category.user_id == current_user.id)
    if type is not None:
        query = query.filter(Category.type == type.value)
    return query.order_by(Category.name).offset(skip).limit(limit).all()


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Category:
    return _get_owned_category(category_id, current_user.id, db)


@router.patch("/{category_id}", response_model=CategoryPublic)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> Category:
    category = _get_owned_category(category_id, current_user.id, db)

    if payload.name is not None:
        category.name = payload.name
    if payload.type is not None:
        category.type = payload.type.value

    try:
        db.commit()
        db.refresh(category)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category name already exists",
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> None:
    category = _get_owned_category(category_id, current_user.id, db)

    has_transactions = (
        db.query(Transaction).filter(Transaction.category_id == category_id).first() is not None
    )
    if has_transactions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category with existing transactions. Remove or reassign transactions first.",
        )

    db.delete(category)
    db.commit()

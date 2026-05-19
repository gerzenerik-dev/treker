from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.enums import TransactionType


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: Decimal
    category_id: Optional[int] = None
    description: Optional[str] = None
    date: date

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("description")
    @classmethod
    def description_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Description must be 500 characters or fewer")
        return v


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    date: Optional[date] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than zero")
            return round(v, 2)
        return v


class TransactionPublic(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int]
    type: TransactionType
    amount: Decimal
    description: Optional[str]
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    type: TransactionType
    total: Decimal


class BalanceSummary(BaseModel):
    income: Decimal
    expenses: Decimal
    balance: Decimal
    by_category: list[CategoryBreakdown]

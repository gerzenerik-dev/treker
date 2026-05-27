from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.enums import DebtDirection, DebtStatus


class DebtCreate(BaseModel):
    direction: DebtDirection
    person: str
    amount: Decimal
    due_date: Optional[date] = None
    comment: Optional[str] = None

    @field_validator("person")
    @classmethod
    def person_length(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Person name must not be empty")
        if len(v) > 100:
            raise ValueError("Person name must be 100 characters or fewer")
        return v

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("comment")
    @classmethod
    def comment_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Comment must be 500 characters or fewer")
        return v


class DebtUpdate(BaseModel):
    status: Optional[DebtStatus] = None
    person: Optional[str] = None
    amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    comment: Optional[str] = None

    @field_validator("person")
    @classmethod
    def person_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Person name must not be empty")
            if len(v) > 100:
                raise ValueError("Person name must be 100 characters or fewer")
        return v

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be greater than zero")
            return round(v, 2)
        return v


class DebtPublic(BaseModel):
    id: int
    user_id: int
    direction: DebtDirection
    person: str
    amount: Decimal
    due_date: Optional[date]
    comment: Optional[str]
    status: DebtStatus
    created_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DebtSummary(BaseModel):
    total_owed_by_me: Decimal
    total_owed_to_me: Decimal
    count_owed_by_me: int
    count_owed_to_me: int

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.enums import TransactionType


class CategoryCreate(BaseModel):
    name: str
    type: TransactionType

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty")
        if len(v) > 100:
            raise ValueError("Name must be 100 characters or fewer")
        return v


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TransactionType] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name must not be empty")
            if len(v) > 100:
                raise ValueError("Name must be 100 characters or fewer")
        return v


class CategoryPublic(BaseModel):
    id: int
    user_id: int
    name: str
    type: TransactionType
    created_at: datetime

    model_config = {"from_attributes": True}

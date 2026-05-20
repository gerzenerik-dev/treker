import secrets
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category

router = APIRouter(prefix="/admin", tags=["admin"])

_ADMIN_HTML = Path(__file__).parent.parent.parent / "admin.html"
_ADMIN_USER = "admin"
_ADMIN_PASS = "admin123"
_SESSION_TOKEN = secrets.token_hex(32)


class LoginRequest(BaseModel):
    username: str
    password: str


def _require_admin(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, _SESSION_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")


@router.get("")
def serve_admin():
    return FileResponse(_ADMIN_HTML, media_type="text/html")


@router.post("/login")
def admin_login(body: LoginRequest):
    ok = secrets.compare_digest(body.username, _ADMIN_USER) and \
         secrets.compare_digest(body.password, _ADMIN_PASS)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    return {"token": _SESSION_TOKEN}


@router.get("/api/users")
def get_all_users(db: Session = Depends(get_db), _: None = Depends(_require_admin)):
    users = db.query(User).order_by(User.id).all()
    result = []
    for user in users:
        txns = (
            db.query(Transaction, Category.name.label("category_name"))
            .outerjoin(Category, Transaction.category_id == Category.id)
            .filter(Transaction.user_id == user.id)
            .order_by(Transaction.date.desc())
            .all()
        )
        income = sum(float(t.Transaction.amount) for t in txns if t.Transaction.type == "income")
        expense = sum(float(t.Transaction.amount) for t in txns if t.Transaction.type == "expense")
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.strftime("%d.%m.%Y"),
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "transactions": [
                {
                    "id": t.Transaction.id,
                    "date": t.Transaction.date.strftime("%d.%m.%Y"),
                    "type": t.Transaction.type,
                    "amount": float(t.Transaction.amount),
                    "description": t.Transaction.description or "",
                    "category": t.category_name or "—",
                }
                for t in txns
            ],
        })
    return result

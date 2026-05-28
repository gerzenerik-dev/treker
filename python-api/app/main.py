import os
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import Base, DATABASE_URL, engine, get_db
from app.models.debt import Debt  # noqa: F401 — ensures debts table is created
from app.models.user import User
from app.routers import admin, auth, categories, debts, transactions, users

HTML_FILE = Path(__file__).parent.parent / "finance-tracker.html"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Treker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(debts.router)


@app.get("/")
def serve_frontend() -> FileResponse:
    return FileResponse(
        HTML_FILE,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/debug/db-info")
def debug_db_info(db: Session = Depends(get_db)) -> dict:
    user_count = db.query(User).count()
    db_url = DATABASE_URL
    db_type = "postgresql" if db_url.startswith("postgres") else "sqlite"
    env_keys = [k for k in os.environ if "DATA" in k or "SECRET" in k]
    return {
        "database_url": db_url[:30],
        "user_count": user_count,
        "db_type": db_type,
        "env_keys": env_keys,
    }

# Treker — Personal Finance Tracker

## Overview

Personal finance tracking web app with JWT authentication, per-user income/expense tracking, and an Apple-minimalist Russian-language UI served directly from the API.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| Auth | PyJWT 2.x, bcrypt |
| Database | PostgreSQL (production), SQLite (local fallback) |
| Frontend | Vanilla HTML/CSS/JS (single file, no build step) |
| Config | pydantic-settings, `os.environ` for `DATABASE_URL` |
| Tests | pytest, httpx, SQLite in-memory via `StaticPool` |
| Deployment | Render (env var `DATABASE_URL` required) |

## Project Structure

```
treker/
├── CLAUDE.md
├── Procfile                        # web: cd python-api && uvicorn ...
├── railway.json                    # NIXPACKS builder config
├── .nixpacks.toml                  # pins Python 3.11
├── requirements.txt                # forwards to python-api/requirements.txt
└── python-api/
    ├── requirements.txt            # all Python dependencies
    ├── pytest.ini
    ├── finance-tracker.html        # ← main frontend (served at /)
    ├── admin.html                  # admin panel (served at /admin)
    ├── app/
    │   ├── main.py                 # FastAPI app, CORS, routers, debug endpoint
    │   ├── database.py             # engine; reads DATABASE_URL from os.environ
    │   ├── config.py               # pydantic-settings (SECRET_KEY, etc.)
    │   ├── dependencies.py         # get_current_user dependency
    │   ├── enums.py                # TransactionType enum
    │   ├── models/
    │   │   ├── user.py
    │   │   ├── category.py
    │   │   └── transaction.py
    │   ├── schemas/                # Pydantic v2 request/response schemas
    │   ├── routers/
    │   │   ├── auth.py             # POST /auth/register, POST /auth/login
    │   │   ├── users.py            # GET /users/me
    │   │   ├── categories.py       # CRUD /categories/
    │   │   ├── transactions.py     # CRUD /transactions/, GET /transactions/balance
    │   │   └── admin.py            # GET /admin (basic-auth protected)
    │   └── services/
    │       └── auth.py             # hash_password, verify_password, create_token
    └── tests/
        ├── conftest.py             # in-memory SQLite, StaticPool, test client
        ├── test_auth.py
        ├── test_users.py
        ├── test_categories.py
        └── test_transactions.py
```

## Key Files

- [python-api/finance-tracker.html](python-api/finance-tracker.html) — entire frontend in one file; Russian UI, ₽, Apple minimalism, offline-capable via localStorage fallback
- [python-api/app/main.py](python-api/app/main.py) — app entry point; serves `finance-tracker.html` at `/`; includes `/debug/db-info` (temporary, no auth)
- [python-api/app/database.py](python-api/app/database.py) — reads `DATABASE_URL` via `os.environ.get(...)` directly, bypasses pydantic to ensure Render env var is always picked up
- [python-api/app/routers/transactions.py](python-api/app/routers/transactions.py) — `/transactions/balance` route declared **before** `/{transaction_id}` to avoid path collision

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DATABASE_URL` | Yes (prod) | `sqlite:///./app.db` | Full PostgreSQL URL on Render |
| `SECRET_KEY` | No | insecure default | Set a strong 32+ char secret in production |

## Running Locally

```bash
cd python-api
pip install -r requirements.txt
uvicorn app.main:app --reload
# App at http://127.0.0.1:8000
```

## Running Tests

```bash
cd python-api
pytest
```

## Deployment (Render)

- Build command: `pip install -r requirements.txt` (run from `python-api/`)
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set `DATABASE_URL` to the Render PostgreSQL internal connection string
- Tables are created automatically on startup via `Base.metadata.create_all`

## Features

- **Auth** — register/login with JWT; per-user data isolation
- **Transactions** — add income/expense with category, date, comment; delete
- **Initial balance** — set starting balance on first login (stored as special `Начальный баланс` category; excluded from income/expense stats, only affects total balance)
- **Filters** — by period (week/month/year/all time), type, category, free-text search
- **Category breakdown** — per-category totals with percentage bars
- **Offline mode** — falls back to localStorage when API is unreachable; syncs on reconnect
- **Admin panel** — `/admin` lists all users and transactions; protected with `admin/admin123`
- **Export** — downloads all transactions as JSON
- **Debug endpoint** — `GET /debug/db-info` returns DB type, user count, and relevant env key names

## Notes

- `Начальный баланс` transactions are neutral (blue in UI); excluded from income/expense cards and breakdown chart
- Negative initial balance is stored as an `expense` with `abs(amount)`; positive as `income`
- The `python-api/frontend/` directory contains an unused React/TypeScript build; the active frontend is `finance-tracker.html`

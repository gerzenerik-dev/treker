from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.category import Category
from app.models.transaction import Transaction

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
LAST_WEEK = (date.today() - timedelta(days=7)).isoformat()


@pytest.fixture
def income_category(db, regular_user):
    cat = Category(user_id=regular_user.id, name="Salary", type="income")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def expense_category(db, regular_user):
    cat = Category(user_id=regular_user.id, name="Rent", type="expense")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def income_tx(db, regular_user, income_category):
    tx = Transaction(
        user_id=regular_user.id,
        category_id=income_category.id,
        type="income",
        amount="3000.00",
        date=date.today(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@pytest.fixture
def expense_tx(db, regular_user, expense_category):
    tx = Transaction(
        user_id=regular_user.id,
        category_id=expense_category.id,
        type="expense",
        amount="1200.50",
        date=date.today(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


class TestCreateTransaction:
    def test_create_income(self, client: TestClient, user_token):
        resp = client.post(
            "/transactions/",
            json={"type": "income", "amount": "2500.00", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "income"
        assert float(data["amount"]) == 2500.00
        assert data["category_id"] is None

    def test_create_expense(self, client: TestClient, user_token):
        resp = client.post(
            "/transactions/",
            json={"type": "expense", "amount": "89.99", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "expense"

    def test_create_with_category(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.post(
            "/transactions/",
            json={
                "type": "income",
                "amount": "5000.00",
                "date": TODAY,
                "category_id": income_category.id,
                "description": "Monthly salary",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["category_id"] == income_category.id
        assert data["description"] == "Monthly salary"

    def test_create_with_other_user_category(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_cat = Category(user_id=admin_user.id, name="Admin Cat", type="income")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        resp = client.post(
            "/transactions/",
            json={"type": "income", "amount": "100.00", "date": TODAY, "category_id": other_cat.id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_create_zero_amount(self, client: TestClient, user_token):
        resp = client.post(
            "/transactions/",
            json={"type": "income", "amount": "0", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_create_negative_amount(self, client: TestClient, user_token):
        resp = client.post(
            "/transactions/",
            json={"type": "income", "amount": "-100.00", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_create_invalid_type(self, client: TestClient, user_token):
        resp = client.post(
            "/transactions/",
            json={"type": "transfer", "amount": "100.00", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_create_unauthenticated(self, client: TestClient):
        resp = client.post(
            "/transactions/",
            json={"type": "income", "amount": "100.00", "date": TODAY},
        )
        assert resp.status_code == 401


class TestListTransactions:
    def test_list_all(
        self, client: TestClient, user_token, income_tx, expense_tx
    ):
        resp = client.get(
            "/transactions/", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_filtered_by_income(
        self, client: TestClient, user_token, income_tx, expense_tx
    ):
        resp = client.get(
            "/transactions/?type=income",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(t["type"] == "income" for t in resp.json())

    def test_list_filtered_by_expense(
        self, client: TestClient, user_token, income_tx, expense_tx
    ):
        resp = client.get(
            "/transactions/?type=expense",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(t["type"] == "expense" for t in resp.json())

    def test_list_filtered_by_category(
        self, client: TestClient, user_token, income_tx, expense_tx, income_category
    ):
        resp = client.get(
            f"/transactions/?category_id={income_category.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(t["category_id"] == income_category.id for t in resp.json())

    def test_list_filtered_by_date_range(
        self, client: TestClient, user_token, db, regular_user
    ):
        old_tx = Transaction(
            user_id=regular_user.id, type="income", amount="100.00",
            date=date.today() - timedelta(days=30),
        )
        recent_tx = Transaction(
            user_id=regular_user.id, type="income", amount="200.00",
            date=date.today(),
        )
        db.add_all([old_tx, recent_tx])
        db.commit()

        resp = client.get(
            f"/transactions/?start_date={YESTERDAY}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(t["date"] >= YESTERDAY for t in resp.json())

    def test_list_only_own_transactions(
        self, client: TestClient, user_token, income_tx, db, admin_user
    ):
        other_tx = Transaction(
            user_id=admin_user.id, type="income", amount="999.00", date=date.today()
        )
        db.add(other_tx)
        db.commit()

        resp = client.get(
            "/transactions/", headers={"Authorization": f"Bearer {user_token}"}
        )
        ids = [t["id"] for t in resp.json()]
        assert income_tx.id in ids
        assert other_tx.id not in ids


class TestGetTransaction:
    def test_get_own_transaction(
        self, client: TestClient, user_token, income_tx
    ):
        resp = client.get(
            f"/transactions/{income_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == income_tx.id

    def test_get_other_user_transaction(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_tx = Transaction(
            user_id=admin_user.id, type="income", amount="500.00", date=date.today()
        )
        db.add(other_tx)
        db.commit()
        db.refresh(other_tx)

        resp = client.get(
            f"/transactions/{other_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_get_nonexistent_transaction(self, client: TestClient, user_token):
        resp = client.get(
            "/transactions/99999", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 404


class TestUpdateTransaction:
    def test_update_amount(
        self, client: TestClient, user_token, income_tx
    ):
        resp = client.patch(
            f"/transactions/{income_tx.id}",
            json={"amount": "3500.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 3500.00

    def test_update_type(self, client: TestClient, user_token, income_tx):
        resp = client.patch(
            f"/transactions/{income_tx.id}",
            json={"type": "expense"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == "expense"

    def test_update_category(
        self, client: TestClient, user_token, income_tx, expense_category
    ):
        resp = client.patch(
            f"/transactions/{income_tx.id}",
            json={"category_id": expense_category.id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["category_id"] == expense_category.id

    def test_update_other_user_transaction(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_tx = Transaction(
            user_id=admin_user.id, type="income", amount="500.00", date=date.today()
        )
        db.add(other_tx)
        db.commit()
        db.refresh(other_tx)

        resp = client.patch(
            f"/transactions/{other_tx.id}",
            json={"amount": "1.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_update_invalid_amount(
        self, client: TestClient, user_token, income_tx
    ):
        resp = client.patch(
            f"/transactions/{income_tx.id}",
            json={"amount": "0"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422


class TestDeleteTransaction:
    def test_delete_transaction(
        self, client: TestClient, user_token, income_tx
    ):
        resp = client.delete(
            f"/transactions/{income_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    def test_delete_confirms_removal(
        self, client: TestClient, user_token, income_tx
    ):
        client.delete(
            f"/transactions/{income_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            f"/transactions/{income_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_delete_other_user_transaction(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_tx = Transaction(
            user_id=admin_user.id, type="income", amount="500.00", date=date.today()
        )
        db.add(other_tx)
        db.commit()
        db.refresh(other_tx)

        resp = client.delete(
            f"/transactions/{other_tx.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestBalance:
    def test_balance_empty(self, client: TestClient, user_token):
        resp = client.get(
            "/transactions/balance",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["income"]) == 0.0
        assert float(data["expenses"]) == 0.0
        assert float(data["balance"]) == 0.0
        assert data["by_category"] == []

    def test_balance_with_transactions(
        self, client: TestClient, user_token, income_tx, expense_tx
    ):
        resp = client.get(
            "/transactions/balance",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["income"]) == 3000.00
        assert float(data["expenses"]) == 1200.50
        assert float(data["balance"]) == pytest.approx(1799.50)

    def test_balance_by_category_breakdown(
        self, client: TestClient, user_token, income_tx, expense_tx
    ):
        resp = client.get(
            "/transactions/balance",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        by_cat = {c["category_name"]: c for c in resp.json()["by_category"]}
        assert "Salary" in by_cat
        assert float(by_cat["Salary"]["total"]) == 3000.00
        assert by_cat["Salary"]["type"] == "income"
        assert "Rent" in by_cat
        assert float(by_cat["Rent"]["total"]) == 1200.50

    def test_balance_only_own_transactions(
        self, client: TestClient, user_token, income_tx, db, admin_user
    ):
        other_tx = Transaction(
            user_id=admin_user.id, type="income", amount="99999.00", date=date.today()
        )
        db.add(other_tx)
        db.commit()

        resp = client.get(
            "/transactions/balance",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert float(resp.json()["income"]) == 3000.00

    def test_balance_date_range_filter(
        self, client: TestClient, user_token, db, regular_user
    ):
        old = Transaction(
            user_id=regular_user.id, type="income", amount="1000.00",
            date=date.today() - timedelta(days=60),
        )
        recent = Transaction(
            user_id=regular_user.id, type="income", amount="500.00",
            date=date.today(),
        )
        db.add_all([old, recent])
        db.commit()

        resp = client.get(
            f"/transactions/balance?start_date={YESTERDAY}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert float(resp.json()["income"]) == 500.00

    def test_balance_uncategorized_transactions_count_in_totals(
        self, client: TestClient, user_token
    ):
        # Transaction without a category still counts toward income/expense total
        client.post(
            "/transactions/",
            json={"type": "income", "amount": "750.00", "date": TODAY},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            "/transactions/balance",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        data = resp.json()
        assert float(data["income"]) == 750.00
        # Uncategorized transaction does NOT appear in by_category
        assert data["by_category"] == []

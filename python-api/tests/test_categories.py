from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models.category import Category
from app.models.transaction import Transaction


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


class TestCreateCategory:
    def test_create_income_category(self, client: TestClient, user_token):
        resp = client.post(
            "/categories/",
            json={"name": "Salary", "type": "income"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Salary"
        assert data["type"] == "income"

    def test_create_expense_category(self, client: TestClient, user_token):
        resp = client.post(
            "/categories/",
            json={"name": "Groceries", "type": "expense"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "expense"

    def test_create_duplicate_name_same_user(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.post(
            "/categories/",
            json={"name": "Salary", "type": "income"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409

    def test_create_same_name_different_users(
        self, client: TestClient, user_token, admin_token, income_category
    ):
        # Two different users can have categories with the same name
        resp = client.post(
            "/categories/",
            json={"name": "Salary", "type": "income"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201

    def test_create_invalid_type(self, client: TestClient, user_token):
        resp = client.post(
            "/categories/",
            json={"name": "Misc", "type": "invalid"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_create_empty_name(self, client: TestClient, user_token):
        resp = client.post(
            "/categories/",
            json={"name": "   ", "type": "income"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_create_unauthenticated(self, client: TestClient):
        resp = client.post("/categories/", json={"name": "Salary", "type": "income"})
        assert resp.status_code == 401


class TestListCategories:
    def test_list_all(
        self, client: TestClient, user_token, income_category, expense_category
    ):
        resp = client.get(
            "/categories/", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Salary" in names
        assert "Rent" in names

    def test_list_filtered_by_income(
        self, client: TestClient, user_token, income_category, expense_category
    ):
        resp = client.get(
            "/categories/?type=income",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(c["type"] == "income" for c in resp.json())

    def test_list_filtered_by_expense(
        self, client: TestClient, user_token, income_category, expense_category
    ):
        resp = client.get(
            "/categories/?type=expense",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(c["type"] == "expense" for c in resp.json())

    def test_list_only_own_categories(
        self, client: TestClient, user_token, admin_token, income_category
    ):
        # Admin creates their own category
        client.post(
            "/categories/",
            json={"name": "Consulting", "type": "income"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/categories/", headers={"Authorization": f"Bearer {user_token}"}
        )
        names = [c["name"] for c in resp.json()]
        assert "Salary" in names
        assert "Consulting" not in names


class TestGetCategory:
    def test_get_own_category(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.get(
            f"/categories/{income_category.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == income_category.id

    def test_get_other_user_category(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_cat = Category(user_id=admin_user.id, name="Admin Cat", type="income")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        resp = client.get(
            f"/categories/{other_cat.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_get_nonexistent_category(self, client: TestClient, user_token):
        resp = client.get(
            "/categories/99999", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 404


class TestUpdateCategory:
    def test_update_name(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.patch(
            f"/categories/{income_category.id}",
            json={"name": "Freelance"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Freelance"

    def test_update_type(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.patch(
            f"/categories/{income_category.id}",
            json={"type": "expense"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == "expense"

    def test_update_to_duplicate_name(
        self, client: TestClient, user_token, income_category, expense_category
    ):
        resp = client.patch(
            f"/categories/{income_category.id}",
            json={"name": "Rent"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409

    def test_update_other_user_category(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_cat = Category(user_id=admin_user.id, name="Other", type="income")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        resp = client.patch(
            f"/categories/{other_cat.id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestDeleteCategory:
    def test_delete_category(
        self, client: TestClient, user_token, income_category
    ):
        resp = client.delete(
            f"/categories/{income_category.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    def test_delete_category_with_transactions(
        self, client: TestClient, user_token, income_category, db, regular_user
    ):
        tx = Transaction(
            user_id=regular_user.id,
            category_id=income_category.id,
            type="income",
            amount="1000.00",
            date=date.today(),
        )
        db.add(tx)
        db.commit()

        resp = client.delete(
            f"/categories/{income_category.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409
        assert "transactions" in resp.json()["detail"].lower()

    def test_delete_other_user_category(
        self, client: TestClient, user_token, db, admin_user
    ):
        other_cat = Category(user_id=admin_user.id, name="Other", type="income")
        db.add(other_cat)
        db.commit()
        db.refresh(other_cat)

        resp = client.delete(
            f"/categories/{other_cat.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_delete_nonexistent_category(self, client: TestClient, user_token):
        resp = client.delete(
            "/categories/99999", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 404

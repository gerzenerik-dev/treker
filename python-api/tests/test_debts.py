from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.debt import Debt

TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


@pytest.fixture
def debt_owed_by_me(db, regular_user):
    debt = Debt(
        user_id=regular_user.id,
        direction="owed_by_me",
        person="Алексей",
        amount="5000.00",
        due_date=date.today() + timedelta(days=7),
        comment="за ужин",
        status="active",
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


@pytest.fixture
def debt_owed_to_me(db, regular_user):
    debt = Debt(
        user_id=regular_user.id,
        direction="owed_to_me",
        person="Мария",
        amount="2500.00",
        status="active",
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


@pytest.fixture
def closed_debt(db, regular_user):
    debt = Debt(
        user_id=regular_user.id,
        direction="owed_by_me",
        person="Иван",
        amount="1000.00",
        status="closed",
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


class TestCreateDebt:
    def test_create_owed_by_me(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "Алексей", "amount": "5000.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["direction"] == "owed_by_me"
        assert data["person"] == "Алексей"
        assert float(data["amount"]) == 5000.00
        assert data["status"] == "active"
        assert data["closed_at"] is None

    def test_create_owed_to_me(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_to_me", "person": "Мария", "amount": "2500.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["direction"] == "owed_to_me"

    def test_create_with_all_fields(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={
                "direction": "owed_by_me",
                "person": "Сергей",
                "amount": "3000.00",
                "due_date": TOMORROW,
                "comment": "За поездку",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["due_date"] == TOMORROW
        assert data["comment"] == "За поездку"

    def test_rejects_negative_amount(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "Алексей", "amount": "-100.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_rejects_zero_amount(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "Алексей", "amount": "0"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_rejects_empty_person(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "   ", "amount": "100.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_rejects_person_too_long(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "А" * 101, "amount": "100.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_rejects_invalid_direction(self, client: TestClient, user_token):
        resp = client.post(
            "/debts/",
            json={"direction": "invalid", "person": "Иван", "amount": "100.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_requires_auth(self, client: TestClient):
        resp = client.post(
            "/debts/",
            json={"direction": "owed_by_me", "person": "Иван", "amount": "100.00"},
        )
        assert resp.status_code == 401


class TestListDebts:
    def test_lists_own_debts(
        self, client: TestClient, user_token, debt_owed_by_me, debt_owed_to_me
    ):
        resp = client.get(
            "/debts/", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_lists_only_own_debts(
        self, client: TestClient, user_token, debt_owed_by_me, db, admin_user
    ):
        other = Debt(user_id=admin_user.id, direction="owed_by_me", person="X", amount="1.00", status="active")
        db.add(other)
        db.commit()

        resp = client.get("/debts/", headers={"Authorization": f"Bearer {user_token}"})
        ids = [d["id"] for d in resp.json()]
        assert debt_owed_by_me.id in ids
        assert other.id not in ids

    def test_filter_by_direction_owed_by_me(
        self, client: TestClient, user_token, debt_owed_by_me, debt_owed_to_me
    ):
        resp = client.get(
            "/debts/?direction=owed_by_me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(d["direction"] == "owed_by_me" for d in resp.json())

    def test_filter_by_direction_owed_to_me(
        self, client: TestClient, user_token, debt_owed_by_me, debt_owed_to_me
    ):
        resp = client.get(
            "/debts/?direction=owed_to_me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(d["direction"] == "owed_to_me" for d in resp.json())

    def test_filter_by_status_active(
        self, client: TestClient, user_token, debt_owed_by_me, closed_debt
    ):
        resp = client.get(
            "/debts/?status=active",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(d["status"] == "active" for d in resp.json())

    def test_filter_by_status_closed(
        self, client: TestClient, user_token, debt_owed_by_me, closed_debt
    ):
        resp = client.get(
            "/debts/?status=closed",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert all(d["status"] == "closed" for d in resp.json())


class TestDebtSummary:
    def test_summary_empty(self, client: TestClient, user_token):
        resp = client.get("/debts/summary", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_owed_by_me"]) == 0.0
        assert float(data["total_owed_to_me"]) == 0.0
        assert data["count_owed_by_me"] == 0
        assert data["count_owed_to_me"] == 0

    def test_summary_aggregates_active(
        self, client: TestClient, user_token, debt_owed_by_me, debt_owed_to_me
    ):
        resp = client.get("/debts/summary", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_owed_by_me"]) == 5000.00
        assert float(data["total_owed_to_me"]) == 2500.00
        assert data["count_owed_by_me"] == 1
        assert data["count_owed_to_me"] == 1

    def test_summary_excludes_closed(
        self, client: TestClient, user_token, debt_owed_by_me, closed_debt
    ):
        resp = client.get("/debts/summary", headers={"Authorization": f"Bearer {user_token}"})
        data = resp.json()
        # closed_debt (owed_by_me, 1000) must NOT add to total
        assert float(data["total_owed_by_me"]) == 5000.00
        assert data["count_owed_by_me"] == 1

    def test_summary_path_does_not_collide_with_id(self, client: TestClient, user_token):
        """Regression: /debts/summary must resolve to the summary endpoint, not /{debt_id}."""
        resp = client.get("/debts/summary", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        # If path collision occurred we'd get 422 (invalid int) or 404
        assert "total_owed_by_me" in resp.json()

    def test_summary_only_own(
        self, client: TestClient, user_token, debt_owed_by_me, db, admin_user
    ):
        other = Debt(user_id=admin_user.id, direction="owed_by_me", person="X", amount="99999.00", status="active")
        db.add(other)
        db.commit()

        resp = client.get("/debts/summary", headers={"Authorization": f"Bearer {user_token}"})
        assert float(resp.json()["total_owed_by_me"]) == 5000.00


class TestGetDebt:
    def test_get_own_debt(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.get(
            f"/debts/{debt_owed_by_me.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == debt_owed_by_me.id

    def test_get_other_user_debt(self, client: TestClient, user_token, db, admin_user):
        other = Debt(user_id=admin_user.id, direction="owed_by_me", person="X", amount="1.00", status="active")
        db.add(other)
        db.commit()
        db.refresh(other)

        resp = client.get(
            f"/debts/{other.id}", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 403

    def test_get_nonexistent_debt(self, client: TestClient, user_token):
        resp = client.get("/debts/99999", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 404


class TestUpdateDebt:
    def test_close_debt_sets_closed_at(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.patch(
            f"/debts/{debt_owed_by_me.id}",
            json={"status": "closed"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "closed"
        assert data["closed_at"] is not None

    def test_reopen_debt_clears_closed_at(self, client: TestClient, user_token, closed_debt):
        resp = client.patch(
            f"/debts/{closed_debt.id}",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "active"
        assert data["closed_at"] is None

    def test_update_person(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.patch(
            f"/debts/{debt_owed_by_me.id}",
            json={"person": "Новое имя"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["person"] == "Новое имя"

    def test_update_amount(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.patch(
            f"/debts/{debt_owed_by_me.id}",
            json={"amount": "6000.00"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 6000.00

    def test_update_invalid_amount(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.patch(
            f"/debts/{debt_owed_by_me.id}",
            json={"amount": "0"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422

    def test_cannot_update_other_user_debt(
        self, client: TestClient, user_token, db, admin_user
    ):
        other = Debt(user_id=admin_user.id, direction="owed_by_me", person="X", amount="1.00", status="active")
        db.add(other)
        db.commit()
        db.refresh(other)

        resp = client.patch(
            f"/debts/{other.id}",
            json={"status": "closed"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestDeleteDebt:
    def test_delete_debt(self, client: TestClient, user_token, debt_owed_by_me):
        resp = client.delete(
            f"/debts/{debt_owed_by_me.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    def test_delete_confirms_removal(self, client: TestClient, user_token, debt_owed_by_me):
        client.delete(
            f"/debts/{debt_owed_by_me.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp = client.get(
            f"/debts/{debt_owed_by_me.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_cannot_delete_other_user_debt(
        self, client: TestClient, user_token, db, admin_user
    ):
        other = Debt(user_id=admin_user.id, direction="owed_by_me", person="X", amount="1.00", status="active")
        db.add(other)
        db.commit()
        db.refresh(other)

        resp = client.delete(
            f"/debts/{other.id}", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert resp.status_code == 403

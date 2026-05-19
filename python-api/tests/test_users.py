from fastapi.testclient import TestClient


class TestGetMe:
    def test_get_me_authenticated(self, client: TestClient, user_token, regular_user):
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client: TestClient):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        resp = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


class TestListUsers:
    def test_list_users_as_admin(self, client: TestClient, admin_token, regular_user, admin_user):
        resp = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "testuser" in usernames
        assert "admin" in usernames

    def test_list_users_as_regular_user(self, client: TestClient, user_token):
        resp = client.get("/users/", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 403

    def test_list_users_unauthenticated(self, client: TestClient):
        resp = client.get("/users/")
        assert resp.status_code == 401

    def test_list_users_pagination(self, client: TestClient, admin_token):
        resp = client.get("/users/?skip=0&limit=1", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert len(resp.json()) <= 1


class TestGetUser:
    def test_get_own_profile(self, client: TestClient, user_token, regular_user):
        resp = client.get(
            f"/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == regular_user.id

    def test_get_other_user_as_regular(self, client: TestClient, user_token, admin_user):
        resp = client.get(
            f"/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_get_any_user_as_admin(self, client: TestClient, admin_token, regular_user):
        resp = client.get(
            f"/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_get_nonexistent_user(self, client: TestClient, admin_token):
        resp = client.get("/users/99999", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404


class TestUpdateUser:
    def test_update_own_email(self, client: TestClient, user_token, regular_user):
        resp = client.patch(
            f"/users/{regular_user.id}",
            json={"email": "newemail@example.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "newemail@example.com"

    def test_update_own_password(self, client: TestClient, user_token, regular_user):
        resp = client.patch(
            f"/users/{regular_user.id}",
            json={"password": "newpassword456"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        # Verify new password works
        login_resp = client.post("/auth/login", data={"username": "testuser", "password": "newpassword456"})
        assert login_resp.status_code == 200

    def test_update_other_user_as_regular(self, client: TestClient, user_token, admin_user):
        resp = client.patch(
            f"/users/{admin_user.id}",
            json={"email": "hack@example.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_regular_user_cannot_change_is_active(self, client: TestClient, user_token, regular_user):
        resp = client.patch(
            f"/users/{regular_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_admin_can_deactivate_user(self, client: TestClient, admin_token, regular_user):
        resp = client.patch(
            f"/users/{regular_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_update_duplicate_email(self, client: TestClient, user_token, regular_user, admin_user):
        resp = client.patch(
            f"/users/{regular_user.id}",
            json={"email": "admin@example.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409


class TestDeleteUser:
    def test_delete_own_account(self, client: TestClient, user_token, regular_user):
        resp = client.delete(
            f"/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 204

    def test_delete_other_user_as_regular(self, client: TestClient, user_token, admin_user):
        resp = client.delete(
            f"/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_admin_can_delete_any_user(self, client: TestClient, admin_token, regular_user):
        resp = client.delete(
            f"/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    def test_delete_nonexistent_user(self, client: TestClient, admin_token):
        resp = client.delete("/users/99999", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404


class TestHealth:
    def test_health_endpoint(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

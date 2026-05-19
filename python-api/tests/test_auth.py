from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "hashed_password" not in data
        assert data["is_active"] is True
        assert data["is_admin"] is False

    def test_register_duplicate_username(self, client: TestClient, regular_user):
        resp = client.post("/auth/register", json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "password123",
        })
        assert resp.status_code == 409
        assert "Username already taken" in resp.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, regular_user):
        resp = client.post("/auth/register", json={
            "username": "otheruser",
            "email": "test@example.com",
            "password": "password123",
        })
        assert resp.status_code == 409
        assert "Email already registered" in resp.json()["detail"]

    def test_register_invalid_username_too_short(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "username": "ab",
            "email": "x@example.com",
            "password": "password123",
        })
        assert resp.status_code == 422

    def test_register_weak_password(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        resp = client.post("/auth/register", json={
            "username": "validuser",
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, regular_user):
        resp = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, regular_user):
        resp = client.post("/auth/login", data={"username": "testuser", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client: TestClient):
        resp = client.post("/auth/login", data={"username": "ghost", "password": "password123"})
        assert resp.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db, regular_user):
        regular_user.is_active = False
        db.commit()

        resp = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
        assert resp.status_code == 403

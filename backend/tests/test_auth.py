from uuid import uuid4

from app.core.security import hash_password
from app.models.user import User
from sqlalchemy import select


def _create_user(db, email: str | None = None, password: str = "rahasia123") -> User:
    """Buat user uji dengan email unik (idempoten antar-test)."""
    if email is None:
        email = f"dokter-{uuid4().hex[:10]}@uji.id"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Dokter Uji",
        role="doctor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_success_sets_cookie_and_returns_token(client, db):
    user = _create_user(db)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "rahasia123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == user.email
    assert body["user"]["role"] == "doctor"
    assert "access_token" in body
    assert "access_token" in resp.cookies


def test_login_wrong_password(client, db):
    user = _create_user(db)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "salah"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "tidakada@uji.id", "password": "apapun"},
    )
    assert resp.status_code == 401


def test_me_without_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "code" in resp.json()


def test_me_with_bearer_header(client, db):
    from app.core.security import create_access_token

    user = _create_user(db, email="bearer@uji.id")
    token = create_access_token(subject=str(user.id))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "bearer@uji.id"


def test_me_with_cookie_after_login(client, db):
    _create_user(db, email="cookie@uji.id")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "cookie@uji.id", "password": "rahasia123"},
    )
    assert login.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["full_name"] == "Dokter Uji"


def test_logout_clears_cookie(client, db):
    _create_user(db, email="keluar@uji.id")
    client.post("/api/v1/auth/login", json={"email": "keluar@uji.id", "password": "rahasia123"})
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    # Setelah logout, /me harus 401
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401


def test_email_case_insensitive(client, db):
    _create_user(db, email="huruf@uji.id")
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "Huruf@Uji.ID", "password": "rahasia123"},
    )
    assert resp.status_code == 200
    # pastikan email tersimpan lowercase
    stored = db.scalar(select(User).where(User.email == "huruf@uji.id"))
    assert stored is not None

from app.models import DrugMaster, Icd10Master, Patient, ProcedureMaster, User
from scripts.seed import DEMO_PASSWORD, USERS, run_seed
from sqlalchemy import func, select


def test_seed_is_idempotent(db):
    first = run_seed(db)
    second = run_seed(db)

    assert first["users"] >= 2
    assert first["patients"] >= 5
    assert first["icd10"] >= 100
    assert first["drugs"] >= 30
    assert first["procedures"] >= 10

    assert all(v == 0 for v in second.values()), "seed kedua tidak boleh menambah apa pun"


def test_seed_creates_expected_totals(db):
    run_seed(db)
    assert db.scalar(select(func.count()).select_from(User)) >= len(USERS)
    assert db.scalar(select(func.count()).select_from(Patient)) == 8
    assert db.scalar(select(func.count()).select_from(Icd10Master)) >= 100
    assert db.scalar(select(func.count()).select_from(DrugMaster)) >= 30
    assert db.scalar(select(func.count()).select_from(ProcedureMaster)) >= 10


def test_seed_user_can_login(db, client):
    run_seed(db)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "dr.julio@klinikdemo.id", "password": DEMO_PASSWORD},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "doctor"

from uuid import uuid4

import pytest
from app.core.security import hash_password
from app.db.base import Base
from app.models import DrugMaster, Icd10Master, ProcedureMaster, User


@pytest.fixture(autouse=True)
def _clean_db(engine):
    """Kosongkan semua tabel setelah tiap tes (commit antar-request tidak di-rollback)."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def auth_client(client, db):
    """Client yang sudah login sebagai dokter uji."""
    email = f"dr-{uuid4().hex[:8]}@uji.id"
    db.add(
        User(
            email=email,
            password_hash=hash_password("rahasia123"),
            full_name="dr. Uji",
            role="doctor",
        )
    )
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "rahasia123"})
    assert resp.status_code == 200
    return client


@pytest.fixture
def masters(db):
    suffix = uuid4().hex[:6]
    code = f"Z{suffix[:3].upper()}"
    icd = Icd10Master(code=code, name=f"Demam berdarah {suffix}")
    drug = DrugMaster(name=f"Paracetamol {suffix}", unit="tablet", price=500)
    proc = ProcedureMaster(name=f"Injeksi {suffix}", price=25000)
    db.add_all([icd, drug, proc])
    db.commit()
    return icd, drug, proc


def _new_patient(client, name="Pasien Uji"):
    resp = client.post(
        "/api/v1/patients",
        json={"full_name": name, "birth_date": "1990-01-01", "gender": "F"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_patients_require_login(client):
    assert client.get("/api/v1/patients").status_code == 401


def test_create_patient_auto_mrn_and_search(auth_client):
    p1 = _new_patient(auth_client, "Zulaikha Unik")
    p2 = _new_patient(auth_client, "Zulaikha Unik Dua")
    assert p1["medical_record_no"].startswith("RM-")
    assert p1["medical_record_no"] != p2["medical_record_no"]

    resp = auth_client.get("/api/v1/patients", params={"q": "zulaikha unik"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    by_mrn = auth_client.get("/api/v1/patients", params={"q": p1["medical_record_no"]})
    assert by_mrn.json()["total"] == 1


def test_create_patient_duplicate_mrn_and_future_birth(auth_client):
    p = _new_patient(auth_client)
    dup = auth_client.post(
        "/api/v1/patients",
        json={
            "medical_record_no": p["medical_record_no"],
            "full_name": "Lain",
            "birth_date": "1980-01-01",
            "gender": "M",
        },
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "MRN_EXISTS"

    future = auth_client.post(
        "/api/v1/patients",
        json={"full_name": "Masa Depan", "birth_date": "2999-01-01", "gender": "M"},
    )
    assert future.status_code == 422


def test_get_update_patient_and_404(auth_client):
    p = _new_patient(auth_client)
    upd = auth_client.put(f"/api/v1/patients/{p['id']}", json={"address": "Jl. Baru 1"})
    assert upd.status_code == 200
    assert upd.json()["address"] == "Jl. Baru 1"
    assert upd.json()["full_name"] == p["full_name"]
    assert auth_client.get("/api/v1/patients/999999").status_code == 404


def test_master_search(auth_client, masters):
    icd, drug, proc = masters
    assert auth_client.get("/api/v1/icd10", params={"q": icd.code}).json()[0]["code"] == icd.code
    assert auth_client.get("/api/v1/drugs", params={"q": drug.name}).json()[0]["id"] == drug.id
    assert auth_client.get("/api/v1/procedures", params={"q": proc.name}).json()[0]["id"] == proc.id


def test_encounter_exam_roundtrip(auth_client, masters):
    icd, drug, proc = masters
    patient = _new_patient(auth_client)
    enc = auth_client.post("/api/v1/encounters", json={"patient_id": patient["id"]})
    assert enc.status_code == 201
    enc_id = enc.json()["id"]
    assert enc.json()["practitioner"]["full_name"] == "dr. Uji"
    assert enc.json()["status"] == "open"

    payload = {
        "anamnesis": "Pusing, badan menggigil, muntah",
        "physical_exam": [{"body_site": "Mata", "finding": "Mata merah"}],
        "diagnoses": [{"icd_code": icd.code, "name": "abaikan", "source": "manual"}],
        "medications": [{"drug_id": drug.id, "quantity": 12}],
        "procedures": [{"procedure_id": proc.id}],
        "education": "Perbanyak minum air putih",
    }
    saved = auth_client.post(f"/api/v1/encounters/{enc_id}/exam", json=payload)
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["status"] == "completed"
    assert body["anamnesis"] == payload["anamnesis"]
    assert body["education"] == payload["education"]
    assert body["physical_exam"][0]["body_site"] == "Mata"
    assert body["diagnoses"][0]["name"] == icd.name  # nama diambil dari master ICD
    assert body["diagnoses"][0]["verified_by_doctor"] is True
    assert body["medications"][0]["subtotal"] == 6000
    assert body["medications"][0]["doctor"] == "dr. Uji"
    assert body["total_cost"] == 6000 + 25000

    # Simpan ulang menggantikan data lama (tidak menggandakan baris)
    again = auth_client.post(
        f"/api/v1/encounters/{enc_id}/exam",
        json={**payload, "physical_exam": [], "medications": []},
    )
    assert again.status_code == 200
    got = auth_client.get(f"/api/v1/encounters/{enc_id}").json()
    assert got["physical_exam"] == []
    assert got["medications"] == []
    assert len(got["diagnoses"]) == 1

    history = auth_client.get(f"/api/v1/patients/{patient['id']}/encounters").json()
    assert history[0]["id"] == enc_id
    assert history[0]["diagnoses"] == [icd.name]


def test_exam_validation(auth_client, masters):
    _, drug, _ = masters
    patient = _new_patient(auth_client)
    enc_id = auth_client.post("/api/v1/encounters", json={"patient_id": patient["id"]}).json()["id"]
    url = f"/api/v1/encounters/{enc_id}/exam"

    assert (
        auth_client.post(
            url, json={"physical_exam": [{"body_site": "Jempol", "finding": "x"}]}
        ).status_code
        == 422
    )
    assert (
        auth_client.post(url, json={"diagnoses": [{"icd_code": "NOPE", "name": "x"}]}).status_code
        == 422
    )
    assert (
        auth_client.post(
            url, json={"medications": [{"drug_id": drug.id, "quantity": 0}]}
        ).status_code
        == 422
    )
    assert auth_client.post(url, json={"medications": [{"drug_id": 999999}]}).status_code == 422
    assert auth_client.post("/api/v1/encounters/999999/exam", json={}).status_code == 404


def test_encounter_unknown_patient(auth_client):
    assert auth_client.post("/api/v1/encounters", json={"patient_id": 999999}).status_code == 404


def test_dashboard_summary(auth_client):
    _new_patient(auth_client)
    body = auth_client.get("/api/v1/dashboard/summary").json()
    assert body["patient_count"] >= 1
    assert "encounters_today" in body

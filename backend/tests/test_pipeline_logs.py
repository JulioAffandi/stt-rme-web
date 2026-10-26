"""Pengujian untuk log pipeline dan metrik evaluasi (Fase 6)."""

from __future__ import annotations

from app.api.pipeline_logs import calculate_wer
from app.models.pipeline import PipelineLog
from app.models.user import User


def test_calculate_wer_perfect_match():
    ref = "pasien mengeluh pusing dan demam"
    hyp = "pasien mengeluh pusing dan demam"
    assert calculate_wer(ref, hyp) == 0.0


def test_calculate_wer_with_errors():
    ref = "pasien mengeluh pusing dan demam tinggi"
    hyp = "pasien mengeluh sakit dan demam"  # 1 substitusi (pusing->sakit), 1 del (tinggi)
    wer = calculate_wer(ref, hyp)
    assert 0.0 < wer < 1.0


def test_calculate_wer_empty():
    assert calculate_wer("", "") == 0.0
    assert calculate_wer("ada kata", "") == 1.0


def test_list_and_metrics_pipeline_logs(client, db):
    user = User(
        email="evaluator@uji.id",
        password_hash="test",
        full_name="dr. Evaluator",
        role="admin",
    )
    db.add(user)
    db.flush()

    # Tambahkan sample log
    log = PipelineLog(
        model_version="whisper-medium-test",
        wer_value=0.082,
        soap_f1=0.915,
        ner_f1=0.884,
        latency_ms={"stt": 750, "soap": 35, "ner": 45, "assertion": 20},
        notes="Uji coba test runner",
    )
    db.add(log)
    db.commit()

    from app.core.security import create_access_token

    token = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /pipeline-logs
    resp = client.get("/api/v1/pipeline-logs", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any(item["model_version"] == "whisper-medium-test" for item in data["items"])

    # 2. Test GET /pipeline-logs/metrics
    resp_metrics = client.get("/api/v1/pipeline-logs/metrics", headers=headers)
    assert resp_metrics.status_code == 200
    metrics = resp_metrics.json()
    assert metrics["total_runs"] >= 1
    assert metrics["avg_wer"] is not None
    assert metrics["avg_soap_f1"] is not None
    assert metrics["avg_ner_f1"] is not None
    assert metrics["avg_total_latency_ms"] > 0

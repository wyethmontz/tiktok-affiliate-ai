from __future__ import annotations

from core.job_store import JobStore


# ── /generate-ad ─────────────────────────────────────────────────────────────

def test_generate_ad_returns_job_id(client):
    resp = client.post("/generate-ad", json={"product": "Whiten serum"})
    assert resp.status_code == 200
    body = resp.json()
    assert "job_id" in body
    assert body["status"] == "pending"


def test_generate_ad_requires_auth(client):
    from api import app
    from core.auth import get_current_user
    app.dependency_overrides.pop(get_current_user, None)
    try:
        resp = client.post("/generate-ad", json={"product": "Serum"})
        assert resp.status_code == 401
    finally:
        from tests.conftest import _fake_auth
        app.dependency_overrides[get_current_user] = _fake_auth


def test_generate_ad_rejects_empty_product(client):
    resp = client.post("/generate-ad", json={"product": ""})
    assert resp.status_code == 422


def test_generate_ad_rejects_product_too_long(client):
    resp = client.post("/generate-ad", json={"product": "x" * 201})
    assert resp.status_code == 422


def test_generate_ad_rejects_invalid_style(client):
    resp = client.post("/generate-ad", json={"product": "Serum", "style": "unknown"})
    assert resp.status_code == 422


def test_generate_ad_rejects_too_many_images(client):
    urls = [f"https://example.com/img{i}.jpg" for i in range(5)]
    resp = client.post("/generate-ad", json={"product": "Serum", "product_image_urls": urls})
    assert resp.status_code == 422


def test_generate_ad_rejects_bad_image_url(client):
    resp = client.post(
        "/generate-ad",
        json={"product": "Serum", "product_image_urls": ["not-a-url"]},
    )
    assert resp.status_code == 422


# ── /jobs/{job_id} ────────────────────────────────────────────────────────────

def test_get_job_not_found(client):
    resp = client.get("/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_get_job_found(client):
    store = JobStore()
    job_id = store.create_job({"product": "test"})
    store.complete_job(job_id, {"copy": "ad text"})

    from unittest.mock import patch
    from api import jobs as api_jobs
    with patch.object(api_jobs, "get_job", return_value=store.get_job(job_id)):
        resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


# ── /ads ──────────────────────────────────────────────────────────────────────

def test_list_ads_returns_list(client):
    resp = client.get("/ads")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_ads_search_too_long(client):
    resp = client.get("/ads", params={"search": "x" * 101})
    assert resp.status_code == 400


# ── JobStore unit tests ───────────────────────────────────────────────────────

def test_job_store_lifecycle():
    store = JobStore()
    jid = store.create_job({"product": "test"})
    assert store.get_job(jid)["status"] == "pending"

    store.update_step(jid, "strategist")
    assert store.get_job(jid)["status"] == "processing"
    assert store.get_job(jid)["current_step"] == "strategist"

    store.complete_job(jid, {"copy": "result"})
    assert store.get_job(jid)["status"] == "completed"
    assert store.get_job(jid)["result"] == {"copy": "result"}


def test_job_store_fail():
    store = JobStore()
    jid = store.create_job({})
    store.fail_job(jid, "something broke")
    assert store.get_job(jid)["status"] == "failed"
    assert store.get_job(jid)["error"] == "something broke"


def test_job_store_missing_returns_none():
    store = JobStore()
    assert store.get_job("no-such-id") is None

import os
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    assert TestClient(app).get("/health").json()["status"] == "ok"

def test_requires_tenant_key():
    assert TestClient(app).get("/v1/campaigns").status_code == 401

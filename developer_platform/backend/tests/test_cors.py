from fastapi.testclient import TestClient

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from apps.developer_platform.backend.main import app, settings

client = TestClient(app)


def test_allowed_origin():
    allowed_origin = settings.CORS_ORIGINS.split(",")[0]
    response = client.get("/health", headers={"Origin": allowed_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin


def test_disallowed_origin():
    response = client.get("/health", headers={"Origin": "https://malicious.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

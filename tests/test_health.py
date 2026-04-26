from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    body = response.json()

    assert body["code"] == "200"
    assert body["message"] == "SUCCESS_RETRIEVED"
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "enterprise-rag-api"
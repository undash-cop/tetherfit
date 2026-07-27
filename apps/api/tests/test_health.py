from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_shape():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "TetherFit"
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "r2" in data["components"]


def test_me_requires_auth():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/me")
    assert response.status_code == 401

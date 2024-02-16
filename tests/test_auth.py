from fastapi.testclient import TestClient

from app.dependencies import get_user_db_client
from app.main import app
from tests.db_client_mock import UserTestDBClient

client = TestClient(app)


def test_register():
    test_db = UserTestDBClient()
    app.dependency_overrides[get_user_db_client] = lambda: test_db

    response = client.post(
        "/auth/register",
        data={"username": "test@email.com", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "access_token" in response.json()
    assert len(test_db.data) == 1
    assert test_db.data[0].email == "test@email.com"


def test_register_and_signin():
    test_db = UserTestDBClient()
    app.dependency_overrides[get_user_db_client] = lambda: test_db

    # Register user
    register_response = client.post(
        "/auth/register",
        data={"username": "test@email.com", "password": "password"},
    )
    assert register_response.status_code == 200

    # Signin as user
    signin_response = client.post(
        "/auth/token",
        data={"username": "test@email.com", "password": "password"},
    )
    assert signin_response.status_code == 200

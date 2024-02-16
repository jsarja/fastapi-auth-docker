from fastapi.testclient import TestClient

from app.dependencies import get_note_db_client, get_user_db_client
from app.main import app
from tests.db_client_mock import NoteTestBClient, UserTestDBClient

client = TestClient(app)

NOTE_JSON = {"title": "Title", "content": "Note content"}


def test_end_to_end():
    user_test_db = UserTestDBClient()
    note_test_db = NoteTestBClient()
    app.dependency_overrides[get_user_db_client] = lambda: user_test_db
    app.dependency_overrides[get_note_db_client] = lambda: note_test_db

    # Try to create a new note without authentication
    response = client.post(
        "/note",
        json=NOTE_JSON,
    )
    assert response.status_code == 401

    # Register a new user with email and password
    register_response = client.post(
        "/auth/register",
        data={"username": "test@email.com", "password": "password"},
    )
    assert register_response.status_code == 200

    # Sign in with email and password
    signin_response = client.post(
        "/auth/token",
        data={"username": "test@email.com", "password": "password"},
    )
    assert signin_response.status_code == 200

    # Create a new note with Authorization header
    jwt_token = signin_response.json()["access_token"]
    response = client.post(
        "/note",
        json=NOTE_JSON,
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    assert response.status_code == 200

    # Get list of user notes.
    response = client.get(
        "/note",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["title"] == "Title"
    assert response_data[0]["content"] == "Note content"

    # Get note for id.
    note_id = response_data[0]["id"]
    response = client.get(
        f"/note/{note_id}",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["title"] == "Title"
    assert response_data["content"] == "Note content"

    # Update note's title
    response = client.put(
        f"/note/{note_id}",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
        json=NOTE_JSON | {"title": "New title"},
    )
    assert response.status_code == 200

    # Fetch note data to test the title change
    response = client.get(
        f"/note/{note_id}",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    response_data = response.json()
    assert response_data["title"] == "New title"
    assert response_data["content"] == "Note content"

    # Delete notes
    response = client.delete(
        f"/note/{note_id}",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    assert response.status_code == 200

    # Fetch all notes to test that the note was deleted
    response = client.get(
        "/note",
        headers={
            "Authorization": f"Bearer {jwt_token}",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 0

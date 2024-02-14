from pydantic import UUID4

from app.internal.user_db_client import UserDBClient, UserModel
from app.internal.note_db_client import NoteDBClient, NoteModel


class NoteTestBClient(NoteDBClient):
    def __init__(self):
        self.data: list[NoteModel] = []

    def get_notes(self, user_id: UUID4) -> list[NoteModel]:
        return [note for note in self.data if note.user_id == user_id]

    def get_note(self, user_id: UUID4, note_id: UUID4) -> NoteModel | None:
        note = [
            note for note in self.data if note.user_id == user_id and note.id == note_id
        ]
        return note[0] if note else None

    def save_note(self, note: NoteModel):
        self.data.append(note)

    def _get_note_index(self, user_id: UUID4, note_id: UUID4):
        index_in_list = [
            i
            for i, note in enumerate(self.data)
            if note.user_id == user_id and note.id == note_id
        ]
        return index_in_list[0] if index_in_list else None

    def update_note(self, user_id: UUID4, note_id: UUID4, note: NoteModel):
        note_index = self._get_note_index(user_id, note_id)
        if note_index is not None:
            self.data[note_index] = note

    def delete_note(self, user_id: UUID4, note_id: UUID4):
        note_index = self._get_note_index(user_id, note_id)
        if note_index is not None:
            self.data.pop(note_index)


class UserTestDBClient(UserDBClient):
    def __init__(self):
        self.data: list[UserModel] = []

    def get_user(self, user_id: UUID4) -> UserModel | None:
        user = [user for user in self.data if user.id == user_id]
        return user[0] if user else None

    def get_google_user(self, google_user_id: str) -> UserModel | None:
        user = [user for user in self.data if user.google_id == google_user_id]
        return user[0] if user else None

    def get_user_for_email(self, email: str) -> UserModel | None:
        user = [user for user in self.data if user.email == email]
        return user[0] if user else None

    def save_user(self, user: UserModel):
        self.data.append(user)

from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import UUID4, BaseModel
from pymongo import MongoClient

from ..config import settings


class NoteModel(BaseModel):
    id: UUID4
    user_id: UUID4
    title: str
    content: str
    last_updated: datetime


class NoteDBClient(ABC):
    @abstractmethod
    def get_notes(self, user_id: UUID4) -> list[NoteModel]:
        pass

    @abstractmethod
    def get_note(self, user_id: UUID4, note_id: UUID4) -> NoteModel | None:
        pass

    @abstractmethod
    def save_note(self, note: NoteModel):
        pass

    @abstractmethod
    def update_note(self, user_id: UUID4, note_id: UUID4, note: NoteModel):
        pass

    @abstractmethod
    def delete_note(self, user_id: UUID4, note_id: UUID4):
        pass


class NoteMongoDBClient(NoteDBClient):
    def __init__(self):
        mongo_db_client = MongoClient(host=settings.MONGODB_URL, uuidRepresentation="standard")
        mongo_db_database = mongo_db_client.get_database(settings.MONGODB_DATABASE_NAME)
        self.note_connection = mongo_db_database.get_collection("note")

    def get_notes(self, user_id: UUID4) -> list[NoteModel]:
        notes = self.note_connection.find({"user_id": user_id})
        return [NoteModel(**note) for note in notes]

    def get_note(self, user_id: UUID4, note_id: UUID4) -> NoteModel | None:
        note = self.note_connection.find_one({"user_id": user_id, "id": note_id})
        return NoteModel(**note) if note else None

    def save_note(self, note: NoteModel):
        self.note_connection.insert_one(note.model_dump())

    def update_note(self, user_id: UUID4, note_id: UUID4, note: NoteModel):
        self.note_connection.update_one(
            {"user_id": user_id, "id": note_id},
            {"$set": note.model_dump()},
            upsert=False,
        )

    def delete_note(self, user_id: UUID4, note_id: UUID4):
        self.note_connection.delete_one({"user_id": user_id, "id": note_id})

from abc import ABC, abstractmethod

from pydantic import UUID4, BaseModel
from pymongo import MongoClient

from ..config import settings


class UserModel(BaseModel):
    id: UUID4
    email: str
    password: str | None = None
    google_id: str | None = None
    is_disabled: bool = False


class UserDBClient(ABC):
    @abstractmethod
    def get_user(self, user_id: UUID4) -> UserModel | None:
        pass

    @abstractmethod
    def get_google_user(self, google_user_id: str) -> UserModel | None:
        pass

    @abstractmethod
    def get_user_for_email(self, email: str) -> UserModel | None:
        pass

    @abstractmethod
    def save_user(self, user: UserModel):
        pass


class UserMongoDBClient(UserDBClient):
    def __init__(self):
        mongo_db_client = MongoClient(
            host=settings.MONGODB_URL, uuidRepresentation="standard"
        )
        mongo_db_database = mongo_db_client.get_database(settings.MONGODB_DATABASE_NAME)

        self.user_connection = mongo_db_database.get_collection("user")

    def get_user(self, user_id: UUID4) -> UserModel | None:
        user = self.user_connection.find_one({"id": user_id})
        return UserModel(**user) if user else None

    def get_google_user(self, google_user_id: str) -> UserModel | None:
        user = self.user_connection.find_one({"google_id": google_user_id})
        return UserModel(**user) if user else None

    def get_user_for_email(self, email: str) -> UserModel | None:
        user = self.user_connection.find_one({"email": email})
        return UserModel(**user) if user else None

    def save_user(self, user: UserModel):
        self.user_connection.insert_one(user.model_dump())

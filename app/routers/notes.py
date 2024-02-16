from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4, BaseModel

from ..dependencies import get_current_user, get_note_db_client
from ..internal.note_db_client import NoteDBClient, NoteModel
from ..internal.user_management import UserModel

router = APIRouter(
    prefix="/note",
    tags=["note"],
)


class NoteBody(BaseModel):
    title: str
    content: str


@router.get("/", response_model=list[NoteModel])
def get_notes(
    user: Annotated[UserModel, Depends(get_current_user)],
    note_db_client: Annotated[NoteDBClient, Depends(get_note_db_client)],
):
    return note_db_client.get_notes(user_id=user.id)


@router.get("/{note_id}", response_model=NoteModel)
def get_note(
    note_id: UUID4,
    user: Annotated[UserModel, Depends(get_current_user)],
    note_db_client: Annotated[NoteDBClient, Depends(get_note_db_client)],
):
    note = note_db_client.get_note(user_id=user.id, note_id=note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No note found for id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return note


@router.post("/", response_model=None)
def save_note(
    user: Annotated[UserModel, Depends(get_current_user)],
    note_db_client: Annotated[NoteDBClient, Depends(get_note_db_client)],
    body: NoteBody,
):
    note = NoteModel(
        id=uuid4(),
        user_id=user.id,
        last_updated=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    return note_db_client.save_note(note=note)


@router.put("/{note_id}", response_model=None)
def update_note(
    note_id: UUID4,
    user: Annotated[UserModel, Depends(get_current_user)],
    body: NoteBody,
    note_db_client: Annotated[NoteDBClient, Depends(get_note_db_client)],
):
    note = NoteModel(
        id=note_id,
        user_id=user.id,
        last_updated=datetime.now(timezone.utc),
        **body.model_dump(),
    )
    return note_db_client.update_note(user_id=user.id, note_id=note_id, note=note)


@router.delete("/{note_id}", response_model=None)
def delete_note(
    note_id: UUID4,
    user: Annotated[UserModel, Depends(get_current_user)],
    note_db_client: Annotated[NoteDBClient, Depends(get_note_db_client)],
):
    return note_db_client.delete_note(user_id=user.id, note_id=note_id)

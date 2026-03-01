# schemas.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class MessageOut(BaseModel):
    id: UUID
    content: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: list[MessageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
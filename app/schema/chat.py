# schemas.py
from datetime import datetime
from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    content: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
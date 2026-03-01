from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional

MAX_MESSAGE_LENGTH = 2000

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class User(SQLModel, table=True):
    """
    Modèle représentant un utilisateur dans la base de données.
    Contient les informations de base, le rôle, le mot de passe haché,
    """
    __tablename__ = "users" # pyright: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    nom: str = Field(nullable=False)
    prenom: str = Field(nullable=False)
    role: str = Field(default=UserRole.USER.value, nullable=False)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversations: list["Conversation"] = Relationship(back_populates="user", cascade_delete=True)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "josiane.ife@example.com",
                "nom": "IFE",
                "prenom": "Josiane",
                "role": "user"
            }
        }
    }

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations" # pyright: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(default="Nouvelle conversation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", ondelete="CASCADE")
    user: Optional[User] = Relationship(back_populates="conversations")

    messages: list["Message"] = Relationship(back_populates="conversation", cascade_delete=True)


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content: str = Field(nullable=False, max_length=MAX_MESSAGE_LENGTH)
    role: MessageRole = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation_id: Optional[UUID] = Field(default=None, foreign_key="conversations.id", ondelete="CASCADE")
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

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

    class Config:
        json_schema_extra = {
            "example": {
                "email": "josiane.ife@example.com",
                "nom": "IFE",
                "prenom": "Josiane",
                "role": "user"
            }
        }
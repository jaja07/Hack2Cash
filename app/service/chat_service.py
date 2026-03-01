from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from database.models import Conversation, Message, User
from uuid import UUID


class ChatService:
    """Service contenant la logique métier pour les conversations et messages."""

    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, user_id: UUID, title: str) -> Conversation:
        """Crée une nouvelle conversation pour un utilisateur."""
        conversation = Conversation(title=title, user_id=user_id)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Récupère une conversation par son ID."""
        return self.session.exec(
            select(Conversation).where(Conversation.id == conversation_id)
        ).first()

    def get_conversation_messages(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation | None:
        """Récupère une conversation avec ses messages pour un utilisateur spécifique."""
        statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))  # pyright: ignore
        )
        return self.session.exec(statement).first()

    def get_user_conversations(self, user_id: UUID) -> list[Conversation]:
        """Récupère toutes les conversations d'un utilisateur."""
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())  # pyright: ignore
        )
        return list(self.session.exec(statement).all())

    def update_conversation_title(
        self, conversation_id: UUID, user_id: UUID, new_title: str
    ) -> Conversation | None:
        """Met à jour le titre d'une conversation."""
        conversation = self.get_conversation(conversation_id)
        if conversation and conversation.user_id == user_id:
            conversation.title = new_title
            self.session.commit()
            self.session.refresh(conversation)
            return conversation
        return None

    def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Supprime une conversation et tous ses messages."""
        conversation = self.get_conversation(conversation_id)
        if conversation and conversation.user_id == user_id:
            self.session.delete(conversation)
            self.session.commit()
            return True
        return False

    def get_conversation_history(
        self, conversation_id: UUID, user_id: UUID
    ) -> list[dict] | None:
        """
        Retourne l'historique d'une conversation sous forme de liste de dicts
        prêts à être envoyés au client ou passés à l'agent.
        Retourne None si la conversation n'existe pas ou n'appartient pas à l'utilisateur.
        """
        conversation = self.get_conversation_messages(conversation_id, user_id)
        if conversation is None:
            return None
        return [
            {"role": m.role, "content": m.content}
            for m in sorted(conversation.messages, key=lambda m: m.created_at)
        ]

    def save_message(
        self, conversation_id: UUID, content: str, role: str
    ) -> Message:
        """Persiste un message dans une conversation."""
        message = Message(
            content=content,
            role=role, # type: ignore
            conversation_id=conversation_id,
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def is_conversation_owner(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Vérifie qu'une conversation appartient bien à un utilisateur."""
        conversation = self.get_conversation(conversation_id)
        return conversation is not None and conversation.user_id == user_id
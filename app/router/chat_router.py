from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Annotated
from database.session import SessionDep
from database.models import Conversation, Message, User
from schema.chat import ConversationOut, ConversationWithMessages
from service.auth_service import get_current_user
from service.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


# ── Dependency helpers ────────────────────────────────────────────────────────

def get_chat_service(session: SessionDep) -> ChatService:
    return ChatService(session)

ChatServiceDep   = Annotated[ChatService, Depends(get_chat_service)]
CurrentUserDep   = Annotated[User, Depends(get_current_user)]


@router.post("/", response_model=ConversationOut)
async def create_conversation(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
    title: str = "Nouvelle conversation",
):
    """Crée une nouvelle conversation pour l'utilisateur connecté."""
    conversation = chat_service.create_conversation(user_id=user.id, title=title)
    return conversation


@router.get("/", response_model=list[ConversationOut])
async def get_user_conversations(
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
):
    """Retourne toutes les conversations de l'utilisateur."""
    conversations = chat_service.get_user_conversations(user_id=user.id)
    return conversations


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
):
    """Retourne une conversation avec tous ses messages, pour un utilisateur spécifique."""
    conversation = chat_service.get_conversation_messages(conversation_id=conversation_id, user_id=user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conversation


@router.patch("/{conversation_id}/title", response_model=ConversationOut)
async def update_title(
    conversation_id: UUID,
    title: str,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Met à jour le titre d'une conversation."""
    conversation = chat_service.update_conversation_title(conversation_id=conversation_id, user_id=user.id, new_title=title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    user: CurrentUserDep,
    chat_service: ChatServiceDep,
):
    """Supprime une conversation et tous ses messages."""
    success = chat_service.delete_conversation(conversation_id=conversation_id, user_id=user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
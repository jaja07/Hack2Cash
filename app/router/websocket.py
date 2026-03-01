from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from sqlmodel import select

from database.session import SessionDep
from service.auth_service import AuthService
from service.chat_service import ChatService
from database.models import MAX_MESSAGE_LENGTH, User

router = APIRouter()

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session: SessionDep,
    conversation_id: UUID,
    token: str = Query(...)
):
    # 1. Validation de l'utilisateur
    auth_service = AuthService(session)
    try:
        email = auth_service.decode_token(token)
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=401)
    except Exception:
        await websocket.close(code=1008)
        return

    chat_service = ChatService(session)
    await websocket.accept()

    # 2. Récupération de l'historique ET vérification des droits en une seule étape
    history = chat_service.get_conversation_history(conversation_id, user.id)
    
    if history is None:
        await websocket.send_json({"type": "error", "content": "Accès refusé."})
        await websocket.close(code=1008)
        return

    # 3. Envoi de l'historique
    await websocket.send_json({"type": "history", "messages": history})

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("content", "").strip()

            if not user_message:
                continue

            if len(user_message) > MAX_MESSAGE_LENGTH:
                await websocket.send_json({"type": "error", "content": "Trop long."})
                continue

            chat_service.save_message(conversation_id, user_message, "user")
            history.append({"role": "user", "content": user_message})

            await websocket.send_json({"type": "status", "content": "thinking"})

            response = f"Tu as dit : {user_message}"

            chat_service.save_message(conversation_id, response, "assistant")
            history.append({"role": "assistant", "content": response})

            await websocket.send_json({"type": "message", "content": response})

    except WebSocketDisconnect:
        pass
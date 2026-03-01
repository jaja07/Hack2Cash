from uuid import UUID
import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlmodel import select

from database.session import SessionDep
from service.auth_service import AuthService
from service.chat_service import ChatService
from database.models import User
from agent import aria_graph  # On importe le graphe pour le streaming
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session: SessionDep,
    conversation_id: UUID,
    token: str = Query(...)
):
    # 1. Validation de l'utilisateur via le token JWT
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

    # 2. Chargement de l'historique de la conversation
    history = chat_service.get_conversation_history(conversation_id, user.id)
    
    if history is None:
        await websocket.send_json({"type": "error", "content": "Accès refusé ou conversation inexistante."})
        await websocket.close(code=1008)
        return

    # Envoi immédiat de l'historique au frontend
    await websocket.send_json({"type": "history", "messages": history})

    try:
        while True:
            # Réception du message utilisateur
            data = await websocket.receive_json()
            user_message = data.get("content", "").strip()
            if not user_message:
                continue

            # Sauvegarde du message utilisateur en base de données
            chat_service.save_message(conversation_id, user_message, "user")

            # 2. RÉCUPÉRATION DE L'HISTORIQUE POUR L'AGENT
            # On récupère les messages précédents pour que l'IA ait du contexte
            raw_history = chat_service.get_conversation_history(conversation_id, user.id)
            
            # Conversion de l'historique au format attendu par LangGraph (HumanMessage/AIMessage)

            formatted_history = []
            for m in raw_history:
                if m["role"] == "user":
                    formatted_history.append(HumanMessage(content=m["content"]))
                else:
                    formatted_history.append(AIMessage(content=m["content"]))

            try:
                # 3. Exécution de l'agent ARIA en mode STREAMING
                # Le mapping doit correspondre aux clés dans AgentGraph.jsx
                mapping = {
                    "domain_identifier": "supervisor",
                    "data_extractor": "web_research",
                    "tool_builder_agent": "tool_builder",
                    "triz_analyzer": "analysis",
                    "report_generator": "output"
                }

                # Lancement du flux de mise à jour du graphe
                async for update in aria_graph.stream(
                    {"user_query": user_message,
                     "messages": formatted_history,
                      "data_sources": []}, # Sources à lier si fichiers uploadés
                    config={"configurable": {"thread_id": str(conversation_id)}},
                    stream_mode="updates"
                ):
                    for node_name, node_state in update.items():
                        graph_key = mapping.get(node_name)
                        if graph_key:
                            # Notifier le frontend pour animer le nœud correspondant
                            await websocket.send_json({
                                "type": "status",
                                "agent": graph_key,
                                "content": "running"
                            })

                # 4. Récupération du résultat final après la fin du stream
                state = aria_graph.get_state(config={"configurable": {"thread_id": str(conversation_id)}})
                artifacts = state.values.get("report_artifacts", {})
                response_text = artifacts.get("markdown") or "Analyse terminée. Aucun rapport généré."

                # Sauvegarde et envoi de la réponse de l'assistant
                chat_service.save_message(conversation_id, response_text, "assistant")
                await websocket.send_json({"type": "message", "content": response_text})
                
                # Remettre le graphe en état neutre
                await websocket.send_json({"type": "status", "content": "idle"})

            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"Erreur Agent: {error_trace}")
                await websocket.send_json({"type": "error", "content": f"Erreur lors de l'analyse : {str(e)}"})

    except WebSocketDisconnect:
        print(f"Déconnexion de l'utilisateur {user.email} (Conv: {conversation_id})")
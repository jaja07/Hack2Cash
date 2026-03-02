from uuid import UUID
import json
import traceback
from typing import Annotated
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlmodel import select
from service.auth_service import get_current_user
from database.session import SessionDep
from database.models import MAX_MESSAGE_LENGTH
from service.auth_service import AuthService
from service.chat_service import ChatService
from database.models import User
from agent import aria_graph  # On importe le graphe pour le streaming
from langchain_core.messages import HumanMessage, AIMessage
import asyncio

import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from uuid import UUID
from pathlib import Path

router = APIRouter(prefix="/ws", tags=["chats"])
CurrentUserDep   = Annotated[User, Depends(get_current_user)]


NODE_TO_FRONT_KEY = {
    "domain_identifier": "supervisor",
    "data_extractor":    "web_research",
    "tool_builder_agent":"tool_builder",
    "data_operator":     "tool_builder",
    "triz_analyzer":     "analysis",
    "report_generator":  "output"
}

# 1. On récupère le chemin absolu du fichier actuel (websocket.py)
current_file_path = Path(__file__).resolve()

# 2. On remonte d'un niveau (pour sortir de router/) et on pointe vers "uploads"
UPLOAD_DIR = current_file_path.parent.parent / "uploads"

# 3. On crée le dossier s'il n'existe pas
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/{conversation_id}/upload")
async def upload_file(
    user: CurrentUserDep,
    conversation_id: UUID,
    file: UploadFile = File(...),    
):
    # 1. Vérifier que la conversation existe et appartient à l'utilisateur
    # (Utilise ton chat_service pour vérifier les droits ici)
    
    # 2. Nettoyer le nom du fichier et créer le chemin de sauvegarde
    # On préfixe par l'ID de la conversation pour retrouver le fichier facilement
    original_filename = file.filename or ""
    file_extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "txt"
    safe_filename = f"{conversation_id}_source.{file_extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    # 3. Sauvegarder le fichier sur le disque
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de sauvegarde: {str(e)}")
    finally:
        file.file.close()
        
    # (Optionnel) Tu pourrais aussi enregistrer le chemin du fichier dans ta BDD
    
    return {"message": "Fichier uploadé avec succès", "filename": safe_filename, "path": file_path}

@router.websocket("/{conversation_id}")
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

            # Validation de la taille du message
            if len(user_message) > MAX_MESSAGE_LENGTH:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Message trop long (max {MAX_MESSAGE_LENGTH} caractères).",
                })
                continue

            # Sauvegarde du message utilisateur en base de données
            chat_service.save_message(conversation_id, user_message, "user")
            
            # Conversion de l'historique au format attendu par LangGraph (HumanMessage/AIMessage)
            formatted_history = []
            for m in history:
                if m["role"] == "user":
                    formatted_history.append(HumanMessage(content=m["content"]))
                else:
                    formatted_history.append(AIMessage(content=m["content"]))

            try:
                # 1. On informe le client que l'agent démarre
                await websocket.send_json({"type": "status", "content": "agent_starting"})
                await websocket.send_json({"type": "agent_step", "node": "supervisor", "status": "running"})

                # 2. Recherche du fichier avec pathlib (propre et robuste)
                # On utilise directement le UPLOAD_DIR défini en haut du fichier
                matched_files = list(UPLOAD_DIR.glob(f"{conversation_id}_source.*"))
                if not matched_files:
                    print(f"⚠️ ATTENTION : Aucun fichier source trouvé pour la conversation {conversation_id}")
                
                sources = []
                if matched_files:
                    file_path = matched_files[0]
                    # suffix renvoie ".csv", on retire le point avec lstrip
                    file_ext = file_path.suffix.lstrip(".") 
                    
                    sources.append({
                        "source_id": f"upload-{conversation_id}",
                        "source_type": "file",
                        "path_or_url": str(file_path), # ARIA attend une chaîne de caractères
                        "data_format": file_ext,
                        "metadata": {},
                    })

                # 3. Appel à ARIA en mode streaming
                from agent import run_aria 
                
                final_markdown_report = ""
                last_node = None #

                # On itère sur les étapes générées par le graphe ARIA
                for update in run_aria(
                    data_sources=sources,
                    output_formats=["markdown"],
                    thread_id=str(conversation_id),
                    stream=True,
                    user_query=user_message,
                ):
                    if isinstance(update, dict):
                        for node_name, node_state in update.items():
                            if isinstance(node_state, dict):
                                raw_status = node_state.get("status", "")
                
                                # Traduction du nom du nœud technique vers la clé attendue par le front
                                front_key = NODE_TO_FRONT_KEY.get(node_name, node_name)
                                
                                if "report_artifacts" in node_state:
                                    artifacts = node_state.get("report_artifacts", {})
                                    if artifacts and isinstance(artifacts, dict):
                                        md = artifacts.get("markdown")
                                        if md:
                                            final_markdown_report = md

                                # 2. FIX TOOL BUILDER : On ne l'allume que s'il y a un besoin réel
                                if front_key == "tool_builder" and not node_state.get("needs_tool_builder", True):
                                    continue


                                # Si on change de node, on marque le précédent comme terminé
                                if last_node and last_node != front_key:
                                    await websocket.send_json({
                                        "type": "agent_step",
                                        "node": last_node,
                                        "status": "completed"
                                    })
                                    await asyncio.sleep(0.05)
                                

                                # Mapping du statut pour React (completed si 'done', sinon running)
                                frontend_status = "completed" if raw_status == "done" else "running"

                                # ENVOI DE L'ÉTAPE : C'est ce message qui déclenche le halo et les billes bleues
                                if front_key != "supervisor":
                                    await websocket.send_json({
                                        "type": "agent_step", 
                                        "node": front_key,
                                        "status": frontend_status
                                    })

                                if frontend_status == "running" and front_key != "supervisor":
                                    last_node = front_key


                                # CORRECTION ICI : on vérifie si le statut est "done"
                                if node_name == "report_generator" and raw_status == "done":
                                    artifacts = node_state.get("report_artifacts", {})
                                    final_markdown_report = artifacts.get("markdown", "No report generated.")

                # 1. On force l'état "Analyse" à terminé (au cas où il a été sauté)
                await websocket.send_json({"type": "agent_step", "node": "analysis", "status": "completed"})

                # 4. ACTIVATION OUTPUT (déclenche la bille bleue vers Output)
                await websocket.send_json({"type": "agent_step", "node": "output", "status": "running"})

                # 4. Fin de la boucle de stream : on traite la réponse finale
                response_text = final_markdown_report if final_markdown_report else "The agent could not generate a response."

                # Sauvegarde et envoi de la réponse de l'assistant
                chat_service.save_message(conversation_id, response_text, "assistant")

                # 5. ENVOI DU MESSAGE (pendant que la bille circule encore)
                await websocket.send_json({"type": "message", "content": response_text})

              # On fige tout à la fin
                await websocket.send_json({"type": "agent_step", "node": "output", "status": "completed"})
                await websocket.send_json({"type": "agent_step", "node": "supervisor", "status": "completed"})
                await websocket.send_json({"type": "status", "content": "connected"})
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"Erreur Agent: {error_trace}")
                await websocket.send_json({"type": "error", "content": f"Erreur lors de l'analyse : {str(e)}"})

    except WebSocketDisconnect:
        print(f"Déconnexion de l'utilisateur {user.email} (Conv: {conversation_id})")
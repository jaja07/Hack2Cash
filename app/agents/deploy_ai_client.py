"""
agents/deploy_ai_client.py
Client Deploy AI réutilisable (OAuth2 client_credentials + chat).
"""
import requests
from core.config import settings


def get_access_token() -> str:
    """Obtient un access token via client_credentials."""
    response = requests.post(
        settings.AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_chat(access_token: str, agent_id: str = "GPT_4O") -> str:
    """Crée une nouvelle session de chat et retourne le chat_id."""
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Org": settings.ORG_ID,
    }
    response = requests.post(
        f"{settings.API_URL}/chats",
        headers=headers,
        json={"agentId": agent_id, "stream": False},
    )
    response.raise_for_status()
    return response.json()["id"]


def call_agent(access_token: str, chat_id: str, message: str) -> str:
    """Envoie un message au chat et retourne la réponse textuelle."""
    headers = {
        "X-Org": settings.ORG_ID,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{settings.API_URL}/messages",
        headers=headers,
        json={
            "chatId": chat_id,
            "stream": False,
            "content": [{"type": "text", "value": message}],
        },
    )
    response.raise_for_status()
    return response.json()["content"][0]["value"]


def llm_call(prompt: str, agent_id: str = "GPT_4O") -> str:
    """
    Raccourci : crée un chat, envoie un prompt, retourne la réponse.
    Usage : réponse = llm_call("Résume ce CRA : ...")
    """
    token   = get_access_token()
    chat_id = create_chat(token, agent_id)
    return call_agent(token, chat_id, prompt)

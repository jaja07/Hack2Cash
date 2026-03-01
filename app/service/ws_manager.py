import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """
    Gestionnaire de connexions WebSocket.

    Maintient la liste des connexions actives et fournit des méthodes
    pour envoyer des messages à un client spécifique ou à tous les clients.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepte une nouvelle connexion WebSocket et l'ajoute à la liste des connexions actives.

        Args:
            websocket: La connexion WebSocket entrante à accepter.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Supprime une connexion WebSocket de la liste des connexions actives.

        Args:
            websocket: La connexion WebSocket à retirer.
        """
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Envoie un message JSON à un client spécifique.

        Args:
            message: Le message à envoyer, sous forme de dictionnaire sérialisable en JSON.
            websocket: La connexion WebSocket du destinataire.
        """
        await websocket.send_json(message)

    async def broadcast(self, message: dict, exclude: WebSocket | None = None):
        """
        Envoie un message JSON à toutes les connexions actives en parallèle.

        Args:
            message: Le message à diffuser, sous forme de dictionnaire sérialisable en JSON.
            exclude: Une connexion WebSocket à exclure de la diffusion (ex: l'émetteur du message).
                     Si None, le message est envoyé à tous les clients connectés.
        """
        tasks = [
            connection.send_json(message)
            for connection in self.active_connections
            if connection != exclude
        ]
        await asyncio.gather(*tasks)
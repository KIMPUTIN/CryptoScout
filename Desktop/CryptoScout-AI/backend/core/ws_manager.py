
# backend/core/ws_manager.py

from fastapi import WebSocket
from typing import List
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WS connected: {len(self.active_connections)} clients")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WS disconnected: {len(self.active_connections)} clients")

    async def broadcast(self, event: str, payload: dict):
        if not self.active_connections:
            return

        message = json.dumps({
            "event": event,
            "data": payload
        })

        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


manager = ConnectionManager()

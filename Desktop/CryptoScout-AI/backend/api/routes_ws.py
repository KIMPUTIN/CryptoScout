
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.ws_manager import manager

router = APIRouter()


@router.websocket("/ws")

async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            # keep connection alive
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

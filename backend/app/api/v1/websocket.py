from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
from app.api.deps import get_current_user_ws
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    self.disconnect(connection, user_id)
    
    async def broadcast_to_all(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    self.disconnect(connection, user_id)


manager = ConnectionManager()


@router.websocket("/live-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading updates"""
    # Authenticate user from query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    # Validate token and get user (simplified - in production use proper auth)
    # For now, we'll accept the connection and use user_id from query
    user_id = websocket.query_params.get("user_id")
    if not user_id:
        await websocket.close(code=4002, reason="Missing user_id")
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        await websocket.close(code=4003, reason="Invalid user_id")
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully",
            "user_id": user_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages (e.g., subscribe to specific channels)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# Helper functions to send updates from other parts of the app
async def send_trade_update(user_id: int, trade_data: dict):
    """Send trade update to user's WebSocket connections"""
    await manager.send_personal_message({
        "type": "trade_update",
        "data": trade_data
    }, user_id)


async def send_scanner_log(user_id: int, log_data: dict):
    """Send scanner log update to user's WebSocket connections"""
    await manager.send_personal_message({
        "type": "scanner_log",
        "data": log_data
    }, user_id)


async def send_signal_alert(user_id: int, signal_data: dict):
    """Send Telegram signal alert to user's WebSocket connections"""
    await manager.send_personal_message({
        "type": "signal_alert",
        "data": signal_data
    }, user_id)


async def send_system_status(user_id: int, status: str, message: str):
    """Send system status update to user's WebSocket connections"""
    await manager.send_personal_message({
        "type": "system_status",
        "status": status,
        "message": message
    }, user_id)

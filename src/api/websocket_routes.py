"""
WebSocket API Routes
===================

WebSocket endpoints for real-time data streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

from core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")


manager = ConnectionManager()


@router.websocket("/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client messages (subscription requests)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                symbols = message.get("symbols", [])
                logger.info(f"Client subscribed to symbols: {symbols}")
                
                # Send confirmation
                await manager.send_personal_message(
                    json.dumps({
                        "type": "subscription_confirmed",
                        "symbols": symbols,
                        "timestamp": str(asyncio.get_event_loop().time())
                    }),
                    websocket
                )
                
                # TODO: Implement actual market data streaming
                # This would integrate with Kite WebSocket
                
            elif message.get("type") == "unsubscribe":
                symbols = message.get("symbols", [])
                logger.info(f"Client unsubscribed from symbols: {symbols}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for trading alerts."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            
            # Send heartbeat
            await manager.send_personal_message(
                json.dumps({
                    "type": "heartbeat",
                    "timestamp": str(asyncio.get_event_loop().time())
                }),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

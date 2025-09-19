from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer
import uuid
import logging
from typing import Optional
from services.websocket_service import websocket_manager, handle_websocket_message
from api.auth import verify_token

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time prescription data synchronization"""
    connection_id = str(uuid.uuid4())
    
    try:
        # Verify authentication if token is provided
        if token:
            try:
                # Verify JWT token
                payload = verify_token(token)
                authenticated_user_id = payload.get("user_id") or payload.get("sub")
                
                # Use authenticated user_id if available
                if authenticated_user_id:
                    user_id = authenticated_user_id
                    
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        # Use anonymous user if no user_id provided
        if not user_id:
            user_id = f"anonymous_{connection_id[:8]}"
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, user_id, connection_id)
        
        try:
            while True:
                # Wait for messages from client
                message = await websocket.receive_text()
                await handle_websocket_message(websocket, connection_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Connection error")
        except:
            pass
    finally:
        # Clean up connection
        websocket_manager.disconnect(connection_id)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "connected_users": websocket_manager.get_user_count(),
        "status": "operational"
    }

@router.get("/ws/connections/{user_id}")
async def get_user_connections(user_id: str):
    """Get connection information for a specific user"""
    connections = websocket_manager.get_user_connections(user_id)
    return {
        "user_id": user_id,
        "connection_count": len(connections),
        "connection_ids": connections
    }
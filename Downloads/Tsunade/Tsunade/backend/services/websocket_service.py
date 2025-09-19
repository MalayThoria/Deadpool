import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from security.data_protection import WebSocketSecurity, DataValidator
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    PRESCRIPTION_UPLOADED = "prescription_uploaded"
    RECOMMENDATION_ADDED = "recommendation_added"
    MEDICATION_REMINDER = "medication_reminder"
    SYNC_STATUS = "sync_status"
    HEALTH_ALERT = "health_alert"
    CONNECTION_STATUS = "connection_status"

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Associate connection with user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat()
        }
        
        logger.info(f"WebSocket connected: user={user_id}, connection={connection_id}")
        
        # Send connection confirmation
        await self.send_to_connection(connection_id, {
            "type": MessageType.CONNECTION_STATUS,
            "status": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            # Get user_id before removing connection
            user_id = self.connection_metadata.get(connection_id, {}).get("user_id")
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
                
            logger.info(f"WebSocket disconnected: user={user_id}, connection={connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")
                self.disconnect(connection_id)
                return False
        return False
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a user with security validation"""
        try:
            # Validate user ID
            user_id = DataValidator.validate_user_id(user_id)
            
            # Sanitize message content
            sanitized_message = WebSocketSecurity.sanitize_websocket_message(message)
            
            # Add timestamp and message ID for tracking
            sanitized_message.update({
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': f"{user_id}_{datetime.utcnow().timestamp()}"
            })
            
            if user_id in self.user_connections:
                connections = list(self.user_connections[user_id])  # Copy to avoid modification during iteration
                successful_sends = 0
                
                for connection_id in connections:
                    success = await self.send_to_connection(connection_id, sanitized_message)
                    if success:
                        successful_sends += 1
                
                logger.info(f"Sent message to user {user_id}: {successful_sends}/{len(connections)} connections")
                return successful_sends > 0
            return False
            
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            return False
    
    async def broadcast_to_all(self, message: dict):
        """Send message to all active connections"""
        if not self.active_connections:
            return 0
            
        connections = list(self.active_connections.keys())  # Copy to avoid modification during iteration
        successful_sends = 0
        
        for connection_id in connections:
            success = await self.send_to_connection(connection_id, message)
            if success:
                successful_sends += 1
        
        logger.info(f"Broadcast message to {successful_sends}/{len(connections)} connections")
        return successful_sends
    
    async def handle_ping(self, connection_id: str):
        """Handle ping from client"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow().isoformat()
            
            await self.send_to_connection(connection_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user"""
        return list(self.user_connections.get(user_id, set()))
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_count(self) -> int:
        """Get total number of connected users"""
        return len(self.user_connections)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

class PrescriptionSyncService:
    """Service for real-time prescription data synchronization"""
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
    
    async def notify_prescription_uploaded(self, user_id: str, prescription_data: dict):
        """Notify user about new prescription upload"""
        message = {
            "type": MessageType.PRESCRIPTION_UPLOADED,
            "data": {
                "prescription_id": prescription_data.get("id"),
                "status": "processed",
                "medications_count": len(prescription_data.get("medications", [])),
                "conditions_count": len(prescription_data.get("conditions", [])),
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.ws_manager.send_to_user(user_id, message)
        logger.info(f"Notified user {user_id} about prescription upload")
    
    async def notify_recommendation_added(self, user_id: str, recommendation: dict):
        """Notify user about new health recommendation"""
        message = {
            "type": MessageType.RECOMMENDATION_ADDED,
            "data": {
                "recommendation_id": recommendation.get("id"),
                "title": recommendation.get("title"),
                "type": recommendation.get("type"),
                "priority": recommendation.get("priority"),
                "description": recommendation.get("description")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.ws_manager.send_to_user(user_id, message)
        logger.info(f"Notified user {user_id} about new recommendation")
    
    async def notify_medication_reminder(self, user_id: str, medication: dict, reminder_time: str):
        """Notify user about medication reminder"""
        message = {
            "type": MessageType.MEDICATION_REMINDER,
            "data": {
                "medication_name": medication.get("name"),
                "dosage": medication.get("dosage"),
                "reminder_time": reminder_time,
                "instructions": medication.get("instructions")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.ws_manager.send_to_user(user_id, message)
        logger.info(f"Sent medication reminder to user {user_id}")
    
    async def notify_sync_status(self, user_id: str, status: str, details: dict = None):
        """Notify user about synchronization status"""
        message = {
            "type": MessageType.SYNC_STATUS,
            "data": {
                "status": status,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.ws_manager.send_to_user(user_id, message)
        logger.info(f"Notified user {user_id} about sync status: {status}")
    
    async def notify_health_alert(self, user_id: str, alert_type: str, message_text: str, severity: str = "medium"):
        """Notify user about health alerts"""
        message = {
            "type": MessageType.HEALTH_ALERT,
            "data": {
                "alert_type": alert_type,
                "message": message_text,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.ws_manager.send_to_user(user_id, message)
        logger.info(f"Sent health alert to user {user_id}: {alert_type}")

# Global sync service instance
sync_service = PrescriptionSyncService(websocket_manager)

async def handle_websocket_message(websocket: WebSocket, connection_id: str, message: str):
    """Handle incoming WebSocket messages"""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "ping":
            await websocket_manager.handle_ping(connection_id)
        elif message_type == "subscribe":
            # Handle subscription to specific data types
            subscription_type = data.get("subscription_type")
            logger.info(f"Connection {connection_id} subscribed to {subscription_type}")
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON message from connection {connection_id}")
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
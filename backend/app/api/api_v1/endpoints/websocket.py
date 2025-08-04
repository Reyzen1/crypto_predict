# File: backend/app/api/api_v1/endpoints/websocket.py
# WebSocket endpoints for real-time updates
# Foundation for real-time price and prediction updates

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import dashboard_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================
# CONNECTION MANAGER
# =====================================

class ConnectionManager:
    """
    WebSocket connection manager for real-time updates
    
    Manages WebSocket connections and handles broadcasting
    price updates and predictions to connected clients.
    """
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: List[WebSocket] = []
        self.symbol_subscriptions: Dict[str, List[WebSocket]] = {}
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if client_info:
            self.connection_info[websocket] = client_info
        
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from symbol subscriptions
        for symbol, connections in self.symbol_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
        
        # Remove connection info
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_symbol_subscribers(self, symbol: str, message: str):
        """Broadcast message to clients subscribed to specific symbol"""
        if symbol not in self.symbol_subscriptions:
            return
        
        connections = self.symbol_subscriptions[symbol][:]  # Create copy
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {symbol} subscriber: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            if connection in self.symbol_subscriptions[symbol]:
                self.symbol_subscriptions[symbol].remove(connection)
    
    def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        """Subscribe WebSocket to symbol updates"""
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = []
        
        if websocket not in self.symbol_subscriptions[symbol]:
            self.symbol_subscriptions[symbol].append(websocket)
            
        logger.info(f"Client subscribed to {symbol}. Subscribers: {len(self.symbol_subscriptions[symbol])}")
    
    def unsubscribe_from_symbol(self, websocket: WebSocket, symbol: str):
        """Unsubscribe WebSocket from symbol updates"""
        if symbol in self.symbol_subscriptions and websocket in self.symbol_subscriptions[symbol]:
            self.symbol_subscriptions[symbol].remove(websocket)
            logger.info(f"Client unsubscribed from {symbol}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "symbol_subscriptions": {
                symbol: len(connections) 
                for symbol, connections in self.symbol_subscriptions.items()
            },
            "timestamp": datetime.now(timezone.utc)
        }


# Global connection manager instance
manager = ConnectionManager()


# =====================================
# WEBSOCKET ENDPOINTS
# =====================================

@router.websocket("/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time dashboard updates
    
    Provides real-time updates for:
    - Price changes
    - New predictions
    - Market status updates
    - System notifications
    
    **Frontend Usage (No Authentication Required):**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/dashboard');
    
    ws.onopen = function(event) {
        // Subscribe to symbols
        ws.send(JSON.stringify({
            type: 'subscribe',
            symbols: ['BTC', 'ETH']
        }));
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'price_update') {
            // Update price display
            updatePrice(data.symbol, data.current_price);
        }
        
        if (data.type === 'prediction_update') {
            // Update prediction display
            updatePrediction(data.symbol, data.predicted_price, data.confidence);
        }
    };
    ```
    
    **Message Types:**
    - `price_update`: Price changes for subscribed symbols
    - `prediction_update`: New predictions available
    - `system_status`: System status changes
    - `market_update`: Market overview changes
    """
    client_info = {
        "connected_at": datetime.now(timezone.utc),
        "endpoint": "dashboard",
        "subscribed_symbols": []
    }
    
    await manager.connect(websocket, client_info)
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "status": "connected",
            "message": "Connected to CryptoPredict dashboard updates",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "available_symbols": ["BTC", "ETH", "ADA", "DOT"]
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Listen for client messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_dashboard_message(websocket, message, db)
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Dashboard WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/prices/{symbol}")
async def websocket_symbol_prices(
    websocket: WebSocket,
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time price updates for specific symbol
    
    Provides dedicated real-time updates for a single cryptocurrency symbol.
    Optimized for crypto-specific pages or detailed views.
    
    **Frontend Usage (No Authentication Required):**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/prices/BTC');
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // data.type = 'price_update'
        // data.symbol = 'BTC'
        // data.current_price = 45000
        // data.change_24h = 1200
        // data.timestamp = '2024-01-15T10:00:00Z'
    };
    ```
    """
    client_info = {
        "connected_at": datetime.now(timezone.utc),
        "endpoint": f"prices/{symbol}",
        "symbol": symbol.upper()
    }
    
    await manager.connect(websocket, client_info)
    
    # Subscribe to symbol updates
    manager.subscribe_to_symbol(websocket, symbol.upper())
    
    try:
        # Send initial price data
        initial_data = await get_initial_symbol_data(symbol, db)
        await manager.send_personal_message(json.dumps(initial_data), websocket)
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            # Handle any client commands (pause, resume, etc.)
            try:
                message = json.loads(data)
                await handle_symbol_message(websocket, symbol, message, db)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
            
    except WebSocketDisconnect:
        manager.unsubscribe_from_symbol(websocket, symbol.upper())
        manager.disconnect(websocket)
        logger.info(f"Symbol {symbol} WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Symbol {symbol} WebSocket error: {e}")
        manager.disconnect(websocket)


# =====================================
# MESSAGE HANDLERS
# =====================================

async def handle_dashboard_message(
    websocket: WebSocket,
    message: Dict[str, Any],
    db: Session
):
    """Handle messages from dashboard WebSocket clients"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # Subscribe to symbol updates
        symbols = message.get("symbols", [])
        for symbol in symbols:
            manager.subscribe_to_symbol(websocket, symbol.upper())
        
        response = {
            "type": "subscription_confirmed",
            "subscribed_symbols": symbols,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(json.dumps(response), websocket)
    
    elif message_type == "unsubscribe":
        # Unsubscribe from symbol updates
        symbols = message.get("symbols", [])
        for symbol in symbols:
            manager.unsubscribe_from_symbol(websocket, symbol.upper())
        
        response = {
            "type": "unsubscription_confirmed",
            "unsubscribed_symbols": symbols,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(json.dumps(response), websocket)
    
    elif message_type == "get_status":
        # Send connection statistics
        stats = manager.get_stats()
        response = {
            "type": "status",
            "data": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(json.dumps(response), websocket)


async def handle_symbol_message(
    websocket: WebSocket,
    symbol: str,
    message: Dict[str, Any],
    db: Session
):
    """Handle messages from symbol-specific WebSocket clients"""
    message_type = message.get("type")
    
    if message_type == "get_latest":
        # Send latest data for symbol
        latest_data = await get_initial_symbol_data(symbol, db)
        await manager.send_personal_message(json.dumps(latest_data), websocket)


async def get_initial_symbol_data(symbol: str, db: Session) -> Dict[str, Any]:
    """Get initial data for symbol WebSocket connection"""
    try:
        # Get quick crypto data
        dashboard_data = await dashboard_service.get_dashboard_summary(
            db=db,
            symbols=[symbol.upper()],
            user_id=None
        )
        
        if dashboard_data["cryptocurrencies"]:
            crypto_data = dashboard_data["cryptocurrencies"][0]
            return {
                "type": "initial_data",
                "symbol": symbol.upper(),
                "current_price": crypto_data["current_price"],
                "predicted_price": crypto_data["predicted_price"],
                "confidence": crypto_data["confidence"],
                "price_change_24h": crypto_data["price_change_24h"],
                "price_change_24h_percent": crypto_data["price_change_24h_percent"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "type": "error",
                "message": f"Symbol {symbol} not found",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        return {
            "type": "error",
            "message": f"Failed to get initial data: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# =====================================
# UTILITY FUNCTIONS FOR TESTING
# =====================================

async def simulate_price_updates():
    """
    Simulate price updates for testing WebSocket functionality
    
    This function can be called periodically to send fake price updates
    to connected WebSocket clients for development and testing.
    """
    import random
    
    symbols = ["BTC", "ETH", "ADA", "DOT"]
    base_prices = {"BTC": 45000, "ETH": 3000, "ADA": 0.5, "DOT": 8.0}
    
    for symbol in symbols:
        if symbol in manager.symbol_subscriptions:
            # Generate random price change
            base_price = base_prices[symbol]
            change_percent = random.uniform(-2, 2)
            new_price = base_price * (1 + change_percent / 100)
            
            update_message = {
                "type": "price_update",
                "symbol": symbol,
                "current_price": round(new_price, 2),
                "change_24h": round(new_price - base_price, 2),
                "change_24h_percent": round(change_percent, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await manager.broadcast_to_symbol_subscribers(
                symbol, 
                json.dumps(update_message)
            )
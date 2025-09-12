"""
WebSocket handler for real-time voice communication.
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .voice_pipeline import VoicePipeline, VoiceInteraction
from .auth.jwt_handler import JWTHandler
from .auth.models import TokenPayload
from .event_streaming import EventStreamingService, VoiceEvent, EventType

logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    session_id: str
    websocket: WebSocket
    client_ip: str
    user_agent: Optional[str] = None
    tenant_id: Optional[str] = None
    connected_at: float
    
    class Config:
        arbitrary_types_allowed = True


class VoiceWebSocketHandler:
    """
    WebSocket handler for real-time voice interactions.
    Manages connections and coordinates voice processing pipeline.
    """
    
    def __init__(self, voice_pipeline: VoicePipeline, jwt_handler: JWTHandler | None = None):
        self.voice_pipeline = voice_pipeline
        self.jwt_handler = jwt_handler or JWTHandler()
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.event_streaming = voice_pipeline.event_streaming  # Get event streaming from pipeline
        self._message_handlers = {
            "audio_chunk": self._handle_audio_chunk,
            "start_session": self._handle_start_session,
            "end_session": self._handle_end_session,
            "ping": self._handle_ping
        }
    
    async def connect(self, websocket: WebSocket, client_ip: str) -> str:
        """Accept new authenticated WebSocket connection."""

        token = websocket.query_params.get("token") or websocket.headers.get("Authorization")
        if token and token.lower().startswith("bearer "):
            token = token.split()[1]
        if not token:
            await websocket.close(code=4401)
            raise WebSocketDisconnect(code=4401)
        try:
            payload: TokenPayload = self.jwt_handler.decode(token)
        except Exception:
            await websocket.close(code=4401)
            raise WebSocketDisconnect(code=4401)

        await websocket.accept()

        session_id = str(uuid.uuid4())

        connection_info = ConnectionInfo(
            session_id=session_id,
            websocket=websocket,
            client_ip=client_ip,
            user_agent=websocket.headers.get("user-agent"),
            connected_at=asyncio.get_event_loop().time(),
            tenant_id=payload.tenant_id,
        )

        self.active_connections[session_id] = connection_info

        logger.info(
            f"New WebSocket connection: {session_id} from {client_ip} tenant {payload.tenant_id}"
        )

        # Publish connection established event
        if self.event_streaming:
            await self.event_streaming.publish_event(VoiceEvent(
                event_type=EventType.CONNECTION_ESTABLISHED,
                session_id=session_id,
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                timestamp=datetime.now(timezone.utc),
                data={
                    "client_ip": client_ip,
                    "user_agent": connection_info.user_agent,
                    "connection_time": connection_info.connected_at
                },
                metadata={"source": "websocket_handler"},
                correlation_id=str(uuid.uuid4())
            ))

        await self._send_message(
            session_id,
            {
                "type": "connection_established",
                "session_id": session_id,
                "message": "HERMES voice assistant ready",
            },
        )

        return session_id
    
    async def disconnect(self, session_id: str) -> None:
        """
        Handle WebSocket disconnection.
        
        Args:
            session_id: Session ID to disconnect
        """
        if session_id in self.active_connections:
            connection_info = self.active_connections[session_id]
            
            # Publish connection terminated event
            if self.event_streaming:
                await self.event_streaming.publish_event(VoiceEvent(
                    event_type=EventType.CONNECTION_TERMINATED,
                    session_id=session_id,
                    tenant_id=connection_info.tenant_id,
                    user_id=None,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "duration_seconds": asyncio.get_event_loop().time() - connection_info.connected_at,
                        "client_ip": connection_info.client_ip
                    },
                    metadata={"source": "websocket_handler"},
                    correlation_id=str(uuid.uuid4())
                ))
            
            try:
                await connection_info.websocket.close()
            except Exception:
                # Connection might already be closed or in an invalid state, 
                # this is acceptable during cleanup
                pass
            
            del self.active_connections[session_id]
            
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def handle_client_messages(self, session_id: str) -> None:
        """
        Handle incoming messages from client.
        
        Args:
            session_id: Session ID for the connection
        """
        if session_id not in self.active_connections:
            logger.error(f"Session {session_id} not found in active connections")
            return
        
        connection_info = self.active_connections[session_id]
        websocket = connection_info.websocket
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive()
                
                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        # Handle binary audio data
                        await self._handle_audio_data(session_id, message["bytes"])
                    elif "text" in message:
                        # Handle text messages
                        await self._handle_text_message(session_id, message["text"])
                
                elif message["type"] == "websocket.disconnect":
                    logger.info(f"Client disconnected: {session_id}")
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {session_id}")
        except Exception as e:
            logger.error(f"Error handling client messages for {session_id}: {str(e)}")
        finally:
            await self.disconnect(session_id)
    
    async def _handle_text_message(self, session_id: str, text_data: str) -> None:
        """
        Handle text message from client.
        
        Args:
            session_id: Session ID
            text_data: JSON text message
        """
        try:
            message = json.loads(text_data)
            message_type = message.get("type")
            
            if message_type in self._message_handlers:
                await self._message_handlers[message_type](session_id, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self._send_error(session_id, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from {session_id}: {text_data}")
            await self._send_error(session_id, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error processing text message from {session_id}: {str(e)}")
            await self._send_error(session_id, "Message processing error")
    
    async def _handle_audio_data(self, session_id: str, audio_data: bytes) -> None:
        """
        Handle binary audio data from client.
        
        Args:
            session_id: Session ID
            audio_data: Raw audio bytes
        """
        try:
            logger.debug(f"Received {len(audio_data)} bytes of audio from {session_id}")
            
            # Process audio through voice pipeline
            interaction = await self.voice_pipeline.process_voice_interaction(
                session_id, audio_data
            )
            
            # Send transcription result
            if interaction.transcription:
                await self._send_message(session_id, {
                    "type": "transcription",
                    "text": interaction.transcription.text,
                    "confidence": interaction.transcription.confidence,
                    "language": interaction.transcription.language
                })
            
            # Send LLM response
            if interaction.llm_response:
                await self._send_message(session_id, {
                    "type": "response",
                    "text": interaction.llm_response,
                    "requires_human_transfer": interaction.requires_human_transfer
                })
            
            # Send audio response
            if interaction.audio_output:
                await self._send_audio_response(session_id, interaction.audio_output.audio_data)
            
            # Send processing metrics
            await self._send_message(session_id, {
                "type": "metrics",
                "processing_time": interaction.total_processing_time,
                "confidence_score": interaction.confidence_score
            })
            
        except Exception as e:
            logger.error(f"Error processing audio from {session_id}: {str(e)}")
            await self._send_error(session_id, "Audio processing error")
    
    async def _handle_audio_chunk(self, session_id: str, message: Dict[str, Any]) -> None:
        """Handle streaming audio chunk message."""
        # This would be used for streaming audio processing
        # For now, we handle audio via binary messages
        pass
    
    async def _handle_start_session(self, session_id: str, message: Dict[str, Any]) -> None:
        """Handle session start message."""
        logger.info(f"Starting voice session: {session_id}")
        
        await self._send_message(session_id, {
            "type": "session_started",
            "message": "Voice session initialized. Please speak clearly."
        })
    
    async def _handle_end_session(self, session_id: str, message: Dict[str, Any]) -> None:
        """Handle session end message."""
        logger.info(f"Ending voice session: {session_id}")
        
        await self._send_message(session_id, {
            "type": "session_ended",
            "message": "Thank you for using HERMES. Have a great day!"
        })
        
        # Disconnect after sending goodbye message
        await asyncio.sleep(1)
        await self.disconnect(session_id)
    
    async def _handle_ping(self, session_id: str, message: Dict[str, Any]) -> None:
        """Handle ping message for connection health check."""
        await self._send_message(session_id, {
            "type": "pong",
            "timestamp": message.get("timestamp")
        })
    
    async def _send_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """
        Send JSON message to client.
        
        Args:
            session_id: Session ID
            message: Message data to send
        """
        if session_id not in self.active_connections:
            logger.warning(f"Attempted to send message to inactive session: {session_id}")
            return
        
        try:
            websocket = self.active_connections[session_id].websocket
            await websocket.send_text(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {str(e)}")
            await self.disconnect(session_id)
    
    async def _send_audio_response(self, session_id: str, audio_data: bytes) -> None:
        """
        Send audio response to client.
        
        Args:
            session_id: Session ID
            audio_data: Audio bytes to send
        """
        if session_id not in self.active_connections:
            return
        
        try:
            websocket = self.active_connections[session_id].websocket
            
            # Send audio data header
            await websocket.send_text(json.dumps({
                "type": "audio_response",
                "size": len(audio_data)
            }))
            
            # Send audio data in chunks to avoid large WebSocket frames
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await websocket.send_bytes(chunk)
            
            # Send end marker
            await websocket.send_text(json.dumps({
                "type": "audio_end"
            }))
            
        except Exception as e:
            logger.error(f"Error sending audio to {session_id}: {str(e)}")
            await self.disconnect(session_id)
    
    async def _send_error(self, session_id: str, error_message: str) -> None:
        """
        Send error message to client.
        
        Args:
            session_id: Session ID
            error_message: Error description
        """
        await self._send_message(session_id, {
            "type": "error",
            "message": error_message
        })
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self, session_id: str) -> Optional[ConnectionInfo]:
        """Get connection information for session."""
        return self.active_connections.get(session_id)
    
    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message to broadcast
        """
        if not self.active_connections:
            return
        
        tasks = []
        for session_id in list(self.active_connections.keys()):
            tasks.append(self._send_message(session_id, message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def cleanup(self) -> None:
        """Clean up all connections and resources."""
        logger.info("Cleaning up WebSocket handler...")
        
        # Disconnect all active connections
        tasks = []
        for session_id in list(self.active_connections.keys()):
            tasks.append(self.disconnect(session_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("WebSocket handler cleanup completed")
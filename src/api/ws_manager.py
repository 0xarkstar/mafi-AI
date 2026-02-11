"""WebSocket connection manager."""

from fastapi import WebSocket

from src.models.events import WSEvent
from src.utils.logger import get_logger

log = get_logger(__name__)


class WSManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            ws: WebSocket connection to register.
        """
        await ws.accept()
        self.active_connections.add(ws)
        log.info("ws_connected", total=len(self.active_connections))

    def disconnect(self, ws: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            ws: WebSocket connection to unregister.
        """
        self.active_connections.discard(ws)
        log.info("ws_disconnected", total=len(self.active_connections))

    async def broadcast(self, event: WSEvent) -> None:
        """Broadcast event to all connected clients.

        Args:
            event: WSEvent to broadcast.
        """
        if not self.active_connections:
            return

        data = event.model_dump()
        dead = set()

        for ws in self.active_connections:
            try:
                await ws.send_json(data)
            except Exception as exc:
                log.warning("ws_send_failed", error=str(exc))
                dead.add(ws)

        # Remove dead connections
        self.active_connections -= dead

"""WebSocket connection manager."""

import asyncio

from fastapi import WebSocket

from src.models.events import WSEvent
from src.utils.logger import get_logger

log = get_logger(__name__)


class WSManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: set[WebSocket] = set()
        self.player_sessions: dict[str, WebSocket] = {}
        self.player_response_futures: dict[str, asyncio.Future] = {}

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

        # Remove from player sessions if it was a player
        player_name = None
        for name, player_ws in list(self.player_sessions.items()):
            if player_ws == ws:
                player_name = name
                break
        if player_name:
            self.unregister_player(player_name)

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

        for ws in list(self.active_connections):
            try:
                await ws.send_json(data)
            except Exception as exc:
                log.warning("ws_send_failed", error=str(exc))
                dead.add(ws)

        # Remove dead connections
        self.active_connections -= dead

    async def register_player(self, name: str, ws: WebSocket) -> None:
        """Register a WebSocket as a player (not just spectator).

        Args:
            name: Player name.
            ws: WebSocket connection to register as player.
        """
        self.player_sessions[name] = ws
        log.info("player_registered", name=name, total_players=len(self.player_sessions))

    def unregister_player(self, name: str) -> None:
        """Remove player session.

        Args:
            name: Player name to unregister.
        """
        self.player_sessions.pop(name, None)
        self.player_response_futures.pop(name, None)
        log.info("player_unregistered", name=name)

    async def send_to_player(self, name: str, data: dict) -> None:
        """Send data to a specific player's WebSocket.

        Args:
            name: Player name.
            data: Data to send as JSON.
        """
        ws = self.player_sessions.get(name)
        if ws:
            try:
                await ws.send_json(data)
                log.debug("sent_to_player", name=name)
            except Exception as exc:
                log.warning("send_to_player_failed", name=name, error=str(exc))
        else:
            log.warning("player_not_found", name=name)

    def set_response_future(self, name: str, future: asyncio.Future) -> None:
        """Set a future for waiting on player response.

        Args:
            name: Player name.
            future: Future to store for this player.
        """
        self.player_response_futures[name] = future
        log.debug("response_future_set", name=name)

    def resolve_response(self, name: str, response: str) -> None:
        """Resolve player's response future.

        Args:
            name: Player name.
            response: Response string from player.
        """
        future = self.player_response_futures.pop(name, None)
        if future and not future.done():
            future.set_result(response)
            log.info("response_resolved", name=name)
        else:
            log.warning("no_pending_future", name=name)

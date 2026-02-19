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
        self.spectator_sessions: dict[str, WebSocket] = {}
        self._rate_limits: dict[int, float] = {}
        self.wallet_sessions: dict[int, str] = {}

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

        # Remove from spectator sessions
        spec_name = None
        for name, spec_ws in list(self.spectator_sessions.items()):
            if spec_ws == ws:
                spec_name = name
                break
        if spec_name:
            self.spectator_sessions.pop(spec_name, None)

        # Clean up rate limit entry
        self._rate_limits.pop(id(ws), None)

        # Clean up wallet session
        self.wallet_sessions.pop(id(ws), None)

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

    def register_spectator(self, name: str, ws: WebSocket) -> None:
        """Register a WebSocket as a spectator chat participant.

        Args:
            name: Spectator display name.
            ws: WebSocket connection.
        """
        self.spectator_sessions[name] = ws
        log.info("spectator_registered", name=name, total_spectators=len(self.spectator_sessions))

    def get_spectator_name(self, ws: WebSocket) -> str | None:
        """Look up spectator name by WebSocket connection.

        Args:
            ws: WebSocket connection.

        Returns:
            Spectator name or None.
        """
        for name, spec_ws in self.spectator_sessions.items():
            if spec_ws == ws:
                return name
        return None

    def register_wallet(self, ws: WebSocket, wallet_address: str) -> None:
        """Associate a wallet address with a WebSocket connection.

        Args:
            ws: WebSocket connection.
            wallet_address: Wallet address string.
        """
        self.wallet_sessions[id(ws)] = wallet_address
        log.info("wallet_registered", wallet=wallet_address)

    def get_wallet_for_ws(self, ws: WebSocket) -> str | None:
        """Look up wallet address for a WebSocket connection.

        Args:
            ws: WebSocket connection.

        Returns:
            Wallet address or None.
        """
        return self.wallet_sessions.get(id(ws))

    def check_rate_limit(self, ws: WebSocket, min_interval: float = 3.0) -> bool:
        """Check if a WebSocket is allowed to send (rate limiting).

        Args:
            ws: WebSocket connection.
            min_interval: Minimum seconds between messages.

        Returns:
            True if allowed, False if rate-limited.
        """
        import time

        ws_id = id(ws)
        now = time.monotonic()
        last = self._rate_limits.get(ws_id, 0.0)
        if now - last < min_interval:
            return False
        self._rate_limits[ws_id] = now
        return True

    def clear_sessions(self) -> None:
        """Remove all player sessions (between games)."""
        self.player_sessions.clear()

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

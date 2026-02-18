"""Tests for WSManager in src/api/ws_manager.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.ws_manager import WSManager
from src.models.events import WSEvent


def make_mock_ws() -> MagicMock:
    """Create a mock WebSocket with async methods."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


def make_event(event_type: str = "test_event", game_id: str = "game-1") -> WSEvent:
    """Create a sample WSEvent."""
    return WSEvent(
        event_type=event_type,
        data={"message": "hello"},
        game_id=game_id,
        timestamp="2024-01-01T00:00:00",
    )


# === connect / disconnect ===


@pytest.mark.asyncio
async def test_connect_accepts_websocket():
    """connect() calls ws.accept() and adds to active_connections."""
    manager = WSManager()
    ws = make_mock_ws()

    await manager.connect(ws)

    ws.accept.assert_awaited_once()
    assert ws in manager.active_connections


@pytest.mark.asyncio
async def test_connect_multiple_websockets():
    """Multiple connections are all tracked."""
    manager = WSManager()
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await manager.connect(ws1)
    await manager.connect(ws2)

    assert len(manager.active_connections) == 2
    assert ws1 in manager.active_connections
    assert ws2 in manager.active_connections


def test_disconnect_removes_connection():
    """disconnect() removes WebSocket from active_connections."""
    manager = WSManager()
    ws = make_mock_ws()
    manager.active_connections.add(ws)

    manager.disconnect(ws)

    assert ws not in manager.active_connections


def test_disconnect_unknown_ws_is_safe():
    """disconnect() with unknown WebSocket does not raise."""
    manager = WSManager()
    ws = make_mock_ws()

    # Should not raise
    manager.disconnect(ws)
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_disconnect_removes_player_session():
    """disconnect() also unregisters the player if they had a session."""
    manager = WSManager()
    ws = make_mock_ws()

    await manager.connect(ws)
    await manager.register_player("Alice", ws)

    manager.disconnect(ws)

    assert "Alice" not in manager.player_sessions
    assert ws not in manager.active_connections


# === broadcast ===


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_connections():
    """broadcast() sends event JSON to all active connections."""
    manager = WSManager()
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()
    manager.active_connections = {ws1, ws2}

    event = make_event("phase_change")
    await manager.broadcast(event)

    ws1.send_json.assert_awaited_once()
    ws2.send_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_broadcast_sends_correct_data():
    """broadcast() sends the event model_dump as JSON."""
    manager = WSManager()
    ws = make_mock_ws()
    manager.active_connections = {ws}

    event = make_event("game_over", game_id="game-42")
    await manager.broadcast(event)

    sent_data = ws.send_json.call_args[0][0]
    assert sent_data["event_type"] == "game_over"
    assert sent_data["game_id"] == "game-42"


@pytest.mark.asyncio
async def test_broadcast_with_no_connections():
    """broadcast() with empty connections does nothing (no error)."""
    manager = WSManager()
    assert len(manager.active_connections) == 0

    # Should not raise
    await manager.broadcast(make_event())


@pytest.mark.asyncio
async def test_broadcast_removes_dead_connections():
    """broadcast() removes connections that fail to send."""
    manager = WSManager()
    ws_good = make_mock_ws()
    ws_dead = make_mock_ws()
    ws_dead.send_json = AsyncMock(side_effect=Exception("connection closed"))

    manager.active_connections = {ws_good, ws_dead}

    await manager.broadcast(make_event())

    # Dead connection should be removed
    assert ws_dead not in manager.active_connections
    assert ws_good in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_continues_after_one_failure():
    """broadcast() still sends to working connections after one fails."""
    manager = WSManager()
    ws_good = make_mock_ws()
    ws_dead = make_mock_ws()
    ws_dead.send_json = AsyncMock(side_effect=Exception("timeout"))

    manager.active_connections = {ws_good, ws_dead}

    await manager.broadcast(make_event())

    # Good connection still received the message
    ws_good.send_json.assert_awaited_once()


# === register_player / unregister_player ===


@pytest.mark.asyncio
async def test_register_player_stores_session():
    """register_player() maps name to WebSocket."""
    manager = WSManager()
    ws = make_mock_ws()

    await manager.register_player("Bob", ws)

    assert manager.player_sessions["Bob"] is ws


@pytest.mark.asyncio
async def test_register_player_multiple():
    """Multiple players can be registered."""
    manager = WSManager()
    ws1 = make_mock_ws()
    ws2 = make_mock_ws()

    await manager.register_player("Alice", ws1)
    await manager.register_player("Bob", ws2)

    assert len(manager.player_sessions) == 2


def test_unregister_player_removes_session():
    """unregister_player() removes player from sessions."""
    manager = WSManager()
    ws = make_mock_ws()
    manager.player_sessions["Alice"] = ws

    manager.unregister_player("Alice")

    assert "Alice" not in manager.player_sessions


def test_unregister_player_removes_response_future():
    """unregister_player() also removes any pending response future."""
    manager = WSManager()
    ws = make_mock_ws()
    manager.player_sessions["Alice"] = ws
    loop = asyncio.new_event_loop()
    future = loop.create_future()
    manager.player_response_futures["Alice"] = future

    manager.unregister_player("Alice")

    assert "Alice" not in manager.player_response_futures
    loop.close()


def test_unregister_unknown_player_is_safe():
    """unregister_player() with unknown name does not raise."""
    manager = WSManager()
    manager.unregister_player("nobody")  # Should not raise


# === send_to_player ===


@pytest.mark.asyncio
async def test_send_to_player_sends_data():
    """send_to_player() sends JSON to the player's WebSocket."""
    manager = WSManager()
    ws = make_mock_ws()
    manager.player_sessions["Alice"] = ws

    await manager.send_to_player("Alice", {"action": "vote"})

    ws.send_json.assert_awaited_once_with({"action": "vote"})


@pytest.mark.asyncio
async def test_send_to_player_not_found():
    """send_to_player() with unknown player does not raise (logs warning)."""
    manager = WSManager()

    # Should not raise
    await manager.send_to_player("ghost", {"action": "vote"})


@pytest.mark.asyncio
async def test_send_to_player_handles_send_failure():
    """send_to_player() handles exception from send_json gracefully."""
    manager = WSManager()
    ws = make_mock_ws()
    ws.send_json = AsyncMock(side_effect=Exception("broken pipe"))
    manager.player_sessions["Alice"] = ws

    # Should not raise
    await manager.send_to_player("Alice", {"data": "x"})


# === set_response_future / resolve_response ===


def test_set_response_future_stores_future():
    """set_response_future() stores future for player."""
    manager = WSManager()
    loop = asyncio.new_event_loop()
    future = loop.create_future()

    manager.set_response_future("Alice", future)

    assert manager.player_response_futures["Alice"] is future
    loop.close()


@pytest.mark.asyncio
async def test_resolve_response_sets_future_result():
    """resolve_response() resolves the pending future with the response."""
    manager = WSManager()
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    manager.player_response_futures["Alice"] = future

    manager.resolve_response("Alice", "I vote for Bob")

    assert future.done()
    assert future.result() == "I vote for Bob"


def test_resolve_response_no_pending_future():
    """resolve_response() with no pending future does not raise."""
    manager = WSManager()

    # Should not raise
    manager.resolve_response("nobody", "some response")


@pytest.mark.asyncio
async def test_resolve_response_already_done_future():
    """resolve_response() skips already-done futures."""
    manager = WSManager()
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    future.set_result("already set")
    manager.player_response_futures["Alice"] = future

    # Should not raise
    manager.resolve_response("Alice", "new value")

    # Original result unchanged
    assert future.result() == "already set"


# === clear_sessions ===


def test_clear_sessions_removes_all_players():
    """clear_sessions() removes all player sessions."""
    manager = WSManager()
    manager.player_sessions["Alice"] = make_mock_ws()
    manager.player_sessions["Bob"] = make_mock_ws()

    manager.clear_sessions()

    assert len(manager.player_sessions) == 0

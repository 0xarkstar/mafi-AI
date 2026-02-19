"""WebSocket endpoint and helpers."""

import re
import uuid
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from src.api.validators import validate_player_name
from src.models.events import WSEvent
from src.utils.logger import get_logger

log = get_logger(__name__)


async def _handle_lobby_join(
    ws: WebSocket,
    data: dict,
    ws_manager,
    app_state,
    is_rejoin: bool = False,
) -> None:
    """Shared logic for join_lobby and rejoin_lobby messages.

    Args:
        ws: WebSocket connection.
        data: Message data dict.
        ws_manager: WSManager instance.
        app_state: FastAPI app.state.
        is_rejoin: True for rejoin_lobby (broadcast only on success), False for join_lobby.
    """
    default_name = "" if is_rejoin else f"Human-{str(uuid.uuid4())[:6]}"
    player_name = data.get("name", default_name)
    avatar_index = data.get("avatar_index")
    wallet_address = data.get("wallet_address")

    error = validate_player_name(player_name)
    if error:
        await ws.send_json({"type": "error", "message": f"Invalid player name: {error}"})
        return

    await ws_manager.register_player(player_name, ws)

    if hasattr(app_state, "lobby_manager") and app_state.lobby_manager:
        from src.players.human import HumanPlayer

        async def _send(msg: dict, _name: str = player_name) -> None:
            await ws_manager.send_to_player(_name, msg)

        player = HumanPlayer(name=player_name, send_to_player=_send, wallet_address=wallet_address)
        success = app_state.lobby_manager.join(player, metadata={"avatar_index": avatar_index})

        lobby_status = app_state.lobby_manager.get_lobby_status()
        await ws.send_json(
            {
                "type": "lobby_joined",
                "data": {
                    "name": player_name,
                    "success": success,
                    "players": [p["name"] for p in lobby_status["players"]],
                },
            }
        )

        # Register wallet and send initial balance if wallet provided
        if wallet_address:
            ws_manager.register_wallet(ws, wallet_address)
            balance_mgr = getattr(app_state, "balance_manager", None)
            if balance_mgr:
                balance = balance_mgr.get_balance(wallet_address)
                await ws.send_json({"type": "balance_update", "data": {"balance": float(balance)}})

        # join_lobby always broadcasts; rejoin_lobby only broadcasts on success
        if not is_rejoin or success:
            await ws_manager.broadcast(
                WSEvent(
                    event_type="lobby_status",
                    data=lobby_status,
                    game_id="",
                    timestamp=datetime.now().isoformat(),
                )
            )
    else:
        await ws.send_json(
            {
                "type": "lobby_joined",
                "data": {"name": player_name, "success": False, "players": []},
            }
        )


async def websocket_endpoint(ws: WebSocket) -> None:
    """WebSocket endpoint for real-time game events.

    Args:
        ws: WebSocket connection.
    """
    app = ws.scope["app"]
    ws_manager = app.state.ws_manager
    await ws_manager.connect(ws)

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "join_lobby":
                await _handle_lobby_join(ws, data, ws_manager, app.state, is_rejoin=False)

            elif data.get("type") == "rejoin_lobby":
                await _handle_lobby_join(ws, data, ws_manager, app.state, is_rejoin=True)

            elif data.get("type") == "action_response":
                player_name = data.get("player_name")
                response = data.get("response")

                if not player_name or not isinstance(player_name, str):
                    await ws.send_json({
                        "type": "error",
                        "message": "Invalid action_response: player_name must be a non-empty string",
                    })
                    continue

                if not response or not isinstance(response, str):
                    await ws.send_json({
                        "type": "error",
                        "message": "Invalid action_response: response must be a non-empty string",
                    })
                    continue

                if hasattr(app.state, "lobby_manager") and app.state.lobby_manager:
                    player = app.state.lobby_manager.players.get(player_name)
                    if player and hasattr(player, "set_response"):
                        player.set_response(response)
                        log.info("human_response_routed", name=player_name)
                    else:
                        log.warning("action_response_no_player", name=player_name)
                        ws_manager.resolve_response(player_name, response)
                else:
                    ws_manager.resolve_response(player_name, response)

            elif data.get("type") == "place_bet":
                log.info("bet_via_ws", data=data)
                from decimal import Decimal as D

                try:
                    betting_mgr = app.state.betting_manager
                    if not betting_mgr:
                        await ws.send_json({
                            "type": "bet_rejected",
                            "data": {"reason": "Betting not enabled"},
                        })
                        continue

                    wallet_address = (
                        data.get("wallet_address")
                        or ws_manager.get_wallet_for_ws(ws)
                        or f"ws:{id(ws)}"
                    )
                    amount = D(str(data.get("amount_usdc", 0)))

                    balance_mgr = getattr(app.state, "balance_manager", None)
                    if balance_mgr and not balance_mgr.deduct(wallet_address, amount):
                        await ws.send_json({
                            "type": "bet_rejected",
                            "data": {"reason": "Insufficient balance"},
                        })
                        continue

                    bet = betting_mgr.place_bet(
                        bettor_address=wallet_address,
                        bet_type=data.get("bet_type"),
                        target=data.get("target"),
                        amount_usdc=amount,
                        round_number=data.get("round", 0),
                        tx_hash=None,
                    )
                    if bet:
                        response_data = {
                            "bet_id": data.get("bet_id"),
                            "bet_type": bet.bet_type.value,
                            "target": bet.target,
                            "amount_usdc": float(bet.amount),
                        }
                        if balance_mgr:
                            response_data["balance"] = float(balance_mgr.get_balance(wallet_address))
                        await ws.send_json({
                            "type": "bet_confirmed",
                            "data": response_data,
                        })
                    else:
                        # Refund if bet placement failed after deduction
                        if balance_mgr:
                            balance_mgr.credit(wallet_address, amount)
                        await ws.send_json({
                            "type": "bet_rejected",
                            "data": {"reason": "Invalid bet parameters"},
                        })
                except Exception as exc:
                    log.error("ws_bet_error", error=str(exc))
                    await ws.send_json({
                        "type": "bet_rejected",
                        "data": {"reason": "Bet processing failed"},
                    })

            elif data.get("type") == "register_wallet":
                wallet = data.get("wallet_address")
                if wallet and isinstance(wallet, str) and wallet.startswith("0x"):
                    ws_manager.register_wallet(ws, wallet)
                    balance_mgr = getattr(app.state, "balance_manager", None)
                    if balance_mgr:
                        balance = balance_mgr.get_balance(wallet)
                        await ws.send_json({"type": "balance_update", "data": {"balance": float(balance)}})

            elif data.get("type") == "join_spec_chat":
                raw_name = data.get("name", "").strip()
                # Sanitize: alphanumeric + underscore, max 16 chars
                sanitized = re.sub(r"[^a-zA-Z0-9_]", "", raw_name)[:16]
                if not sanitized:
                    sanitized = f"spec_{str(uuid.uuid4())[:6]}"
                # Avoid collisions with existing spectator names
                base = sanitized
                counter = 1
                while ws_manager.spectator_sessions.get(sanitized) is not None:
                    sanitized = f"{base}_{counter}"
                    counter += 1
                ws_manager.register_spectator(sanitized, ws)
                await ws.send_json({
                    "type": "spec_chat_joined",
                    "data": {"name": sanitized},
                })

            elif data.get("type") == "spec_chat":
                text = data.get("text", "").strip()[:200]
                if not text:
                    continue
                if not ws_manager.check_rate_limit(ws):
                    await ws.send_json({
                        "type": "spec_chat_error",
                        "data": {"reason": "Rate limited — wait a few seconds"},
                    })
                    continue
                sender = ws_manager.get_spectator_name(ws)
                if not sender:
                    await ws.send_json({
                        "type": "spec_chat_error",
                        "data": {"reason": "Join spectator chat first"},
                    })
                    continue
                # Broadcast to all connected clients
                await ws_manager.broadcast(
                    WSEvent(
                        event_type="spec_chat_message",
                        data={"name": sender, "text": text, "isAi": False},
                        game_id="",
                        timestamp=datetime.now().isoformat(),
                    )
                )

            elif data.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
        log.info("ws_client_disconnected")

    except Exception as exc:
        log.error("ws_error", error=str(exc))
        ws_manager.disconnect(ws)

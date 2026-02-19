"""WebSocket endpoint and helpers."""

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

    error = validate_player_name(player_name)
    if error:
        await ws.send_json({"type": "error", "message": f"Invalid player name: {error}"})
        return

    await ws_manager.register_player(player_name, ws)

    if hasattr(app_state, "lobby_manager") and app_state.lobby_manager:
        from src.players.human import HumanPlayer

        async def _send(msg: dict, _name: str = player_name) -> None:
            await ws_manager.send_to_player(_name, msg)

        player = HumanPlayer(name=player_name, send_to_player=_send)
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

                    bet = betting_mgr.place_bet(
                        bettor_address=f"ws:{id(ws)}",
                        bet_type=data.get("bet_type"),
                        target=data.get("target"),
                        amount_usdc=D(str(data.get("amount_usdc", 0))),
                        round_number=data.get("round", 0),
                        tx_hash=None,
                    )
                    if bet:
                        await ws.send_json({
                            "type": "bet_confirmed",
                            "data": {
                                "bet_id": data.get("bet_id"),
                                "bet_type": bet.bet_type.value,
                                "target": bet.target,
                                "amount_usdc": float(bet.amount),
                            },
                        })
                    else:
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

            elif data.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
        log.info("ws_client_disconnected")

    except Exception as exc:
        log.error("ws_error", error=str(exc))
        ws_manager.disconnect(ws)

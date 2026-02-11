"""Main AI Bettor client that orchestrates betting."""

import asyncio
import json
import time
from decimal import Decimal

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from src.ai_bettor.analyzer import GameAnalyzer
from src.ai_bettor.models import AIBettorState, GameObservation
from src.ai_bettor.strategy import BettingStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AIBettorClient:
    """Main AI Bettor client that watches games and places bets."""

    def __init__(
        self,
        ws_url: str,
        api_url: str,
        api_key: str,
        budget_usdc: Decimal,
        model: str = "gpt-4o-mini",
    ):
        """Initialize AI Bettor client.

        Args:
            ws_url: WebSocket URL (e.g., ws://localhost:8080/ws)
            api_url: REST API base URL (e.g., http://localhost:8080)
            api_key: OpenAI API key for analysis
            budget_usdc: Starting budget in USDC
            model: OpenAI model to use
        """
        self.ws_url = ws_url
        self.api_url = api_url
        self.budget_usdc = budget_usdc
        self.model = model

        self.analyzer = GameAnalyzer(api_key, model)
        self.strategy = BettingStrategy()
        self.http_client = httpx.AsyncClient(timeout=10.0)

        # Initialize state
        self.state = AIBettorState(
            balance_usdc=budget_usdc,
            bets_placed=0,
            last_bet_time=None,
            total_wagered=Decimal("0"),
            total_won=Decimal("0"),
        )

        # Event accumulation for building observations
        self.current_game_id: str | None = None
        self.current_phase = "lobby"
        self.current_round = 0
        self.alive_agents: list[str] = []
        self.dead_agents: list[str] = []
        self.recent_events: list[str] = []
        self.current_odds: dict[str, Decimal] = {}

        self._running = False

    async def run(self):
        """Main loop: connect WebSocket, listen events, maybe bet."""
        self._running = True
        retry_delay = 1.0

        while self._running:
            try:
                logger.info("connecting_to_websocket", url=self.ws_url)
                async with websockets.connect(self.ws_url) as websocket:
                    logger.info("websocket_connected")
                    retry_delay = 1.0  # Reset on successful connection

                    async for message in websocket:
                        if not self._running:
                            break

                        try:
                            event = json.loads(message)
                            await self._handle_event(event)
                        except json.JSONDecodeError:
                            logger.warning("invalid_json_received", message=message)
                        except Exception as e:
                            logger.error("event_handling_error", error=str(e))

            except ConnectionClosed:
                if self._running:
                    logger.warning(
                        "websocket_connection_closed", retry_in=retry_delay
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff
            except Exception as e:
                if self._running:
                    logger.error("websocket_error", error=str(e), retry_in=retry_delay)
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)

        logger.info("ai_bettor_stopped")

    async def stop(self):
        """Stop the bettor client."""
        self._running = False
        await self.http_client.aclose()

    async def _handle_event(self, event: dict):
        """Handle incoming WebSocket event."""
        event_type = event.get("event_type")
        data = event.get("data", {})
        game_id = event.get("game_id")

        # Update game_id if present
        if game_id:
            self.current_game_id = game_id

        # Handle different event types
        if event_type == "game_started":
            self._reset_game_state(game_id)
            self.current_phase = data.get("phase", "lobby")
            self.alive_agents = list(data.get("alive_agents", []))
            self._add_event(f"Game started with {len(self.alive_agents)} players")

        elif event_type == "phase_change":
            self.current_phase = data.get("phase", self.current_phase)
            self.current_round = data.get("round_number", self.current_round)
            self._add_event(f"Phase changed to {self.current_phase}")

            # Consider betting on phase change
            observation = self._build_observation()
            if observation:
                await self._maybe_place_bet(observation)

        elif event_type == "odds_update":
            # Update odds board
            odds_data = data.get("odds", {})
            self.current_odds = {k: Decimal(str(v)) for k, v in odds_data.items()}
            self._add_event("Odds updated")

            # Consider betting on odds update
            observation = self._build_observation()
            if observation:
                await self._maybe_place_bet(observation)

        elif event_type == "elimination":
            eliminated = data.get("agent")
            if eliminated:
                if eliminated in self.alive_agents:
                    self.alive_agents.remove(eliminated)
                if eliminated not in self.dead_agents:
                    self.dead_agents.append(eliminated)
                self._add_event(f"{eliminated} was eliminated")

        elif event_type == "agent_message":
            agent = data.get("agent", "Unknown")
            message = data.get("message", "")[:100]  # Truncate
            self._add_event(f"{agent}: {message}")

        elif event_type == "vote":
            voter = data.get("voter", "Unknown")
            target = data.get("target", "Unknown")
            self._add_event(f"{voter} voted for {target}")

        elif event_type == "game_over":
            winner = data.get("winner", "Unknown")
            self._add_event(f"Game over! {winner} won")
            self.current_phase = "game_over"

    def _reset_game_state(self, game_id: str):
        """Reset accumulated game state for new game."""
        self.current_game_id = game_id
        self.current_phase = "lobby"
        self.current_round = 0
        self.alive_agents = []
        self.dead_agents = []
        self.recent_events = []
        self.current_odds = {}
        logger.info("game_state_reset", game_id=game_id)

    def _add_event(self, event: str):
        """Add event to recent events (rolling window of 10)."""
        self.recent_events.append(event)
        if len(self.recent_events) > 10:
            self.recent_events = self.recent_events[-10:]

    def _build_observation(self) -> GameObservation | None:
        """Build observation from accumulated events."""
        if not self.current_game_id:
            return None

        return GameObservation(
            game_id=self.current_game_id,
            phase=self.current_phase,
            round_number=self.current_round,
            alive_agents=tuple(self.alive_agents),
            dead_agents=tuple(self.dead_agents),
            recent_events=tuple(self.recent_events),
            current_odds=dict(self.current_odds),
        )

    async def _maybe_place_bet(self, observation: GameObservation):
        """Consider placing a bet based on current observation."""
        # Check strategy timing/cooldown
        if not self.strategy.should_bet_now(observation, self.state):
            logger.debug(
                "bet_skipped_by_strategy",
                phase=observation.phase,
                balance=float(self.state.balance_usdc),
            )
            return

        # Get AI decision
        decision = await self.analyzer.analyze_and_decide(
            observation, self.state.balance_usdc
        )

        if not decision.should_bet:
            logger.debug("ai_decided_not_to_bet", reasoning=decision.reasoning)
            return

        # Calculate amount based on confidence
        amount = self.strategy.calculate_amount(
            decision.confidence, self.state.balance_usdc
        )

        if amount <= 0:
            logger.debug(
                "bet_amount_too_low",
                confidence=decision.confidence,
                balance=float(self.state.balance_usdc),
            )
            return

        # Place the bet
        success = await self._place_bet_via_api(
            game_id=observation.game_id,
            bet_type=decision.bet_type,
            target=decision.target,
            amount=amount,
        )

        if success:
            # Update state immutably
            self.state = self.state.model_copy(
                update={
                    "balance_usdc": self.state.balance_usdc - amount,
                    "bets_placed": self.state.bets_placed + 1,
                    "last_bet_time": time.time(),
                    "total_wagered": self.state.total_wagered + amount,
                }
            )
            logger.info(
                "bet_placed",
                bet_type=decision.bet_type,
                target=decision.target,
                amount=float(amount),
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )

    async def _place_bet_via_api(
        self, game_id: str, bet_type: str, target: str, amount: Decimal
    ) -> bool:
        """Place bet via REST API.

        Args:
            game_id: Game ID
            bet_type: Type of bet
            target: Bet target
            amount: Bet amount in USDC

        Returns:
            True if bet was placed successfully
        """
        try:
            url = f"{self.api_url}/api/bets/x402"
            payload = {
                "game_id": game_id,
                "bet_type": bet_type,
                "target": target,
                "amount_usdc": float(amount),
                "round": self.current_round,
            }

            response = await self.http_client.post(url, json=payload)

            if response.status_code == 200:
                logger.info("bet_api_success", response=response.json())
                return True
            else:
                logger.warning(
                    "bet_api_failed",
                    status=response.status_code,
                    response=response.text,
                )
                return False

        except Exception as e:
            logger.error("bet_api_error", error=str(e))
            return False

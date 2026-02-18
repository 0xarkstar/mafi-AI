"""Tests for Database and Repositories in src/storage/."""

import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from src.config.constants import BetType, Phase, Role
from src.models.betting import Bet
from src.models.game import GameState, RoundResult
from src.storage.database import Database
from src.storage.repositories.bet_repo import BetRepository
from src.storage.repositories.game_repo import GameRepository


# === Fixtures ===


@pytest.fixture
async def db():
    """Create a real in-memory-style database using a temp file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database = Database(db_path)
        await database.connect()
        yield database
        await database.disconnect()


@pytest.fixture
async def game_repo(db):
    """Create GameRepository with connected database."""
    return GameRepository(db)


@pytest.fixture
async def bet_repo(db):
    """Create BetRepository with connected database."""
    return BetRepository(db)


@pytest.fixture
def sample_game() -> GameState:
    """Create a sample GameState for testing."""
    return GameState(
        game_id="test-game-001",
        phase=Phase.NIGHT,
        round_number=0,
        alive_agents=("Agent1", "Agent2", "Agent3", "Agent4", "Agent5", "Agent6", "Agent7"),
        dead_agents=tuple(),
        role_map={
            "Agent1": Role.MAFIA,
            "Agent2": Role.MAFIA,
            "Agent3": Role.DETECTIVE,
            "Agent4": Role.CITIZEN,
            "Agent5": Role.CITIZEN,
            "Agent6": Role.CITIZEN,
            "Agent7": Role.CITIZEN,
        },
        rounds=tuple(),
        winner=None,
    )


@pytest.fixture
def sample_bet() -> Bet:
    """Create a sample Bet for testing."""
    return Bet(
        bet_id="bet-001",
        game_id="test-game-001",
        bettor_id="0xBettor123",
        bet_type=BetType.SIDE_WIN,
        target="citizens",
        amount=Decimal("5.00"),
        round_placed=0,
        weight=Decimal("1.5"),
    )


# === Database Tests ===


@pytest.mark.asyncio
async def test_database_connects_successfully(db):
    """Database.connect() establishes a connection."""
    assert db.connection is not None


@pytest.mark.asyncio
async def test_database_creates_migrations_table(db):
    """connect() creates the _migrations tracking table."""
    row = await db.fetchone(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'"
    )
    assert row is not None


@pytest.mark.asyncio
async def test_database_creates_games_table(db):
    """Migrations create the games table."""
    row = await db.fetchone(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='games'"
    )
    assert row is not None


@pytest.mark.asyncio
async def test_database_creates_bets_table(db):
    """Migrations create the bets table."""
    row = await db.fetchone(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bets'"
    )
    assert row is not None


@pytest.mark.asyncio
async def test_database_migrations_not_reapplied(db):
    """Running connect() again (via _run_migrations) skips already-applied migrations."""
    # Call _run_migrations again manually — should not error or duplicate
    await db._run_migrations()

    rows = await db.fetchall("SELECT filename FROM _migrations")
    filenames = [row["filename"] for row in rows]
    # Should have exactly one entry per migration (no duplicates)
    assert len(filenames) == len(set(filenames))


@pytest.mark.asyncio
async def test_database_connection_property_raises_when_not_connected():
    """connection property raises RuntimeError when not connected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "not_connected.db"
        database = Database(db_path)
        with pytest.raises(RuntimeError, match="not connected"):
            _ = database.connection


@pytest.mark.asyncio
async def test_database_disconnect_sets_db_to_none():
    """disconnect() sets _db to None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "disconnect_test.db"
        database = Database(db_path)
        await database.connect()
        assert database._db is not None

        await database.disconnect()
        assert database._db is None


@pytest.mark.asyncio
async def test_database_execute_and_fetchone(db):
    """execute() and fetchone() work correctly."""
    await db.execute(
        "INSERT INTO spectators (session_id, chips) VALUES (?, ?)",
        ("sess-1", 500.0),
    )
    await db.commit()

    row = await db.fetchone("SELECT chips FROM spectators WHERE session_id = ?", ("sess-1",))
    assert row is not None
    assert row["chips"] == 500.0


@pytest.mark.asyncio
async def test_database_fetchall_returns_all_rows(db):
    """fetchall() returns all matching rows."""
    for i in range(3):
        await db.execute(
            "INSERT INTO spectators (session_id, chips) VALUES (?, ?)",
            (f"sess-{i}", float(1000 + i * 100)),
        )
    await db.commit()

    rows = await db.fetchall("SELECT session_id FROM spectators")
    assert len(rows) >= 3


@pytest.mark.asyncio
async def test_database_executemany(db):
    """executemany() inserts multiple rows."""
    params = [(f"multi-{i}", float(i * 10)) for i in range(5)]
    await db.executemany(
        "INSERT INTO spectators (session_id, chips) VALUES (?, ?)", params
    )
    await db.commit()

    rows = await db.fetchall("SELECT session_id FROM spectators WHERE session_id LIKE 'multi-%'")
    assert len(rows) == 5


# === GameRepository Tests ===


@pytest.mark.asyncio
async def test_game_repo_save_and_find(game_repo, sample_game):
    """save() persists game, find_by_id() retrieves it."""
    await game_repo.save(sample_game)

    found = await game_repo.find_by_id("test-game-001")

    assert found is not None
    assert found.game_id == "test-game-001"
    assert found.phase == Phase.NIGHT
    assert found.round_number == 0
    assert found.winner is None


@pytest.mark.asyncio
async def test_game_repo_find_nonexistent_returns_none(game_repo):
    """find_by_id() returns None for unknown game_id."""
    result = await game_repo.find_by_id("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_game_repo_save_restores_role_map(game_repo, sample_game):
    """Saved role_map is correctly deserialized."""
    await game_repo.save(sample_game)

    found = await game_repo.find_by_id("test-game-001")
    assert found.role_map["Agent1"] == Role.MAFIA
    assert found.role_map["Agent3"] == Role.DETECTIVE
    assert found.role_map["Agent4"] == Role.CITIZEN


@pytest.mark.asyncio
async def test_game_repo_save_restores_alive_and_dead_agents(game_repo, sample_game):
    """Saved alive_agents and dead_agents are correctly deserialized."""
    await game_repo.save(sample_game)

    found = await game_repo.find_by_id("test-game-001")
    assert "Agent1" in found.alive_agents
    assert len(found.dead_agents) == 0


@pytest.mark.asyncio
async def test_game_repo_upsert_updates_existing(game_repo, sample_game):
    """Saving the same game_id twice updates the record (upsert)."""
    await game_repo.save(sample_game)

    # Update game state: one agent eliminated, phase changed
    updated = sample_game.model_copy(update={
        "phase": Phase.DAY_DISCUSSION,
        "round_number": 1,
        "winner": "citizens",
    })
    await game_repo.save(updated)

    found = await game_repo.find_by_id("test-game-001")
    assert found.phase == Phase.DAY_DISCUSSION
    assert found.round_number == 1
    assert found.winner == "citizens"


@pytest.mark.asyncio
async def test_game_repo_save_with_rounds(game_repo, sample_game):
    """Game with round results saves and restores rounds correctly."""
    round_result = RoundResult(
        round_number=0,
        phase=Phase.DAY_VOTE,
        eliminated="Agent1",
        eliminated_role=Role.MAFIA,
        votes={"Agent3": "Agent1", "Agent4": "Agent1"},
        night_kill="Agent5",
    )
    game_with_rounds = sample_game.model_copy(update={
        "rounds": (round_result,),
        "round_number": 1,
    })

    await game_repo.save(game_with_rounds)

    found = await game_repo.find_by_id("test-game-001")
    assert len(found.rounds) == 1
    assert found.rounds[0].eliminated == "Agent1"
    assert found.rounds[0].eliminated_role == Role.MAFIA
    assert found.rounds[0].night_kill == "Agent5"


@pytest.mark.asyncio
async def test_game_repo_update_state_is_alias_for_save(game_repo, sample_game):
    """update_state() is an alias for save()."""
    await game_repo.save(sample_game)

    updated = sample_game.model_copy(update={"winner": "mafia"})
    await game_repo.update_state(updated)

    found = await game_repo.find_by_id("test-game-001")
    assert found.winner == "mafia"


# === BetRepository Tests ===


@pytest.mark.asyncio
async def test_bet_repo_save_requires_game(bet_repo, game_repo, sample_game, sample_bet):
    """Saving a bet requires the game to exist (FK constraint)."""
    await game_repo.save(sample_game)
    await bet_repo.save(sample_bet)

    found = await bet_repo.find_by_id("bet-001")
    assert found is not None


@pytest.mark.asyncio
async def test_bet_repo_find_by_id(bet_repo, game_repo, sample_game, sample_bet):
    """find_by_id() returns the correct bet."""
    await game_repo.save(sample_game)
    await bet_repo.save(sample_bet)

    found = await bet_repo.find_by_id("bet-001")

    assert found is not None
    assert found.bet_id == "bet-001"
    assert found.game_id == "test-game-001"
    assert found.bettor_id == "0xBettor123"
    assert found.bet_type == BetType.SIDE_WIN
    assert found.target == "citizens"
    assert found.amount == Decimal("5.00")
    assert found.round_placed == 0
    assert found.weight == Decimal("1.5")


@pytest.mark.asyncio
async def test_bet_repo_find_nonexistent_returns_none(bet_repo):
    """find_by_id() returns None for unknown bet_id."""
    result = await bet_repo.find_by_id("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_bet_repo_find_by_game(bet_repo, game_repo, sample_game):
    """find_by_game() returns all bets for a game."""
    await game_repo.save(sample_game)

    bets = [
        Bet(
            bet_id=f"bet-{i:03d}",
            game_id="test-game-001",
            bettor_id=f"0xAddr{i}",
            bet_type=BetType.SIDE_WIN,
            target="citizens",
            amount=Decimal("2.00"),
            round_placed=0,
            weight=Decimal("1.0"),
        )
        for i in range(3)
    ]
    for bet in bets:
        await bet_repo.save(bet)

    found_bets = await bet_repo.find_by_game("test-game-001")

    assert len(found_bets) == 3
    bet_ids = {b.bet_id for b in found_bets}
    assert "bet-000" in bet_ids
    assert "bet-001" in bet_ids
    assert "bet-002" in bet_ids


@pytest.mark.asyncio
async def test_bet_repo_find_by_game_empty(bet_repo, game_repo, sample_game):
    """find_by_game() returns empty list when no bets exist."""
    await game_repo.save(sample_game)

    result = await bet_repo.find_by_game("test-game-001")
    assert result == []


@pytest.mark.asyncio
async def test_bet_repo_find_by_game_different_games(bet_repo, game_repo):
    """find_by_game() returns only bets for the specified game."""
    # Create two games
    for i in range(1, 3):
        game = GameState(
            game_id=f"game-{i:03d}",
            phase=Phase.NIGHT,
            round_number=0,
            alive_agents=tuple(f"A{j}" for j in range(7)),
            dead_agents=tuple(),
            role_map={f"A{j}": (Role.MAFIA if j < 2 else Role.CITIZEN) for j in range(7)},
            rounds=tuple(),
            winner=None,
        )
        await game_repo.save(game)

    # Save bets for game-001 only
    bet = Bet(
        bet_id="bet-g1",
        game_id="game-001",
        bettor_id="0xAddr",
        bet_type=BetType.SIDE_WIN,
        target="mafia",
        amount=Decimal("3.00"),
        round_placed=0,
    )
    await bet_repo.save(bet)

    # Query game-002 (no bets)
    result = await bet_repo.find_by_game("game-002")
    assert result == []

    # Query game-001 (has bets)
    result = await bet_repo.find_by_game("game-001")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_bet_repo_settle_bets(bet_repo, game_repo, sample_game, sample_bet):
    """settle_bets() updates settled=1 and payout for specified bets."""
    await game_repo.save(sample_game)
    await bet_repo.save(sample_bet)

    payouts = {"bet-001": Decimal("10.50")}
    await bet_repo.settle_bets("test-game-001", payouts)

    row = await bet_repo._db.fetchone(
        "SELECT settled, payout FROM bets WHERE bet_id = ?", ("bet-001",)
    )
    assert row is not None
    assert row["settled"] == 1
    assert abs(row["payout"] - 10.50) < 0.001

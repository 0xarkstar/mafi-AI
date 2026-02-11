"""SQLite database connection and migration manager."""

from pathlib import Path

import aiosqlite

from src.utils.logger import get_logger

log = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    async def connect(self) -> None:
        """Connect to SQLite and run migrations."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self._db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._run_migrations()
        log.info("database_connected", path=str(self._db_path))

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None
            log.info("database_disconnected")

    async def _run_migrations(self) -> None:
        """Run all SQL migration files in order."""
        db = self.connection
        await db.execute(
            "CREATE TABLE IF NOT EXISTS _migrations ("
            "  filename TEXT PRIMARY KEY,"
            "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        await db.commit()

        cursor = await db.execute("SELECT filename FROM _migrations")
        applied = {row["filename"] for row in await cursor.fetchall()}

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration_file in migration_files:
            if migration_file.name not in applied:
                log.info("applying_migration", filename=migration_file.name)
                sql = migration_file.read_text()
                await db.executescript(sql)
                await db.execute(
                    "INSERT INTO _migrations (filename) VALUES (?)",
                    (migration_file.name,),
                )
                await db.commit()
                log.info("migration_applied", filename=migration_file.name)

    async def execute(
        self, sql: str, params: tuple = ()
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement."""
        return await self.connection.execute(sql, params)

    async def executemany(
        self, sql: str, params_list: list[tuple]
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        return await self.connection.executemany(sql, params_list)

    async def fetchone(
        self, sql: str, params: tuple = ()
    ) -> aiosqlite.Row | None:
        """Execute and fetch one row."""
        cursor = await self.connection.execute(sql, params)
        return await cursor.fetchone()

    async def fetchall(
        self, sql: str, params: tuple = ()
    ) -> list[aiosqlite.Row]:
        """Execute and fetch all rows."""
        cursor = await self.connection.execute(sql, params)
        return await cursor.fetchall()

    async def commit(self) -> None:
        """Commit current transaction."""
        await self.connection.commit()

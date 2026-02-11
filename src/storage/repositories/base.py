"""Abstract base repository."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from src.storage.database import Database

T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """Abstract base for all repositories."""

    def __init__(self, db: Database) -> None:
        self._db = db

    @abstractmethod
    async def save(self, entity: T) -> None:
        """Persist an entity."""

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> T | None:
        """Find entity by ID."""

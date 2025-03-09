from typing import Generic, TypeVar, List, Optional, Dict, Any
from abc import ABC, abstractmethod

T = TypeVar('T')  # Generic type for the entity


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository that defines common operations for all repositories.
    """
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """Get an entity by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by its ID."""
        pass
    
    @abstractmethod
    def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """Find entities matching the given criteria."""
        pass 
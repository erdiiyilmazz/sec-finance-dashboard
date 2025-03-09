from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import json


@dataclass
class CacheEntry:
    """
    Represents a single entry in the data cache.
    """
    key: str
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def age(self) -> timedelta:
        """Get the age of this cache entry."""
        return datetime.now() - self.created_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CacheEntry":
        """Create a CacheEntry from a dictionary."""
        created_at = datetime.fromisoformat(data["created_at"])
        expires_at = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        
        return cls(
            key=data["key"],
            data=data["data"],
            created_at=created_at,
            expires_at=expires_at,
            metadata=data.get("metadata", {})
        )


@dataclass
class DataCache:
    """
    Represents a cache for SEC data to minimize API calls and ensure ethical data usage.
    """
    name: str
    entries: Dict[str, CacheEntry] = field(default_factory=dict)
    max_size: Optional[int] = None  # Maximum number of entries
    default_ttl: Optional[timedelta] = None  # Default time-to-live for entries
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        entry = self.entries.get(key)
        if entry is None or entry.is_expired:
            return None
        return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None, 
            metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set a value in the cache."""
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + ttl
        elif self.default_ttl is not None:
            expires_at = datetime.now() + self.default_ttl
            
        self.entries[key] = CacheEntry(
            key=key,
            data=value,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Enforce max size if specified
        if self.max_size and len(self.entries) > self.max_size:
            self._evict_oldest()
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if key in self.entries:
            del self.entries[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.entries.clear()
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry from the cache."""
        if not self.entries:
            return
            
        oldest_key = min(self.entries.items(), key=lambda x: x[1].created_at)[0]
        del self.entries[oldest_key]
    
    def save_to_file(self, filepath: str) -> None:
        """Save the cache to a file."""
        serialized = {
            "name": self.name,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
            "max_size": self.max_size,
            "default_ttl": self.default_ttl.total_seconds() if self.default_ttl else None
        }
        
        with open(filepath, 'w') as f:
            json.dump(serialized, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "DataCache":
        """Load a cache from a file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        cache = cls(
            name=data["name"],
            max_size=data.get("max_size"),
            default_ttl=timedelta(seconds=data["default_ttl"]) if data.get("default_ttl") else None
        )
        
        for key, entry_data in data.get("entries", {}).items():
            cache.entries[key] = CacheEntry.from_dict(entry_data)
        
        return cache 
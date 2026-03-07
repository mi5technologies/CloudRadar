"""Base cloud provider interface."""
from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base for AWS, Azure, GCP providers."""

    @abstractmethod
    def authenticate(self) -> bool:
        """Verify credentials and return True if valid."""
        pass

    @abstractmethod
    def get_account_id(self) -> str:
        """Return cloud account/subscription/project identifier."""
        pass

    @abstractmethod
    def get_regions(self) -> list[str]:
        """Return list of regions to scan."""
        pass

    @abstractmethod
    def discover_assets(self, asset_types: list[str] | None = None) -> dict[str, list[dict]]:
        """Discover assets; return dict of asset_type -> list of asset dicts."""
        pass

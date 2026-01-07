"""
Base provider class for all LLM search providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class SearchProvider(ABC):
    """Abstract base class for all LLM search providers."""

    def __init__(self, config: dict):
        """
        Initialize provider with configuration.

        Args:
            config: Full configuration dict from venues.toml
        """
        self.config = config
        self.provider_config = config.get("search_provider", {})

    @abstractmethod
    def search(self, query: str, query_info: dict) -> dict:
        """
        Execute a search query and return standardized results.

        Args:
            query: The search query string
            query_info: Metadata about the query (type, region, city, priority)

        Returns:
            dict with keys:
                - query_info: The input query_info dict
                - text: Search result text
                - success: bool indicating success
                - timestamp: ISO format timestamp
                - error: error message (if success=False)
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the provider is properly configured.

        Returns:
            True if properly configured, False otherwise
        """
        pass

    @abstractmethod
    def get_required_env_vars(self) -> list[str]:
        """
        Get list of required environment variables for this provider.

        Returns:
            List of environment variable names
        """
        pass

    def _standardize_result(
        self, raw_result: str, query_info: dict, success: bool = True, error: Optional[str] = None
    ) -> dict:
        """
        Convert provider-specific result to standard format.

        Args:
            raw_result: The text result from the provider
            query_info: Original query metadata
            success: Whether the search was successful
            error: Error message if success=False

        Returns:
            Standardized result dict
        """
        result = {
            "query_info": query_info,
            "text": raw_result,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

        if not success and error:
            result["error"] = error

        return result

    def get_provider_name(self) -> str:
        """Get the provider's name."""
        return self.__class__.__name__.replace("Provider", "").lower()

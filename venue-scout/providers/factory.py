"""
Provider factory for creating LLM search providers.
"""

from .base import SearchProvider
from .claude_provider import ClaudeProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider
from .mcp_provider import MCPProvider


# Provider registry
PROVIDERS = {
    "claude": ClaudeProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
    "mcp": MCPProvider,
}


def create_provider(provider_name: str, config: dict) -> SearchProvider:
    """
    Create a search provider instance by name.

    Args:
        provider_name: Name of the provider ("claude", "openrouter", "ollama", "mcp")
        config: Full configuration dict from venues.toml

    Returns:
        SearchProvider instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_name = provider_name.lower().strip()

    if provider_name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider: '{provider_name}'. Available providers: {available}"
        )

    provider_class = PROVIDERS[provider_name]
    return provider_class(config)


def list_providers() -> list[str]:
    """
    Get list of available provider names.

    Returns:
        List of provider names
    """
    return list(PROVIDERS.keys())

"""
Venue Scout - Multi-Provider LLM Integration

This package provides a unified interface for multiple LLM providers:
- Claude (Anthropic)
- OpenRouter (multiple models with web search)
- Ollama (local models)
- MCP (Model Context Protocol with various search servers)
"""

from .base import SearchProvider
from .factory import create_provider, list_providers
from .claude_provider import ClaudeProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider
from .mcp_provider import MCPProvider

__all__ = [
    "SearchProvider",
    "create_provider",
    "list_providers",
    "ClaudeProvider",
    "OpenRouterProvider",
    "OllamaProvider",
    "MCPProvider",
]

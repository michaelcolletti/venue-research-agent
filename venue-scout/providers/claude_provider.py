"""
Claude provider using Anthropic API with native web search.
"""

import os
import sys
from .base import SearchProvider

try:
    from anthropic import Anthropic
except ImportError:
    print("Warning: anthropic package not installed. Install with: pip install anthropic")
    Anthropic = None


class ClaudeProvider(SearchProvider):
    """Search provider using Claude API with native web_search tool."""

    def __init__(self, config: dict):
        super().__init__(config)

        # Get Claude-specific configuration
        claude_config = self.provider_config.get("claude", {})
        self.model = claude_config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = claude_config.get("max_tokens", 2000)
        self.web_search_tool_version = claude_config.get(
            "web_search_tool_version", "web_search_20250305"
        )

        # Initialize client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key and Anthropic:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None

    def get_required_env_vars(self) -> list[str]:
        """Return required environment variables."""
        return ["ANTHROPIC_API_KEY"]

    def validate_config(self) -> bool:
        """Validate Claude provider configuration."""
        if Anthropic is None:
            print("Error: anthropic package not installed")
            return False

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY environment variable not set")
            print("\nTo set up:")
            print("  export ANTHROPIC_API_KEY='sk-ant-...'")
            return False

        if not self.client:
            print("Error: Claude client not initialized")
            return False

        return True

    def search(self, query: str, query_info: dict) -> dict:
        """
        Execute search using Claude with web search tool.

        This preserves the exact logic from the original claude_search.py implementation.
        """
        system_prompt = """You are a venue research assistant helping a musician find
performance venues. When searching, focus on:
- Live music venues, bars, restaurants with live music
- Capacity and venue type when available
- Booking contact information if found
- Any mentions of venues seeking musicians

Format your findings as structured data."""

        user_message = f"""Search for: {query}

After searching, provide a structured summary of venues found with:
1. Venue name
2. City/Location
3. Venue type (bar, restaurant, theater, etc.)
4. Any booking/contact info found
5. Notable details (capacity, genres, etc.)

Also note any opportunities where venues are actively seeking musicians."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=[{"type": self.web_search_tool_version, "name": "web_search"}],
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract text content from response
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            return self._standardize_result(result_text, query_info, success=True)

        except Exception as e:
            error_msg = str(e)
            return self._standardize_result("", query_info, success=False, error=error_msg)

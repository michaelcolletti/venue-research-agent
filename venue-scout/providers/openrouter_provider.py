"""
OpenRouter provider with web search support via :online model suffix.
"""

import os
from .base import SearchProvider

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai package not installed. Install with: pip install openai")
    OpenAI = None


class OpenRouterProvider(SearchProvider):
    """
    Search provider using OpenRouter.ai with web search.

    OpenRouter provides access to multiple models with web search capability
    by using the :online suffix (e.g., "openai/gpt-4o:online").
    Web search is powered by Exa.ai with up to 5 results per request.
    """

    def __init__(self, config: dict):
        super().__init__(config)

        # Get OpenRouter-specific configuration
        openrouter_config = self.provider_config.get("openrouter", {})
        self.model = openrouter_config.get("model", "openai/gpt-4o:online")
        self.max_tokens = openrouter_config.get("max_tokens", 2000)
        self.max_search_results = openrouter_config.get("max_search_results", 5)

        # Ensure model has :online suffix for web search
        if ":online" not in self.model:
            print(
                f"Warning: Model '{self.model}' doesn't have :online suffix. "
                f"Adding it to enable web search."
            )
            self.model = f"{self.model}:online"

        # Initialize OpenRouter client (uses OpenAI SDK with custom base URL)
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key and OpenAI:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
        else:
            self.client = None

    def get_required_env_vars(self) -> list[str]:
        """Return required environment variables."""
        return ["OPENROUTER_API_KEY"]

    def validate_config(self) -> bool:
        """Validate OpenRouter provider configuration."""
        if OpenAI is None:
            print("Error: openai package not installed")
            return False

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: OPENROUTER_API_KEY environment variable not set")
            print("\nTo set up:")
            print("  1. Get API key from https://openrouter.ai/")
            print("  2. export OPENROUTER_API_KEY='sk-or-...'")
            return False

        if not self.client:
            print("Error: OpenRouter client not initialized")
            return False

        return True

    def search(self, query: str, query_info: dict) -> dict:
        """
        Execute search using OpenRouter with web search.

        OpenRouter automatically performs web search for models with :online suffix.
        The search is powered by Exa.ai and returns up to 5 results per request.
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
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            # Extract text from response
            result_text = response.choices[0].message.content

            return self._standardize_result(result_text, query_info, success=True)

        except Exception as e:
            error_msg = str(e)
            return self._standardize_result("", query_info, success=False, error=error_msg)

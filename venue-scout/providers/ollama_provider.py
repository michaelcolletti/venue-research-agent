"""
Ollama provider for local LLM models with web search support.
"""

import os
from .base import SearchProvider

try:
    import ollama
except ImportError:
    print("Warning: ollama package not installed. Install with: pip install ollama")
    ollama = None


class OllamaProvider(SearchProvider):
    """
    Search provider using local Ollama models with web search.

    Ollama provides free local model execution. Web search can be enabled
    through Ollama's built-in function calling or via MCP integration.
    Requires Ollama to be running locally (default: http://localhost:11434).
    """

    def __init__(self, config: dict):
        super().__init__(config)

        # Get Ollama-specific configuration
        ollama_config = self.provider_config.get("ollama", {})
        self.model = ollama_config.get("model", "llama3.1:latest")
        self.base_url = ollama_config.get("base_url", "http://localhost:11434")
        self.max_tokens = ollama_config.get("max_tokens", 2000)
        self.enable_web_search = ollama_config.get("enable_web_search", True)

        # Set environment variable for Ollama base URL
        if self.base_url:
            os.environ["OLLAMA_HOST"] = self.base_url

        self.client = ollama if ollama else None

    def get_required_env_vars(self) -> list[str]:
        """Return required environment variables (none required, but OLLAMA_HOST optional)."""
        return []  # Ollama is optional/local

    def validate_config(self) -> bool:
        """Validate Ollama provider configuration."""
        if ollama is None:
            print("Error: ollama package not installed")
            print("Install with: pip install ollama")
            return False

        try:
            # Test connection to Ollama
            models = ollama.list()
            print(f"Connected to Ollama at {self.base_url}")

            # Check if requested model is available
            available_models = [m["name"] for m in models.get("models", [])]
            if self.model not in available_models:
                print(f"Warning: Model '{self.model}' not found locally")
                print(f"Available models: {', '.join(available_models)}")
                print(f"\nPull the model with: ollama pull {self.model}")
                return False

            return True

        except Exception as e:
            print(f"Error: Cannot connect to Ollama at {self.base_url}")
            print(f"Details: {e}")
            print("\nMake sure Ollama is running:")
            print("  1. Install Ollama from https://ollama.ai/")
            print(f"  2. Pull a model: ollama pull {self.model}")
            print("  3. Start Ollama service")
            return False

    def search(self, query: str, query_info: dict) -> dict:
        """
        Execute search using Ollama with web search function.

        Note: Ollama's web search support is still evolving. This implementation
        uses a basic prompt-based approach. For better web search, consider using
        the MCP provider with Ollama as the LLM backend.
        """
        system_prompt = """You are a venue research assistant helping a musician find
performance venues. When searching, focus on:
- Live music venues, bars, restaurants with live music
- Capacity and venue type when available
- Booking contact information if found
- Any mentions of venues seeking musicians

Format your findings as structured data.

Note: If you need to search the web, indicate what searches would be helpful.
In production, web search would be performed via external tools."""

        user_message = f"""Search for: {query}

Provide a structured summary of venues that match this query with:
1. Venue name
2. City/Location
3. Venue type (bar, restaurant, theater, etc.)
4. Any booking/contact info
5. Notable details (capacity, genres, etc.)

Also note any opportunities where venues are actively seeking musicians.

Based on your knowledge, what information can you provide about venues matching this query?"""

        try:
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                options={
                    "num_predict": self.max_tokens,
                },
            )

            # Extract text from response
            result_text = response.get("message", {}).get("content", "")

            # Note: Ollama doesn't have native web search yet
            # This is a placeholder that works with local knowledge only
            note = (
                "\n\n[Note: Ollama response based on training data. "
                "For real-time web search, use MCP provider with Ollama as LLM backend.]"
            )
            result_text += note

            return self._standardize_result(result_text, query_info, success=True)

        except Exception as e:
            error_msg = str(e)
            return self._standardize_result("", query_info, success=False, error=error_msg)

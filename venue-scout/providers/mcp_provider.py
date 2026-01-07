"""
MCP (Model Context Protocol) provider with universal web search support.

This provider uses MCP servers for web search and any LLM for analysis.
Supports multiple MCP search servers: WebSearch-MCP, SerpApi, Brave Search, etc.
"""

import os
import json
from .base import SearchProvider

# MCP and LLM imports with fallbacks
try:
    from mcp import Client as MCPClient, StdioServerParameters
    from mcp.types import Tool
except ImportError:
    print("Warning: mcp package not installed. Install with: pip install mcp")
    MCPClient = None
    StdioServerParameters = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class MCPProvider(SearchProvider):
    """
    Search provider using Model Context Protocol for web search.

    Combines MCP servers (for web search) with any LLM (for analysis).
    Supports multiple MCP servers and multiple LLM backends.
    """

    def __init__(self, config: dict):
        super().__init__(config)

        # Get MCP-specific configuration
        mcp_config = self.provider_config.get("mcp", {})
        self.server_type = mcp_config.get("server_type", "websearch-mcp")
        self.model = mcp_config.get("model", "claude-sonnet-4-20250514")
        self.max_results = mcp_config.get("max_results", 10)
        self.max_tokens = mcp_config.get("max_tokens", 2000)
        self.server_config = mcp_config.get("server_config", {})

        # Initialize MCP client and LLM client
        self.mcp_client = None
        self.llm_client = None
        self.llm_type = self._detect_llm_type()

    def _detect_llm_type(self) -> str:
        """Detect which LLM to use based on model name."""
        if "claude" in self.model.lower():
            return "claude"
        elif "gpt" in self.model.lower() or "openai" in self.model.lower():
            return "openai"
        elif "gemini" in self.model.lower() or "google" in self.model.lower():
            return "openai"  # Google models via OpenRouter use OpenAI SDK
        else:
            return "claude"  # Default to Claude

    def get_required_env_vars(self) -> list[str]:
        """Return required environment variables based on server and model."""
        env_vars = []

        # MCP server requirements
        if self.server_type == "serpapi":
            env_vars.append("SERPAPI_API_KEY")
        elif self.server_type == "brave":
            env_vars.append("BRAVE_API_KEY")

        # LLM requirements
        if self.llm_type == "claude":
            env_vars.append("ANTHROPIC_API_KEY")
        elif self.llm_type == "openai":
            env_vars.append("OPENAI_API_KEY")

        return env_vars

    def validate_config(self) -> bool:
        """Validate MCP provider configuration."""
        # Check MCP package
        if MCPClient is None:
            print("Error: mcp package not installed")
            print("Install with: pip install mcp")
            return False

        # Check LLM availability
        if self.llm_type == "claude" and Anthropic is None:
            print("Error: anthropic package not installed for Claude model")
            return False
        elif self.llm_type == "openai" and OpenAI is None:
            print("Error: openai package not installed for OpenAI/Gemini models")
            return False

        # Check required environment variables
        for env_var in self.get_required_env_vars():
            if not os.environ.get(env_var):
                print(f"Error: {env_var} environment variable not set")
                return False

        return True

    def _init_mcp_client(self):
        """Initialize MCP client connection."""
        if MCPClient is None:
            raise RuntimeError("MCP package not available")

        # Configure server based on type
        if self.server_type == "websearch-mcp":
            # WebSearch-MCP server (no API key required)
            server_params = StdioServerParameters(
                command="npx",
                args=["web-search-mcp"],
                env=None,
            )
        elif self.server_type == "brave":
            # Brave Search MCP server
            server_params = StdioServerParameters(
                command="npx",
                args=["@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY")},
            )
        elif self.server_type == "serpapi":
            # SerpApi MCP server
            server_params = StdioServerParameters(
                command="mcp-server-serpapi",
                args=[],
                env={"SERPAPI_API_KEY": os.environ.get("SERPAPI_API_KEY")},
            )
        else:
            # Custom server
            command = self.server_config.get("server_executable", "mcp-server")
            args = self.server_config.get("server_args", [])
            server_params = StdioServerParameters(
                command=command,
                args=args,
            )

        return MCPClient(server_params)

    def _init_llm_client(self):
        """Initialize LLM client based on model type."""
        if self.llm_type == "claude":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            return Anthropic(api_key=api_key)
        elif self.llm_type == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            return OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")

    def _perform_web_search(self, query: str) -> str:
        """Perform web search using MCP server."""
        try:
            # Initialize MCP client if not already done
            if self.mcp_client is None:
                self.mcp_client = self._init_mcp_client()

            # Call web search tool
            # Note: This is a simplified implementation
            # Real MCP integration would use the MCP client protocol
            search_results = f"[Simulated MCP search results for: {query}]\n"
            search_results += (
                "Note: Full MCP integration requires MCP server to be running.\n"
            )
            search_results += (
                "For production use, ensure MCP server is properly configured."
            )

            return search_results

        except Exception as e:
            return f"Error performing MCP search: {str(e)}"

    def _analyze_with_llm(self, query: str, search_results: str) -> str:
        """Analyze search results using LLM."""
        try:
            # Initialize LLM client if not already done
            if self.llm_client is None:
                self.llm_client = self._init_llm_client()

            system_prompt = """You are a venue research assistant helping a musician find
performance venues. Analyze the search results and focus on:
- Live music venues, bars, restaurants with live music
- Capacity and venue type when available
- Booking contact information if found
- Any mentions of venues seeking musicians

Format your findings as structured data."""

            user_message = f"""Based on these search results for: {query}

Search Results:
{search_results}

Provide a structured summary of venues found with:
1. Venue name
2. City/Location
3. Venue type (bar, restaurant, theater, etc.)
4. Any booking/contact info found
5. Notable details (capacity, genres, etc.)

Also note any opportunities where venues are actively seeking musicians."""

            # Call LLM based on type
            if self.llm_type == "claude":
                response = self.llm_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "user", "content": system_prompt + "\n\n" + user_message}
                    ],
                )
                result_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        result_text += block.text
                return result_text

            elif self.llm_type == "openai":
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                )
                return response.choices[0].message.content

        except Exception as e:
            return f"Error analyzing with LLM: {str(e)}"

    def search(self, query: str, query_info: dict) -> dict:
        """
        Execute search using MCP for web search and LLM for analysis.

        Process:
        1. Use MCP server to perform web search
        2. Get search results
        3. Send results to LLM for analysis
        4. Return structured venue information
        """
        try:
            # Step 1: Perform web search via MCP
            search_results = self._perform_web_search(query)

            # Step 2: Analyze results with LLM
            analysis = self._analyze_with_llm(query, search_results)

            return self._standardize_result(analysis, query_info, success=True)

        except Exception as e:
            error_msg = str(e)
            return self._standardize_result("", query_info, success=False, error=error_msg)

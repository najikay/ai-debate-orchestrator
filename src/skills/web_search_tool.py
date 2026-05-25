"""WebSearchTool — HTTP-based web search via a configurable REST API.

API key and base URL are supplied at construction time (callers should
read them from the environment via ``python-dotenv``).  All queries are
sanitized before dispatch; HTTP errors and timeouts are surfaced as
:class:`~src.skills.base_skill.SkillError`.
"""

import requests

from src.skills.base_skill import AgentSkill, SkillError, SkillResult

_MAX_QUERY_LEN: int = 200
_TIMEOUT_SECONDS: float = 10.0


class WebSearchTool(AgentSkill):
    """Executes web searches against a REST search API.

    Args:
        api_key: Secret key sent in the ``X-API-Key`` request header.
        base_url: Base URL of the search endpoint (no trailing slash needed).

    Attributes:
        skill_name: Always ``"web_search"``.
        api_key: The API key used to authenticate requests.
        base_url: The search endpoint URL.

    Example::

        tool = WebSearchTool(api_key=os.getenv("SEARCH_API_KEY"),
                             base_url=os.getenv("SEARCH_BASE_URL"))
        result = tool.execute("climate change evidence 2025")
    """

    skill_name: str = "web_search"

    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key: str = api_key
        self.base_url: str = base_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, query: str) -> SkillResult:
        """Search the web for *query* and return structured snippets.

        Args:
            query: Raw search query string (will be sanitized internally).

        Returns:
            A :class:`SkillResult` with result snippets and the raw response.

        Raises:
            SkillError: On HTTP errors (4xx/5xx) or network timeouts.
        """
        clean = self._sanitize(query)
        try:
            response = requests.get(
                self.base_url,
                params={"q": clean},
                headers={"X-API-Key": self.api_key},
                timeout=_TIMEOUT_SECONDS,
            )
        except requests.Timeout:
            raise SkillError(f"Timeout after {_TIMEOUT_SECONDS}s querying '{clean}'.")

        if response.status_code != 200:
            raise SkillError(
                f"Search API returned HTTP {response.status_code} "
                f"for query '{clean}'."
            )

        return self._parse_response(query, response.json())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sanitize(self, query: str) -> str:
        """Strip whitespace and truncate *query* to :data:`_MAX_QUERY_LEN` chars.

        Args:
            query: Raw query string.

        Returns:
            Cleaned query string (may be empty if input was whitespace-only).
        """
        return query.strip()[:_MAX_QUERY_LEN]

    def _parse_response(self, query: str, raw: dict) -> SkillResult:
        """Convert a raw API response dict into a :class:`SkillResult`.

        Args:
            query: The original query string (stored in the result).
            raw: Parsed JSON response from the search API.

        Returns:
            A populated :class:`SkillResult`.

        Raises:
            SkillError: If ``results`` key is missing or the list is empty.
        """
        if "results" not in raw:
            raise SkillError("Search response missing 'results' key.")
        items = raw["results"]
        if not items:
            raise SkillError("Search response contained an empty results list.")
        snippets = [
            item.get("snippet", item.get("title", ""))
            for item in items
            if item.get("snippet") or item.get("title")
        ]
        return SkillResult(query=query, snippets=snippets, raw_response=raw)

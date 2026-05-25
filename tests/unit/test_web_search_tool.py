"""Unit tests for WebSearchTool.

TDD order:
    __init__ (api_key / base_url from env)
    → _sanitize (strip / truncate / whitespace-only)
    → _parse_response (SkillResult / missing key / empty results)
    → execute (happy / sanitize called / HTTP-500 / HTTP-429 / Timeout)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.skills.base_skill import SkillError, SkillResult
from src.skills.web_search_tool import WebSearchTool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_search_response() -> dict:
    """Valid search API JSON response with two result items."""
    return {
        "results": [
            {"title": "Result 1", "snippet": "Snippet one.", "url": "https://a.com"},
            {"title": "Result 2", "snippet": "Snippet two.", "url": "https://b.com"},
        ]
    }


@pytest.fixture
def tool(monkeypatch: pytest.MonkeyPatch) -> WebSearchTool:
    """WebSearchTool with env vars patched so no real key is required."""
    monkeypatch.setenv("SEARCH_API_KEY", "test-key-123")
    monkeypatch.setenv("SEARCH_BASE_URL", "https://api.test.example/search")
    return WebSearchTool(
        api_key="test-key-123",
        base_url="https://api.test.example/search",
    )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_web_search_tool_init_reads_api_key(tool: WebSearchTool) -> None:
    """api_key attribute is stored on the instance."""
    assert tool.api_key == "test-key-123"


def test_web_search_tool_init_reads_base_url(tool: WebSearchTool) -> None:
    """base_url attribute is stored on the instance."""
    assert tool.base_url == "https://api.test.example/search"


def test_web_search_tool_skill_name(tool: WebSearchTool) -> None:
    """skill_name is 'web_search'."""
    assert tool.skill_name == "web_search"


# ---------------------------------------------------------------------------
# _sanitize
# ---------------------------------------------------------------------------


def test_sanitize_strips_leading_and_trailing_whitespace(
    tool: WebSearchTool,
) -> None:
    """Leading and trailing whitespace is removed."""
    assert tool._sanitize("  hello world  ") == "hello world"


def test_sanitize_truncates_query_to_200_characters(tool: WebSearchTool) -> None:
    """Queries longer than 200 chars are truncated to exactly 200 chars."""
    long_query = "a" * 250
    result = tool._sanitize(long_query)
    assert len(result) == 200


def test_sanitize_returns_empty_string_for_whitespace_only_input(
    tool: WebSearchTool,
) -> None:
    """A query consisting entirely of whitespace sanitizes to an empty string."""
    assert tool._sanitize("   \t\n  ") == ""


def test_sanitize_preserves_normal_query(tool: WebSearchTool) -> None:
    """A well-formed query is returned unchanged."""
    assert tool._sanitize("AI debate systems") == "AI debate systems"


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


def test_parse_response_returns_skill_result_with_non_empty_snippets(
    tool: WebSearchTool, mock_search_response: dict
) -> None:
    """A valid response dict produces a SkillResult with at least one snippet."""
    result = tool._parse_response("test query", mock_search_response)
    assert isinstance(result, SkillResult)
    assert len(result.snippets) >= 1


def test_parse_response_snippets_contain_result_text(
    tool: WebSearchTool, mock_search_response: dict
) -> None:
    """Snippet text originates from the 'snippet' field of each result."""
    result = tool._parse_response("test query", mock_search_response)
    combined = " ".join(result.snippets)
    assert "Snippet one" in combined or "Snippet two" in combined


def test_parse_response_raises_skill_error_on_missing_results_key(
    tool: WebSearchTool,
) -> None:
    """SkillError raised when the 'results' key is absent from the response."""
    with pytest.raises(SkillError, match="results"):
        tool._parse_response("q", {"data": []})


def test_parse_response_raises_skill_error_on_empty_results_list(
    tool: WebSearchTool,
) -> None:
    """SkillError raised when 'results' is an empty list."""
    with pytest.raises(SkillError, match="empty"):
        tool._parse_response("q", {"results": []})


# ---------------------------------------------------------------------------
# execute — happy path
# ---------------------------------------------------------------------------


def test_execute_returns_skill_result_on_http_200(
    tool: WebSearchTool, mock_search_response: dict
) -> None:
    """execute returns a SkillResult when the API responds with 200."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_search_response

    with patch("requests.get", return_value=mock_resp):
        result = tool.execute("AI ethics")

    assert isinstance(result, SkillResult)
    assert result.query == "AI ethics"


def test_execute_calls_sanitize_before_dispatching_query(
    tool: WebSearchTool, mock_search_response: dict
) -> None:
    """_sanitize is invoked inside execute (verified via wrapping spy)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_search_response

    with patch("requests.get", return_value=mock_resp):
        with patch.object(tool, "_sanitize", wraps=tool._sanitize) as spy:
            tool.execute("  AI ethics  ")

    spy.assert_called_once_with("  AI ethics  ")


# ---------------------------------------------------------------------------
# execute — error paths
# ---------------------------------------------------------------------------


def test_execute_raises_skill_error_on_http_500(tool: WebSearchTool) -> None:
    """SkillError is raised when the API returns a 5xx status code."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(SkillError, match="500"):
            tool.execute("query")


def test_execute_raises_skill_error_on_http_429(tool: WebSearchTool) -> None:
    """SkillError is raised when the API returns 429 (rate limited)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(SkillError, match="429"):
            tool.execute("query")


def test_execute_raises_skill_error_on_requests_timeout(
    tool: WebSearchTool,
) -> None:
    """SkillError is raised when requests.get raises Timeout."""
    with patch("requests.get", side_effect=requests.Timeout):
        with pytest.raises(SkillError, match="[Tt]imeout"):
            tool.execute("query")

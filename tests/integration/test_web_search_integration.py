"""Integration test for WebSearchTool — requires live SEARCH_API_KEY.

Marked @pytest.mark.slow so it is excluded from the default unit-test run.
Run with: uv run pytest -m slow
"""

import os

import pytest

from src.skills.web_search_tool import WebSearchTool

pytestmark = pytest.mark.slow


@pytest.mark.slow
def test_web_search_live_returns_non_empty_snippets() -> None:
    """Live search returns at least one non-empty snippet.

    Skipped automatically when SEARCH_API_KEY or SEARCH_BASE_URL are absent.
    """
    api_key = os.getenv("SEARCH_API_KEY", "")
    base_url = os.getenv("SEARCH_BASE_URL", "")
    if not api_key or not base_url:
        pytest.skip("SEARCH_API_KEY or SEARCH_BASE_URL not set — skipping live test.")

    tool = WebSearchTool(api_key=api_key, base_url=base_url)
    result = tool.execute("artificial intelligence debate")
    assert len(result.snippets) >= 1
    assert all(isinstance(s, str) and s for s in result.snippets)

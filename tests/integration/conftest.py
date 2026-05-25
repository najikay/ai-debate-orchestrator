"""
Configuration for integration tests.

All tests in this package are automatically marked as `slow` — they make
live API calls and require ANTHROPIC_API_KEY and SEARCH_API_KEY in .env.

Skip the entire suite with: uv run pytest -m "not slow"
"""

import pytest

pytestmark = pytest.mark.slow

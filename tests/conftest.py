"""
Shared pytest configuration and fixtures for the AI Debate System test suite.

Marks:
    slow: Integration tests that make live API calls.
          Run with: uv run pytest -m slow
          Skip with: uv run pytest -m "not slow"
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (integration tests requiring live API calls)",
    )

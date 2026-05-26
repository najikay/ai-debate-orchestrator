"""Unit tests for the Flask web application.

TDD order:
    create_app (returns Flask app)
    → GET / (200 / contains form / contains Bootstrap)
    → POST /api/debate (missing topic / valid topic mocked / error path)
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ui.app import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    """Return a Flask test-client-ready app with testing=True."""
    flask_app = create_app(config_path="config/")
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# create_app
# ---------------------------------------------------------------------------


def test_create_app_returns_flask_instance(app) -> None:
    """create_app returns a Flask application object."""
    from flask import Flask
    assert isinstance(app, Flask)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


def test_index_route_returns_200(client) -> None:
    """GET / responds with HTTP 200."""
    resp = client.get("/")
    assert resp.status_code == 200


def test_index_route_contains_topic_input(client) -> None:
    """Index page HTML includes a text input for the debate topic."""
    resp = client.get("/")
    body = resp.data.decode()
    assert "topic" in body.lower()


def test_index_route_contains_bootstrap(client) -> None:
    """Index page references Bootstrap CSS."""
    resp = client.get("/")
    body = resp.data.decode()
    assert "bootstrap" in body.lower()


# ---------------------------------------------------------------------------
# POST /api/debate — validation
# ---------------------------------------------------------------------------


def test_api_debate_returns_400_when_topic_missing(client) -> None:
    """POST /api/debate with no topic returns HTTP 400."""
    resp = client.post(
        "/api/debate",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_api_debate_returns_400_when_topic_is_blank(client) -> None:
    """POST /api/debate with empty topic string returns HTTP 400."""
    resp = client.post(
        "/api/debate",
        data=json.dumps({"topic": "   "}),
        content_type="application/json",
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/debate — happy path (DebateEngine fully mocked)
# ---------------------------------------------------------------------------


def _make_mock_engine(topic: str = "test"):
    """Build a minimal DebateEngine mock that returns a plausible verdict."""
    from src.agents.base_agent import DebateMessage
    from src.agents.father_agent import Verdict
    from src.infrastructure.cost_reporter import CostSummary

    msg = DebateMessage(
        message_id="aaa",
        sender="pro_son",
        recipient="father",
        turn=1,
        content="Great argument.",
        sources=["http://example.com"],
        token_count=5,
        timestamp="2026-05-26T00:00:00+00:00",
    )
    verdict = Verdict(
        verdict_id="bbb",
        winner="pro_son",
        draw=False,
        reasoning="Pro Son was consistently clearer and better evidenced.",
        turn_count=20,
        timestamp="2026-05-26T01:00:00+00:00",
    )
    summary = CostSummary(
        per_agent={}, total_usd=0.05, budget_cap_usd=2.0, utilisation_pct=2.5
    )
    engine = MagicMock()
    engine.start.return_value = verdict
    engine.state_manager.state.transcript = [msg]
    engine.cost_reporter.compute.return_value = summary
    return engine


def test_api_debate_returns_200_on_success(client) -> None:
    """Mocked engine: POST /api/debate returns HTTP 200."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.post(
            "/api/debate",
            data=json.dumps({"topic": "AI is good"}),
            content_type="application/json",
        )
    assert resp.status_code == 200


def test_api_debate_response_contains_transcript(client) -> None:
    """Response JSON includes a non-empty transcript list."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.post(
            "/api/debate",
            data=json.dumps({"topic": "AI is good"}),
            content_type="application/json",
        )
    body = resp.get_json()
    assert "transcript" in body
    assert len(body["transcript"]) >= 1


def test_api_debate_response_contains_verdict(client) -> None:
    """Response JSON includes a verdict with winner and reasoning."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.post(
            "/api/debate",
            data=json.dumps({"topic": "AI is good"}),
            content_type="application/json",
        )
    body = resp.get_json()
    assert "verdict" in body
    assert body["verdict"]["winner"] in ("pro_son", "con_son")


def test_api_debate_response_contains_cost(client) -> None:
    """Response JSON includes a cost summary."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.post(
            "/api/debate",
            data=json.dumps({"topic": "AI is good"}),
            content_type="application/json",
        )
    body = resp.get_json()
    assert "cost" in body
    assert "total_usd" in body["cost"]


def test_api_debate_returns_500_on_engine_error(client) -> None:
    """Engine exception is caught and returned as HTTP 500."""
    broken = MagicMock()
    broken.start.side_effect = RuntimeError("boom")
    with patch("src.ui.app.DebateEngine", return_value=broken), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.post(
            "/api/debate",
            data=json.dumps({"topic": "AI is good"}),
            content_type="application/json",
        )
    assert resp.status_code == 500

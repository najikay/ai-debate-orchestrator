"""Unit tests for BaseAgent ABC.

TDD order:
    cannot instantiate directly
    → __init__ (agent_id / role / gatekeeper)
    → parse_response (valid JSON / JSONDecodeError / schema violation)
    → _validate_schema (valid / missing field / bad enum)
    → call_api (dispatches through gatekeeper / uses model / includes agent_id)
"""

import json
from unittest.mock import MagicMock

import pytest

from src.agents.base_agent import (
    AgentFailureError,
    BaseAgent,
    DebateMessage,
    MessageParseError,
)
from src.infrastructure.gatekeeper import APIResponse, Gatekeeper

# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------

_VALID_MSG = {
    "message_id": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "pro_son",
    "recipient": "father",
    "turn": 1,
    "content": "AI improves lives.",
    "sources": ["https://example.com"],
    "token_count": 10,
    "timestamp": "2026-05-25T12:00:00+00:00",
}


class ConcreteAgent(BaseAgent):
    """Minimal concrete subclass for testing BaseAgent in isolation."""

    def build_prompt(self, context: dict) -> str:
        return "prompt"

    def act(self, context: dict) -> DebateMessage:
        raw = json.dumps(_VALID_MSG)
        return self.parse_response(raw)


@pytest.fixture
def mock_gatekeeper() -> MagicMock:
    return MagicMock(spec=Gatekeeper)


@pytest.fixture
def mock_config() -> dict:
    return {
        "agents": {"concrete": {"model": "test-model"}},
        "agent_key": "concrete",
    }


@pytest.fixture
def agent(mock_gatekeeper: MagicMock, mock_config: dict) -> ConcreteAgent:
    return ConcreteAgent(
        agent_id="agent-1",
        role="pro",
        gatekeeper=mock_gatekeeper,
        config=mock_config,
        model="test-model",
    )


# ---------------------------------------------------------------------------
# Cannot instantiate directly
# ---------------------------------------------------------------------------


def test_base_agent_cannot_be_instantiated_directly(
    mock_gatekeeper: MagicMock, mock_config: dict
) -> None:
    """Direct instantiation of BaseAgent raises TypeError."""
    with pytest.raises(TypeError):
        BaseAgent(  # type: ignore[abstract]
            agent_id="x",
            role="r",
            gatekeeper=mock_gatekeeper,
            config=mock_config,
            model="m",
        )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_base_agent_init_sets_agent_id(agent: ConcreteAgent) -> None:
    """agent_id is stored as an attribute."""
    assert agent.agent_id == "agent-1"


def test_base_agent_init_sets_role(agent: ConcreteAgent) -> None:
    """role is stored as an attribute."""
    assert agent.role == "pro"


def test_base_agent_init_stores_gatekeeper_reference(
    agent: ConcreteAgent, mock_gatekeeper: MagicMock
) -> None:
    """The gatekeeper reference is stored on the instance."""
    assert agent.gatekeeper is mock_gatekeeper


def test_base_agent_init_stores_model(agent: ConcreteAgent) -> None:
    """model string is stored on the instance."""
    assert agent.model == "test-model"


# ---------------------------------------------------------------------------
# parse_response
# ---------------------------------------------------------------------------


def test_parse_response_returns_debate_message_on_valid_json(
    agent: ConcreteAgent,
) -> None:
    """A valid JSON string produces a DebateMessage dataclass."""
    raw = json.dumps(_VALID_MSG)
    msg = agent.parse_response(raw)
    assert isinstance(msg, DebateMessage)
    assert msg.content == "AI improves lives."


def test_parse_response_raises_message_parse_error_on_invalid_json(
    agent: ConcreteAgent,
) -> None:
    """A non-JSON string raises MessageParseError."""
    with pytest.raises(MessageParseError):
        agent.parse_response("not valid json {{")


def test_parse_response_raises_message_parse_error_on_schema_violation(
    agent: ConcreteAgent,
) -> None:
    """JSON that violates the DebateMessage schema raises MessageParseError."""
    bad = dict(_VALID_MSG)
    bad["sender"] = "invalid_role"  # not in enum
    with pytest.raises(MessageParseError):
        agent.parse_response(json.dumps(bad))


def test_parse_response_raises_message_parse_error_on_missing_field(
    agent: ConcreteAgent,
) -> None:
    """JSON missing a required field raises MessageParseError."""
    bad = dict(_VALID_MSG)
    del bad["content"]
    with pytest.raises(MessageParseError):
        agent.parse_response(json.dumps(bad))


# ---------------------------------------------------------------------------
# _validate_schema
# ---------------------------------------------------------------------------


def test_validate_schema_returns_true_on_valid_message_dict(
    agent: ConcreteAgent,
) -> None:
    """_validate_schema returns True for a fully conformant dict."""
    assert agent._validate_schema(_VALID_MSG) is True


def test_validate_schema_returns_false_on_missing_required_field(
    agent: ConcreteAgent,
) -> None:
    """_validate_schema returns False when a required field is absent."""
    bad = dict(_VALID_MSG)
    del bad["turn"]
    assert agent._validate_schema(bad) is False


def test_validate_schema_returns_false_on_wrong_sender_enum_value(
    agent: ConcreteAgent,
) -> None:
    """_validate_schema returns False when sender is not in the enum."""
    bad = dict(_VALID_MSG)
    bad["sender"] = "moderator"
    assert agent._validate_schema(bad) is False


# ---------------------------------------------------------------------------
# call_api
# ---------------------------------------------------------------------------


def test_call_api_dispatches_through_gatekeeper(
    agent: ConcreteAgent, mock_gatekeeper: MagicMock
) -> None:
    """call_api calls gatekeeper.dispatch exactly once."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="reply", prompt_tokens=5, completion_tokens=3
    )
    agent.call_api("hello")
    mock_gatekeeper.dispatch.assert_called_once()


def test_call_api_uses_model_from_init(
    agent: ConcreteAgent, mock_gatekeeper: MagicMock
) -> None:
    """The APIRequest passed to dispatch uses the model set at __init__."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="reply", prompt_tokens=5, completion_tokens=3
    )
    agent.call_api("hello")
    req = mock_gatekeeper.dispatch.call_args[0][0]
    assert req.model == "test-model"


def test_call_api_includes_agent_id_in_request(
    agent: ConcreteAgent, mock_gatekeeper: MagicMock
) -> None:
    """The APIRequest passed to dispatch carries the correct agent_id."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="reply", prompt_tokens=5, completion_tokens=3
    )
    agent.call_api("hello")
    req = mock_gatekeeper.dispatch.call_args[0][0]
    assert req.agent_id == "agent-1"


def test_call_api_returns_response_content(
    agent: ConcreteAgent, mock_gatekeeper: MagicMock
) -> None:
    """call_api returns the content string from the APIResponse."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="model reply", prompt_tokens=5, completion_tokens=3
    )
    result = agent.call_api("hello")
    assert result == "model reply"


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


def test_message_parse_error_is_exception() -> None:
    """MessageParseError is a subclass of Exception."""
    with pytest.raises(Exception):
        raise MessageParseError("parse failed")


def test_agent_failure_error_is_exception() -> None:
    """AgentFailureError is a subclass of Exception."""
    with pytest.raises(Exception):
        raise AgentFailureError("agent failed")

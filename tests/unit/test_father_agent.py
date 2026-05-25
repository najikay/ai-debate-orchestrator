"""Unit tests for FatherAgent.

TDD order:
    __init__ (role=father)
    → open_debate (returns DebateMessage / sender=father / recipient=pro_son / uuid)
    → _validate_message (valid / missing content / invalid sender / empty sources on turn%3)
    → route (pro_son / con_son / invalid)
    → _check_min_turns (False at 19 / True at 20 / True above 20)
    → _score_persuasiveness (dict keys / rubric dimensions / rubric template)
    → evaluate (NotEnoughTurns / draw=False / winner / reasoning≥50 / tiebreaker)
"""

import json
import types
from unittest.mock import MagicMock, patch

import pytest

from src.agents.father_agent import FatherAgent, NotEnoughTurnsError, Verdict
from src.agents.base_agent import DebateMessage
from src.infrastructure.gatekeeper import APIResponse, Gatekeeper

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE = {
    "message_id": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "pro_son",
    "recipient": "father",
    "turn": 1,
    "content": "AI benefits society.",
    "sources": ["https://example.com"],
    "token_count": 10,
    "timestamp": "2026-05-25T12:00:00+00:00",
}


def _make_msg(**overrides) -> DebateMessage:
    return DebateMessage(**{**_BASE, **overrides})


def _make_state(n: int) -> types.SimpleNamespace:
    """Return a simple state object with n transcript messages and turn_count=n."""
    msgs = [_make_msg(turn=i + 1, sender="pro_son" if i % 2 == 0 else "con_son")
            for i in range(n)]
    return types.SimpleNamespace(transcript=msgs, turn_count=n, topic="AI ethics")


_SCORE_JSON = json.dumps({
    "scores": {
        "pro_son": {"clarity": 8, "evidence": 9, "logic": 7, "total": 24},
        "con_son": {"clarity": 6, "evidence": 7, "logic": 8, "total": 21},
    },
    "winner": "pro_son",
    "draw": False,
    "reasoning": "Pro Son presented clearer arguments backed by more evidence.",
})

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_gatekeeper() -> MagicMock:
    gk = MagicMock(spec=Gatekeeper)
    gk.dispatch.return_value = APIResponse(
        content=_SCORE_JSON, prompt_tokens=20, completion_tokens=50
    )
    return gk


@pytest.fixture
def father_config() -> dict:
    return {"schema_version": "1.0"}


@pytest.fixture
def agent(mock_gatekeeper: MagicMock, father_config: dict) -> FatherAgent:
    return FatherAgent(
        gatekeeper=mock_gatekeeper,
        config=father_config,
        model="test-model",
    )


@pytest.fixture
def sample_state() -> types.SimpleNamespace:
    return _make_state(20)


@pytest.fixture
def short_state() -> types.SimpleNamespace:
    return _make_state(10)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_father_agent_init_sets_role_to_father(agent: FatherAgent) -> None:
    """role attribute is 'father'."""
    assert agent.role == "father"


def test_father_agent_init_sets_agent_id(agent: FatherAgent) -> None:
    """agent_id defaults to 'father'."""
    assert agent.agent_id == "father"


# ---------------------------------------------------------------------------
# open_debate
# ---------------------------------------------------------------------------


def test_open_debate_returns_debate_message(agent: FatherAgent) -> None:
    """open_debate returns a DebateMessage."""
    result = agent.open_debate("AI ethics")
    assert isinstance(result, DebateMessage)


def test_open_debate_sender_field_is_father(agent: FatherAgent) -> None:
    """The opening message has sender='father'."""
    result = agent.open_debate("AI ethics")
    assert result.sender == "father"


def test_open_debate_recipient_field_is_pro_son(agent: FatherAgent) -> None:
    """The opening message is addressed to pro_son first."""
    result = agent.open_debate("AI ethics")
    assert result.recipient == "pro_son"


def test_open_debate_message_id_is_valid_uuid(agent: FatherAgent) -> None:
    """message_id is a non-empty string (UUID format)."""
    import uuid as _uuid
    result = agent.open_debate("AI ethics")
    parsed = _uuid.UUID(result.message_id)
    assert str(parsed) == result.message_id


def test_open_debate_embeds_topic_in_content(agent: FatherAgent) -> None:
    """The topic appears in the content field."""
    result = agent.open_debate("climate change")
    assert "climate change" in result.content


# ---------------------------------------------------------------------------
# _validate_message
# ---------------------------------------------------------------------------


def test_validate_message_returns_true_on_complete_valid_message(
    agent: FatherAgent,
) -> None:
    """A fully valid DebateMessage passes validation."""
    assert agent._validate_message(_make_msg()) is True


def test_validate_message_returns_false_on_missing_content(
    agent: FatherAgent,
) -> None:
    """Empty content field fails validation."""
    msg = _make_msg(content="")
    assert agent._validate_message(msg) is False


def test_validate_message_returns_false_on_invalid_sender_value(
    agent: FatherAgent,
) -> None:
    """Sender not in the allowed enum fails validation."""
    msg = _make_msg(sender="moderator")
    assert agent._validate_message(msg) is False


def test_validate_message_returns_false_on_empty_sources_on_turn_divisible_by_3(
    agent: FatherAgent,
) -> None:
    """Empty sources on a turn divisible by 3 fails validation."""
    msg = _make_msg(turn=3, sources=[])
    assert agent._validate_message(msg) is False


def test_validate_message_allows_empty_sources_on_non_divisible_turn(
    agent: FatherAgent,
) -> None:
    """Empty sources are allowed on turns not divisible by 3."""
    msg = _make_msg(turn=1, sources=[])
    assert agent._validate_message(msg) is True


# ---------------------------------------------------------------------------
# route
# ---------------------------------------------------------------------------


def test_route_returns_pro_son_identifier(agent: FatherAgent) -> None:
    """Messages addressed to pro_son return 'pro_son'."""
    msg = _make_msg(recipient="pro_son")
    assert agent.route(msg) == "pro_son"


def test_route_returns_con_son_identifier(agent: FatherAgent) -> None:
    """Messages addressed to con_son return 'con_son'."""
    msg = _make_msg(recipient="con_son")
    assert agent.route(msg) == "con_son"


def test_route_raises_value_error_on_invalid_recipient(
    agent: FatherAgent,
) -> None:
    """Recipient not in the allowed set raises ValueError."""
    msg = _make_msg(recipient="unknown_agent")
    with pytest.raises(ValueError):
        agent.route(msg)


# ---------------------------------------------------------------------------
# _check_min_turns
# ---------------------------------------------------------------------------


def test_check_min_turns_returns_false_when_turn_count_is_19(
    agent: FatherAgent,
) -> None:
    """Returns False when transcript has fewer than 20 messages."""
    assert agent._check_min_turns(_make_state(19)) is False


def test_check_min_turns_returns_true_when_turn_count_is_20(
    agent: FatherAgent,
) -> None:
    """Returns True at exactly 20 turns."""
    assert agent._check_min_turns(_make_state(20)) is True


def test_check_min_turns_returns_true_when_turn_count_exceeds_20(
    agent: FatherAgent,
) -> None:
    """Returns True when turn count exceeds 20."""
    assert agent._check_min_turns(_make_state(25)) is True


# ---------------------------------------------------------------------------
# _score_persuasiveness
# ---------------------------------------------------------------------------


def test_score_persuasiveness_returns_dict_with_pro_and_con_keys(
    agent: FatherAgent, sample_state: types.SimpleNamespace
) -> None:
    """Returned dict has 'pro_son' and 'con_son' top-level keys."""
    scores = agent._score_persuasiveness(sample_state.transcript)
    assert "pro_son" in scores and "con_son" in scores


def test_score_persuasiveness_each_entry_has_rubric_dimensions(
    agent: FatherAgent, sample_state: types.SimpleNamespace
) -> None:
    """Each agent entry has clarity, evidence, logic, and total fields."""
    scores = agent._score_persuasiveness(sample_state.transcript)
    for key in ("pro_son", "con_son"):
        for dim in ("clarity", "evidence", "logic", "total"):
            assert dim in scores[key], f"Missing '{dim}' in scores['{key}']"


def test_score_persuasiveness_uses_rubric_prompt_template(
    agent: FatherAgent, sample_state: types.SimpleNamespace, mock_gatekeeper: MagicMock
) -> None:
    """The rubric prompt template (from PRD §9.3) appears in the API call payload."""
    agent._score_persuasiveness(sample_state.transcript)
    call_payload = mock_gatekeeper.dispatch.call_args[0][0].payload
    prompt_text = call_payload.get("prompt", "")
    assert "Clarity (1-10)" in prompt_text
    assert "Evidence Quality (1-10)" in prompt_text
    assert "Logical Consistency (1-10)" in prompt_text


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------


def test_evaluate_raises_not_enough_turns_error_when_below_20(
    agent: FatherAgent, short_state: types.SimpleNamespace
) -> None:
    """NotEnoughTurnsError raised when fewer than 20 turns have elapsed."""
    with pytest.raises(NotEnoughTurnsError):
        agent.evaluate(short_state)


def test_evaluate_returns_verdict_with_draw_false(
    agent: FatherAgent, sample_state: types.SimpleNamespace
) -> None:
    """Verdict.draw is always False."""
    verdict = agent.evaluate(sample_state)
    assert verdict.draw is False


def test_evaluate_winner_is_pro_son_or_con_son(
    agent: FatherAgent, sample_state: types.SimpleNamespace
) -> None:
    """Verdict.winner is exactly 'pro_son' or 'con_son'."""
    verdict = agent.evaluate(sample_state)
    assert verdict.winner in ("pro_son", "con_son")


def test_evaluate_reasoning_field_is_at_least_50_characters(
    agent: FatherAgent, sample_state: types.SimpleNamespace
) -> None:
    """Verdict.reasoning contains at least 50 characters."""
    verdict = agent.evaluate(sample_state)
    assert len(verdict.reasoning) >= 50


def test_evaluate_applies_tiebreaker_when_scores_are_equal(
    agent: FatherAgent, sample_state: types.SimpleNamespace, mock_gatekeeper: MagicMock
) -> None:
    """When totals are equal the tiebreaker resolves to one of the two agents."""
    tie_json = json.dumps({
        "scores": {
            "pro_son": {"clarity": 8, "evidence": 8, "logic": 8, "total": 24},
            "con_son": {"clarity": 8, "evidence": 8, "logic": 8, "total": 24},
        },
        "winner": "pro_son",
        "draw": False,
        "reasoning": "Tied scores resolved by momentum in the final turns of debate.",
    })
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content=tie_json, prompt_tokens=20, completion_tokens=50
    )
    verdict = agent.evaluate(sample_state)
    assert verdict.winner in ("pro_son", "con_son")
    assert verdict.draw is False

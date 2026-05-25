"""Unit tests for StateManager.

TDD order:
    __init__ (status / turn_count / transcript)
    → record_message (appends / increments / refreshes updated_at)
    → record_verdict (stores / duplicate guard)
    → get_turn_count (zero / after n messages)
    → to_json (string / parseable / fields present)
    → from_json (topic / turn_count / transcript / malformed)
"""

import json
import time

import pytest

from src.agents.base_agent import DebateMessage
from src.agents.father_agent import Verdict
from src.engine.state_manager import StateManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sm() -> StateManager:
    return StateManager()


@pytest.fixture
def sample_message() -> DebateMessage:
    return DebateMessage(
        message_id="123e4567-e89b-12d3-a456-426614174000",
        sender="pro_son",
        recipient="father",
        turn=1,
        content="AI is beneficial.",
        sources=["https://example.com"],
        token_count=10,
        timestamp="2026-05-25T12:00:00+00:00",
    )


@pytest.fixture
def sample_verdict() -> Verdict:
    return Verdict(
        verdict_id="00000000-0000-0000-0000-000000000001",
        winner="pro_son",
        draw=False,
        reasoning="Pro Son demonstrated superior clarity and evidence quality.",
        turn_count=20,
        timestamp="2026-05-25T13:00:00+00:00",
    )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_state_manager_init_status_is_initialization(sm: StateManager) -> None:
    """Initial status is 'INITIALIZATION'."""
    assert sm.state.status == "INITIALIZATION"


def test_state_manager_init_turn_count_is_zero(sm: StateManager) -> None:
    """Initial turn_count is 0."""
    assert sm.state.turn_count == 0


def test_state_manager_init_transcript_is_empty_list(sm: StateManager) -> None:
    """Initial transcript is an empty list."""
    assert sm.state.transcript == []


def test_state_manager_init_verdict_is_none(sm: StateManager) -> None:
    """Initial verdict is None."""
    assert sm.state.verdict is None


# ---------------------------------------------------------------------------
# record_message
# ---------------------------------------------------------------------------


def test_record_message_appends_to_transcript(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """record_message adds the message to the transcript."""
    sm.record_message(sample_message)
    assert len(sm.state.transcript) == 1
    assert sm.state.transcript[0] is sample_message


def test_record_message_increments_turn_count_by_one(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """Each call to record_message increments turn_count by 1."""
    sm.record_message(sample_message)
    sm.record_message(sample_message)
    assert sm.state.turn_count == 2


def test_record_message_refreshes_updated_at_timestamp(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """updated_at changes after a record_message call."""
    before = sm.state.updated_at
    time.sleep(0.01)
    sm.record_message(sample_message)
    assert sm.state.updated_at != before


# ---------------------------------------------------------------------------
# record_verdict
# ---------------------------------------------------------------------------


def test_record_verdict_stores_verdict_object(
    sm: StateManager, sample_verdict: Verdict
) -> None:
    """record_verdict stores the Verdict and sets status to TERMINATED."""
    sm.record_verdict(sample_verdict)
    assert sm.state.verdict is sample_verdict
    assert sm.state.status == "TERMINATED"


def test_record_verdict_raises_if_verdict_already_exists(
    sm: StateManager, sample_verdict: Verdict
) -> None:
    """A second call to record_verdict raises ValueError."""
    sm.record_verdict(sample_verdict)
    with pytest.raises(ValueError):
        sm.record_verdict(sample_verdict)


# ---------------------------------------------------------------------------
# get_turn_count
# ---------------------------------------------------------------------------


def test_get_turn_count_returns_zero_on_fresh_state(sm: StateManager) -> None:
    """get_turn_count returns 0 before any messages are recorded."""
    assert sm.get_turn_count() == 0


def test_get_turn_count_returns_correct_value_after_n_messages(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """get_turn_count returns the number of recorded messages."""
    for _ in range(5):
        sm.record_message(sample_message)
    assert sm.get_turn_count() == 5


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------


def test_to_json_output_is_a_string(sm: StateManager) -> None:
    """to_json returns a str."""
    assert isinstance(sm.to_json(), str)


def test_to_json_output_is_parseable_json(sm: StateManager) -> None:
    """to_json output can be parsed by json.loads."""
    data = json.loads(sm.to_json())
    assert isinstance(data, dict)


def test_to_json_includes_topic_and_turn_count_and_transcript(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """to_json serialized output contains topic, turn_count, and transcript keys."""
    sm.state.topic = "AI ethics"
    sm.record_message(sample_message)
    data = json.loads(sm.to_json())
    assert "topic" in data
    assert "turn_count" in data
    assert "transcript" in data
    assert data["turn_count"] == 1


# ---------------------------------------------------------------------------
# from_json
# ---------------------------------------------------------------------------


def test_from_json_restores_topic_field(sm: StateManager) -> None:
    """from_json restores the topic field from a serialized state."""
    sm.state.topic = "AI debate"
    restored = sm.from_json(sm.to_json())
    assert restored.topic == "AI debate"


def test_from_json_restores_turn_count(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """from_json restores the turn_count correctly."""
    sm.record_message(sample_message)
    sm.record_message(sample_message)
    restored = sm.from_json(sm.to_json())
    assert restored.turn_count == 2


def test_from_json_restores_full_transcript_array(
    sm: StateManager, sample_message: DebateMessage
) -> None:
    """from_json restores the transcript list length."""
    sm.record_message(sample_message)
    sm.record_message(sample_message)
    restored = sm.from_json(sm.to_json())
    assert len(restored.transcript) == 2


def test_from_json_raises_value_error_on_malformed_json(sm: StateManager) -> None:
    """from_json raises ValueError on invalid JSON input."""
    with pytest.raises(ValueError):
        sm.from_json("not valid json {{{{")

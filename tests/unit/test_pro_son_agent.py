"""Unit tests for ProSonAgent.

TDD order:
    __init__ (position / skills)
    → build_prompt (non-empty / pro instruction / topic embedded)
    → _enforce_position (unchanged for pro / raises on con stance)
    → generate_argument (happy / sources non-empty / retries / failure)
"""

from unittest.mock import MagicMock

import pytest

from src.agents.base_agent import AgentFailureError, DebateMessage
from src.agents.pro_son_agent import ProSonAgent
from src.infrastructure.gatekeeper import APIResponse, Gatekeeper
from src.skills.base_skill import AgentSkill, SkillResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_MSG = {
    "message_id": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "father",
    "recipient": "pro_son",
    "turn": 1,
    "content": "Debate topic: AI ethics.",
    "sources": [],
    "token_count": 10,
    "timestamp": "2026-05-25T12:00:00+00:00",
}


@pytest.fixture
def mock_gatekeeper() -> MagicMock:
    gk = MagicMock(spec=Gatekeeper)
    gk.dispatch.return_value = APIResponse(
        content="AI benefits society greatly.", prompt_tokens=5, completion_tokens=10
    )
    return gk


@pytest.fixture
def mock_skill() -> MagicMock:
    skill = MagicMock(spec=AgentSkill)
    skill.execute.return_value = SkillResult(
        query="AI ethics",
        snippets=["AI reduces poverty."],
        raw_response={},
    )
    return skill


@pytest.fixture
def pro_config() -> dict:
    return {"schema_version": "1.0"}


@pytest.fixture
def agent(
    mock_gatekeeper: MagicMock, mock_skill: MagicMock, pro_config: dict
) -> ProSonAgent:
    return ProSonAgent(
        gatekeeper=mock_gatekeeper,
        config=pro_config,
        skills=[mock_skill],
        model="test-model",
    )


@pytest.fixture
def father_msg() -> DebateMessage:
    return DebateMessage(**_VALID_MSG)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_pro_son_init_sets_position_attribute_to_pro(agent: ProSonAgent) -> None:
    """position attribute is 'pro'."""
    assert agent.position == "pro"


def test_pro_son_init_stores_skills_list(
    agent: ProSonAgent, mock_skill: MagicMock
) -> None:
    """skills list is stored on the instance."""
    assert mock_skill in agent.skills


def test_pro_son_init_sets_agent_id(agent: ProSonAgent) -> None:
    """agent_id defaults to 'pro_son'."""
    assert agent.agent_id == "pro_son"


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


def test_build_prompt_returns_non_empty_string(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """build_prompt returns a non-empty string."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    assert isinstance(result, str) and result.strip()


def test_build_prompt_contains_pro_position_instruction(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """Prompt explicitly instructs the agent to argue FOR the topic."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    lower = result.lower()
    assert "pro" in lower or "support" in lower or "for" in lower


def test_build_prompt_embeds_topic_from_debate_state(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """The topic string appears somewhere in the generated prompt."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    assert "AI ethics" in result


# ---------------------------------------------------------------------------
# _enforce_position
# ---------------------------------------------------------------------------


def test_enforce_position_returns_content_unchanged_for_pro_argument(
    agent: ProSonAgent,
) -> None:
    """Content supporting the pro position passes through unchanged."""
    content = "AI greatly benefits society and improves lives."
    assert agent._enforce_position(content) == content


def test_enforce_position_raises_on_con_stance_detected(
    agent: ProSonAgent,
) -> None:
    """Content expressing opposition raises an internal position signal."""
    with pytest.raises(Exception):
        agent._enforce_position("I strongly oppose this position and disagree with it.")


# ---------------------------------------------------------------------------
# generate_argument
# ---------------------------------------------------------------------------


def test_generate_argument_returns_valid_debate_message(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """generate_argument returns a DebateMessage on the happy path."""
    result = agent.generate_argument(father_msg)
    assert isinstance(result, DebateMessage)


def test_generate_argument_sender_is_pro_son(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """The returned DebateMessage has sender='pro_son'."""
    result = agent.generate_argument(father_msg)
    assert result.sender == "pro_son"


def test_generate_argument_sources_field_is_non_empty(
    agent: ProSonAgent, father_msg: DebateMessage
) -> None:
    """sources list is populated from the skill's snippets."""
    result = agent.generate_argument(father_msg)
    assert len(result.sources) >= 1


def test_generate_argument_retries_up_to_2_times_on_position_violation(
    agent: ProSonAgent, father_msg: DebateMessage, mock_gatekeeper: MagicMock
) -> None:
    """dispatch is called again (up to 2 retries) when position is violated."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="I strongly oppose this — I disagree entirely.",
        prompt_tokens=5,
        completion_tokens=10,
    )
    with pytest.raises(AgentFailureError):
        agent.generate_argument(father_msg)
    # 3 total attempts (1 initial + 2 retries)
    assert mock_gatekeeper.dispatch.call_count == 3


def test_generate_argument_raises_agent_failure_error_after_2_retries(
    agent: ProSonAgent, father_msg: DebateMessage, mock_gatekeeper: MagicMock
) -> None:
    """AgentFailureError raised when all 3 attempts violate the position."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="I oppose and disagree with this.",
        prompt_tokens=5,
        completion_tokens=10,
    )
    with pytest.raises(AgentFailureError):
        agent.generate_argument(father_msg)

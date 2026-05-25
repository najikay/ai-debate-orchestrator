"""Unit tests for ConSonAgent.

TDD order:
    __init__ (position / skills)
    → build_prompt (non-empty / con instruction / topic embedded)
    → _enforce_position (unchanged for con / raises on pro stance)
    → generate_argument (happy / sources non-empty / retries / failure)
"""

from unittest.mock import MagicMock

import pytest

from src.agents.base_agent import AgentFailureError, DebateMessage
from src.agents.con_son_agent import ConSonAgent
from src.infrastructure.gatekeeper import APIResponse, Gatekeeper
from src.skills.base_skill import AgentSkill, SkillResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_MSG = {
    "message_id": "123e4567-e89b-12d3-a456-426614174001",
    "sender": "father",
    "recipient": "con_son",
    "turn": 2,
    "content": "Debate topic: AI ethics.",
    "sources": [],
    "token_count": 10,
    "timestamp": "2026-05-25T12:00:00+00:00",
}


@pytest.fixture
def mock_gatekeeper() -> MagicMock:
    gk = MagicMock(spec=Gatekeeper)
    gk.dispatch.return_value = APIResponse(
        content="AI poses serious risks to society.",
        prompt_tokens=5,
        completion_tokens=10,
    )
    return gk


@pytest.fixture
def mock_skill() -> MagicMock:
    skill = MagicMock(spec=AgentSkill)
    skill.execute.return_value = SkillResult(
        query="AI ethics",
        snippets=["AI raises ethical concerns."],
        raw_response={},
    )
    return skill


@pytest.fixture
def con_config() -> dict:
    return {"schema_version": "1.0"}


@pytest.fixture
def agent(
    mock_gatekeeper: MagicMock, mock_skill: MagicMock, con_config: dict
) -> ConSonAgent:
    return ConSonAgent(
        gatekeeper=mock_gatekeeper,
        config=con_config,
        skills=[mock_skill],
        model="test-model",
    )


@pytest.fixture
def father_msg() -> DebateMessage:
    return DebateMessage(**_VALID_MSG)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_con_son_init_sets_position_attribute_to_con(agent: ConSonAgent) -> None:
    """position attribute is 'con'."""
    assert agent.position == "con"


def test_con_son_init_stores_skills_list(
    agent: ConSonAgent, mock_skill: MagicMock
) -> None:
    """skills list is stored on the instance."""
    assert mock_skill in agent.skills


def test_con_son_init_sets_agent_id(agent: ConSonAgent) -> None:
    """agent_id defaults to 'con_son'."""
    assert agent.agent_id == "con_son"


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


def test_build_prompt_returns_non_empty_string(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """build_prompt returns a non-empty string."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    assert isinstance(result, str) and result.strip()


def test_build_prompt_contains_con_position_instruction(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """Prompt explicitly instructs the agent to argue AGAINST the topic."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    lower = result.lower()
    assert "con" in lower or "against" in lower or "oppose" in lower


def test_build_prompt_embeds_topic_from_debate_state(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """The topic string appears in the generated prompt."""
    result = agent.build_prompt({"message": father_msg, "topic": "AI ethics"})
    assert "AI ethics" in result


# ---------------------------------------------------------------------------
# _enforce_position
# ---------------------------------------------------------------------------


def test_enforce_position_returns_content_unchanged_for_con_argument(
    agent: ConSonAgent,
) -> None:
    """Content opposing the topic passes through unchanged."""
    content = "AI poses grave risks and we must resist its unchecked growth."
    assert agent._enforce_position(content) == content


def test_enforce_position_raises_on_pro_stance_detected(
    agent: ConSonAgent,
) -> None:
    """Content expressing support raises an internal position signal."""
    with pytest.raises(Exception):
        agent._enforce_position("AI is wonderful and greatly benefits humanity.")


# ---------------------------------------------------------------------------
# generate_argument
# ---------------------------------------------------------------------------


def test_generate_argument_returns_valid_debate_message(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """generate_argument returns a DebateMessage on the happy path."""
    result = agent.generate_argument(father_msg)
    assert isinstance(result, DebateMessage)


def test_generate_argument_sender_is_con_son(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """The returned DebateMessage has sender='con_son'."""
    result = agent.generate_argument(father_msg)
    assert result.sender == "con_son"


def test_generate_argument_sources_field_is_non_empty(
    agent: ConSonAgent, father_msg: DebateMessage
) -> None:
    """sources list is populated from the skill's snippets."""
    result = agent.generate_argument(father_msg)
    assert len(result.sources) >= 1


def test_generate_argument_retries_up_to_2_times_on_position_violation(
    agent: ConSonAgent, father_msg: DebateMessage, mock_gatekeeper: MagicMock
) -> None:
    """dispatch is called 3 times (1 + 2 retries) when position is always violated."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="AI is wonderful and greatly benefits humanity.",
        prompt_tokens=5,
        completion_tokens=10,
    )
    with pytest.raises(AgentFailureError):
        agent.generate_argument(father_msg)
    assert mock_gatekeeper.dispatch.call_count == 3


def test_generate_argument_raises_agent_failure_error_after_2_retries(
    agent: ConSonAgent, father_msg: DebateMessage, mock_gatekeeper: MagicMock
) -> None:
    """AgentFailureError raised when all 3 attempts violate the position."""
    mock_gatekeeper.dispatch.return_value = APIResponse(
        content="I strongly support and advocate for this wonderful topic.",
        prompt_tokens=5,
        completion_tokens=10,
    )
    with pytest.raises(AgentFailureError):
        agent.generate_argument(father_msg)

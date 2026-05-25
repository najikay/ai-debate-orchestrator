"""Unit tests for AgentSkill ABC, SkillResult, and SkillError.

TDD order:
    SkillError (is Exception subclass)
    → SkillResult (dataclass fields)
    → AgentSkill (cannot instantiate / partial subclass still abstract / full subclass ok)
"""

import pytest

from src.skills.base_skill import AgentSkill, SkillError, SkillResult

# ---------------------------------------------------------------------------
# SkillError
# ---------------------------------------------------------------------------


def test_skill_error_is_subclass_of_exception() -> None:
    """SkillError can be raised and caught as Exception."""
    with pytest.raises(Exception):
        raise SkillError("test error")


# ---------------------------------------------------------------------------
# SkillResult
# ---------------------------------------------------------------------------


def test_skill_result_dataclass_has_query_snippets_raw_response_fields() -> None:
    """SkillResult stores query, snippets, and raw_response."""
    result = SkillResult(
        query="test query",
        snippets=["snippet 1", "snippet 2"],
        raw_response={"key": "value"},
    )
    assert result.query == "test query"
    assert result.snippets == ["snippet 1", "snippet 2"]
    assert result.raw_response == {"key": "value"}


# ---------------------------------------------------------------------------
# AgentSkill ABC
# ---------------------------------------------------------------------------


def test_agent_skill_cannot_be_instantiated_directly() -> None:
    """Direct instantiation of AgentSkill raises TypeError."""
    with pytest.raises(TypeError):
        AgentSkill()  # type: ignore[abstract]


def test_concrete_subclass_missing_execute_is_still_abstract() -> None:
    """A subclass that omits execute() cannot be instantiated."""

    class IncompleteSkill(AgentSkill):
        skill_name = "incomplete"
        # execute not implemented

    with pytest.raises(TypeError):
        IncompleteSkill()  # type: ignore[abstract]


def test_concrete_subclass_with_execute_is_instantiable() -> None:
    """A subclass that implements execute() can be instantiated and called."""

    class ConcreteSkill(AgentSkill):
        skill_name = "concrete"

        def execute(self, query: str) -> SkillResult:
            return SkillResult(query=query, snippets=["result"], raw_response={})

    skill = ConcreteSkill()
    result = skill.execute("hello")
    assert isinstance(result, SkillResult)
    assert result.query == "hello"

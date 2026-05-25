"""Unit tests for LogicAnalyzerTool.

TDD order:
    skill_name attribute
    → execute (returns SkillResult / non-empty snippets / keyword detection /
      word count)
    → empty query (no exception)
    → no network calls
"""

from unittest.mock import patch

import pytest

from src.skills.base_skill import SkillResult
from src.skills.logic_analyzer_tool import LogicAnalyzerTool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tool() -> LogicAnalyzerTool:
    return LogicAnalyzerTool()


PREMISE_QUERY = "Because the sky is blue and since birds fly, we can study them."
CONCLUSION_QUERY = "All men are mortal. Therefore Socrates is mortal."
MIXED_QUERY = (
    "Given that inflation is rising, interest rates must follow. "
    "Thus, housing prices will stabilise."
)

# ---------------------------------------------------------------------------
# skill_name
# ---------------------------------------------------------------------------


def test_logic_analyzer_skill_name_is_logic_analyzer(tool: LogicAnalyzerTool) -> None:
    """skill_name attribute equals 'logic_analyzer'."""
    assert tool.skill_name == "logic_analyzer"


# ---------------------------------------------------------------------------
# execute — structure
# ---------------------------------------------------------------------------


def test_execute_returns_skill_result(tool: LogicAnalyzerTool) -> None:
    """execute returns a SkillResult instance."""
    result = tool.execute("Any argument text here.")
    assert isinstance(result, SkillResult)


def test_execute_preserves_query_in_result(tool: LogicAnalyzerTool) -> None:
    """The returned SkillResult carries the original query string."""
    q = "Some argument."
    result = tool.execute(q)
    assert result.query == q


def test_execute_snippets_are_non_empty(tool: LogicAnalyzerTool) -> None:
    """snippets list contains at least one entry for any non-empty query."""
    result = tool.execute("All cats are mammals.")
    assert len(result.snippets) >= 1


# ---------------------------------------------------------------------------
# execute — premise keywords
# ---------------------------------------------------------------------------


def test_execute_detects_premise_keywords(tool: LogicAnalyzerTool) -> None:
    """Premise keyword count is positive for a query containing 'because'/'since'."""
    result = tool.execute(PREMISE_QUERY)
    rubric = result.raw_response
    assert rubric["premise_keywords"] >= 1


# ---------------------------------------------------------------------------
# execute — conclusion keywords
# ---------------------------------------------------------------------------


def test_execute_detects_conclusion_keywords(tool: LogicAnalyzerTool) -> None:
    """Conclusion keyword count is positive for a query containing 'therefore'."""
    result = tool.execute(CONCLUSION_QUERY)
    rubric = result.raw_response
    assert rubric["conclusion_keywords"] >= 1


# ---------------------------------------------------------------------------
# execute — word / sentence counts
# ---------------------------------------------------------------------------


def test_execute_counts_words(tool: LogicAnalyzerTool) -> None:
    """word_count equals the number of whitespace-split tokens."""
    text = "One two three four five"
    result = tool.execute(text)
    assert result.raw_response["word_count"] == 5


def test_execute_counts_sentences(tool: LogicAnalyzerTool) -> None:
    """sentence_count reflects the number of sentence-ending punctuation marks."""
    text = "First sentence. Second sentence! Third sentence?"
    result = tool.execute(text)
    assert result.raw_response["sentence_count"] == 3


# ---------------------------------------------------------------------------
# execute — edge cases
# ---------------------------------------------------------------------------


def test_execute_empty_query_returns_result_without_raising(
    tool: LogicAnalyzerTool,
) -> None:
    """An empty query string returns a SkillResult rather than raising."""
    result = tool.execute("")
    assert isinstance(result, SkillResult)


# ---------------------------------------------------------------------------
# No network calls
# ---------------------------------------------------------------------------


def test_execute_makes_no_network_calls(tool: LogicAnalyzerTool) -> None:
    """execute never triggers DNS resolution — purely local computation."""
    with patch("socket.getaddrinfo", side_effect=AssertionError("network call")) as spy:
        tool.execute(MIXED_QUERY)
    spy.assert_not_called()

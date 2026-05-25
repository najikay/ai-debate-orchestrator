"""Integration tests: full debate session end-to-end.

Fixtures and helpers live in conftest.py.  All tests share one
module-scoped ``debate_result`` to minimise LLM stub invocations.
"""

import pytest

from src.agents.father_agent import Verdict

pytestmark = pytest.mark.slow


def test_full_debate_completes_without_raising_exception(debate_result) -> None:
    assert debate_result is not None


def test_full_debate_returns_verdict_object(debate_result) -> None:
    verdict, _, _ = debate_result
    assert isinstance(verdict, Verdict)


def test_full_debate_transcript_has_at_least_20_messages(debate_result) -> None:
    _, transcript, _ = debate_result
    assert len(transcript) >= 20


def test_full_debate_all_messages_validate_against_debate_message_schema(
    debate_result, debate_schema
) -> None:
    """Every DebateMessage in the transcript validates against the JSON schema."""
    import jsonschema

    _, transcript, _ = debate_result
    for msg in transcript:
        data = {k: getattr(msg, k) for k in msg.__dataclass_fields__}
        jsonschema.validate(instance=data, schema=debate_schema)


def test_full_debate_verdict_draw_field_is_false(debate_result) -> None:
    verdict, _, _ = debate_result
    assert verdict.draw is False


def test_full_debate_verdict_winner_is_pro_son_or_con_son(debate_result) -> None:
    verdict, _, _ = debate_result
    assert verdict.winner in ("pro_son", "con_son")


def test_full_debate_web_search_invoked_at_least_once_per_3_turns_per_side(
    debate_result,
) -> None:
    """Every 3-turn window per side must contain ≥1 message with non-empty sources."""
    _, transcript, _ = debate_result
    for sender in ("pro_son", "con_son"):
        side = [m for m in transcript if m.sender == sender]
        for i in range(0, len(side), 3):
            chunk = side[i : i + 3]
            assert any(m.sources for m in chunk), (
                f"No sources in turns {i + 1}–{i + len(chunk)} for {sender}"
            )


def test_full_debate_cost_report_generated_at_session_end(debate_result) -> None:
    _, _, engine = debate_result
    summary = engine.cost_reporter.compute()
    assert summary.total_usd >= 0


def test_no_message_sent_directly_from_pro_son_to_con_son(debate_result) -> None:
    _, transcript, _ = debate_result
    direct = [
        m for m in transcript
        if m.sender == "pro_son" and m.recipient == "con_son"
    ]
    assert direct == []


def test_no_message_sent_directly_from_con_son_to_pro_son(debate_result) -> None:
    _, transcript, _ = debate_result
    direct = [
        m for m in transcript
        if m.sender == "con_son" and m.recipient == "pro_son"
    ]
    assert direct == []

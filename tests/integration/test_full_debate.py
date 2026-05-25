"""Integration tests: full debate session end-to-end.

All 10 tests share one module-scoped debate result to minimise overhead.
The Anthropic API (external) is stubbed at Gatekeeper._make_api_call so
the suite runs in CI without ANTHROPIC_API_KEY.  Every other component
(DebateEngine, StateManager, CostReporter, Watchdog, all agents) is real.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.father_agent import Verdict
from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.gatekeeper import APIRequest, APIResponse, Gatekeeper
from src.skills.base_skill import AgentSkill, SkillResult

pytestmark = pytest.mark.slow

_TOPIC = "AI will replace human workers"
_ROOT = Path(__file__).parent.parent.parent
_SCHEMA = json.loads(
    (_ROOT / "src" / "schemas" / "debate_message.json").read_text()
)

_RUBRIC_RESPONSE = json.dumps(
    {
        "scores": {
            "pro_son": {"clarity": 8, "evidence": 7, "logic": 8, "total": 23},
            "con_son": {"clarity": 7, "evidence": 7, "logic": 7, "total": 21},
        },
        "winner": "pro_son",
        "draw": False,
        "reasoning": "Pro Son demonstrated superior clarity and evidence quality.",
    }
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_make_api_call(self: Gatekeeper, request: APIRequest) -> APIResponse:
    """Deterministic stub: routes by agent_id, never calls the network."""
    if request.agent_id == "father":
        content = _RUBRIC_RESPONSE
    elif request.agent_id == "pro_son":
        content = (
            "This technology greatly benefits humanity by improving productivity"
            " and fostering innovation across every sector of the economy."
        )
    else:
        content = (
            "This technology has significant drawbacks including job displacement"
            " and widening inequality that society must carefully address."
        )
    return APIResponse(content=content, prompt_tokens=10, completion_tokens=30)


class _StubSkill(AgentSkill):
    skill_name = "stub_search"

    def execute(self, query: str) -> SkillResult:
        return SkillResult(
            query=query,
            snippets=["Stub evidence A.", "Stub evidence B."],
            raw_response={},
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def debate_result():
    """Run one debate with stubbed LLM; expose (verdict, transcript, engine)."""
    config = ConfigLoader(str(_ROOT / "config")).load_setup()
    stub = _StubSkill()
    with patch.object(Gatekeeper, "_make_api_call", _fake_make_api_call):
        engine = DebateEngine(config)
        engine.pro_son.skills = [stub]
        engine.con_son.skills = [stub]
        verdict = engine.start(_TOPIC)
    transcript = engine.state_manager.state.transcript
    return verdict, transcript, engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_full_debate_completes_without_raising_exception(debate_result) -> None:
    assert debate_result is not None


def test_full_debate_returns_verdict_object(debate_result) -> None:
    verdict, _, _ = debate_result
    assert isinstance(verdict, Verdict)


def test_full_debate_transcript_has_at_least_20_messages(debate_result) -> None:
    _, transcript, _ = debate_result
    assert len(transcript) >= 20


def test_full_debate_all_messages_validate_against_debate_message_schema(
    debate_result,
) -> None:
    import jsonschema

    _, transcript, _ = debate_result
    for msg in transcript:
        data = {k: getattr(msg, k) for k in msg.__dataclass_fields__}
        jsonschema.validate(instance=data, schema=_SCHEMA)


def test_full_debate_verdict_draw_field_is_false(debate_result) -> None:
    verdict, _, _ = debate_result
    assert verdict.draw is False


def test_full_debate_verdict_winner_is_pro_son_or_con_son(debate_result) -> None:
    verdict, _, _ = debate_result
    assert verdict.winner in ("pro_son", "con_son")


def test_full_debate_web_search_invoked_at_least_once_per_3_turns_per_side(
    debate_result,
) -> None:
    """Every 3-turn window per side must have ≥1 message with non-empty sources."""
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

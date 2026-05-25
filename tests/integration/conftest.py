"""
Configuration and shared fixtures for integration tests.

All tests in this package are automatically marked as `slow` — they run
the full DebateEngine with the Anthropic API stubbed at _make_api_call so
no live API key is required.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.gatekeeper import APIRequest, APIResponse, Gatekeeper
from src.skills.base_skill import AgentSkill, SkillResult

pytestmark = pytest.mark.slow

_TOPIC = "AI will replace human workers"
_ROOT = Path(__file__).parent.parent.parent

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


@pytest.fixture(scope="module")
def debate_schema() -> dict:
    """Parsed debate_message JSON schema."""
    return json.loads(
        (_ROOT / "src" / "schemas" / "debate_message.json").read_text()
    )


@pytest.fixture(scope="module")
def debate_result():
    """Run one full debate with stubbed LLM; return (verdict, transcript, engine)."""
    config = ConfigLoader(str(_ROOT / "config")).load_setup()
    stub = _StubSkill()
    with patch.object(Gatekeeper, "_make_api_call", _fake_make_api_call):
        engine = DebateEngine(config)
        engine.pro_son.skills = [stub]
        engine.con_son.skills = [stub]
        verdict = engine.start(_TOPIC)
    transcript = engine.state_manager.state.transcript
    return verdict, transcript, engine

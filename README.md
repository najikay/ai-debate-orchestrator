# AI Debate System

**Group:** NajAmjad | **Course:** AI Orchestration | **Version:** 1.0.0

A multi-agent AI orchestration system in which three Claude agents —
Father (judge), Pro Son (affirmative), and Con Son (negative) — conduct
a structured, scored debate on any topic supplied by the user.

---

## Overview

The system runs a full debate loop: the Father moderates and routes all
messages; Pro Son argues for the topic; Con Son argues against it.
After a minimum of 10 turns per side the Father evaluates persuasiveness
using a three-dimension rubric (Clarity, Evidence Quality, Logical
Consistency) and declares a winner. All inter-agent messages are
validated against a JSON schema. Costs are tracked in real time and a
budget cap prevents runaway spending.

---

## Architecture

See `docs/PLAN.md` for the full C4 context diagram, class hierarchy, and
layered architecture overview.

**Layers (bottom → top):**

| Layer | Key classes |
|---|---|
| Infrastructure | `Gatekeeper`, `Watchdog`, `CostReporter`, `ConfigLoader`, `LoggerManager` |
| Skills | `WebSearchTool`, `LogicAnalyzerTool` |
| Agents | `BaseAgent`, `ProSonAgent`, `ConSonAgent`, `FatherAgent` |
| Engine | `StateManager`, `DebateEngine` |
| UI | `DebateCLI` |

---

## Prerequisites

- Python 3.11+
- `uv` package manager (≥ 0.4.0)
- Anthropic API key (`ANTHROPIC_API_KEY`)
- Optional: Search API key (`SEARCH_API_KEY`) for live web search

---

## Installation

```bash
git clone <repo-url>
cd A2
cp .env-example .env          # fill in real API keys
uv sync --extra dev           # installs all dependencies + dev tools
```

---

## Configuration

| File | Purpose |
|---|---|
| `config/setup.json` | Agent models, turn limits, budget cap, watchdog settings |
| `config/rate_limits.json` | Per-model RPM and TPM limits |
| `config/pricing.json` | Per-token USD rates for cost reporting |

Key `setup.json` fields:

```json
{
  "debate": { "min_turns_per_side": 10, "max_session_cost_usd": 2.00 },
  "agents": {
    "father":  { "model": "claude-sonnet-4-6" },
    "pro_son": { "model": "claude-haiku-4-5" },
    "con_son": { "model": "claude-haiku-4-5" }
  }
}
```

---

## Usage

```bash
uv run debate --topic "AI will replace human workers"
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--topic TEXT` | *(required)* | The debate topic |
| `--config PATH` | `config/` | Path to config directory |
| `--dry-run` | `False` | Validate config only; no LLM calls |

---

## Dry Run

```bash
uv run debate --topic "AI ethics" --dry-run
```

Loads and validates `setup.json`, prints agent model assignments, then
exits without making any API calls.

---

## Web GUI

A responsive Flask + Bootstrap 5 interface is available alongside the CLI.

```bash
uv run debate-web          # starts on http://localhost:5000
PORT=8080 uv run debate-web  # custom port via env var
```

1. Open `http://localhost:5000` in your browser.
2. Type a debate topic and click **Debate**.
3. Watch colour-coded chat bubbles appear for each agent turn once the debate completes.
4. The **Verdict** and **Cost** cards render automatically at the end.

The web server uses the same `config/` directory and `ANTHROPIC_API_KEY` as the CLI.
No database or additional infrastructure is required.

---

## Debate Output

```
[INFO]  Loading config from 'config/' ...
[INFO]  Config loaded. Schema version: 1.0

[DEBATE STARTING] Topic: AI will replace human workers

============================================================
[VERDICT]
  Winner    : pro_son
  Turns     : 21
  Reasoning : pro_son scored 23/30, con_son scored 21/30. ...
============================================================

[COST REPORT]
  Total : $0.4821 / $2.00  (24.1% of budget)
```

---

## Running Tests

```bash
# Unit tests (fast, no API key needed)
uv run pytest -m "not slow"

# Integration tests (stubbed LLM, no API key needed)
uv run pytest -m slow

# Full suite with coverage
uv run pytest --cov=src --cov-fail-under=85
```

---

## Cost Reporting

The `CostReporter` accumulates prompt and completion tokens per agent,
applies per-model USD rates from `config/pricing.json`, and prints a
summary table before exit. A warning is logged when utilisation reaches
90% of the budget cap; the loop exits early at 100%.

---

## Golden Rules

Every source file in `src/` must satisfy all five:

1. **≤ 150 lines** — split into sub-modules if exceeded
2. **0 ruff violations** — `line-length = 88`, rules E/W/F/I
3. **> 85% test coverage** — enforced by `--cov-fail-under=85`
4. **TDD** — failing tests written before each implementation
5. **No hardcoded values; no direct agent-to-agent messages**

---

## Project Structure

```
src/
  agents/         FatherAgent, ProSonAgent, ConSonAgent, BaseAgent
  engine/         DebateEngine, StateManager
  infrastructure/ Gatekeeper, Watchdog, CostReporter, ConfigLoader, LoggerManager
  schemas/        debate_message.json, verdict.json
  skills/         WebSearchTool, LogicAnalyzerTool
  ui/             DebateCLI
tests/
  unit/           Per-module unit tests (TDD)
  integration/    Full-debate integration test suite
config/           setup.json, rate_limits.json, pricing.json
docs/             PRD.md, PLAN.md, TODO.md
```

---

## Agent Roles

| Agent | Model | Role |
|---|---|---|
| Father | claude-sonnet-4-6 | Moderator, router, and judge |
| Pro Son | claude-haiku-4-5 | Argues FOR the topic |
| Con Son | claude-haiku-4-5 | Argues AGAINST the topic |

All messages route through the Father. Direct agent-to-agent messages
are prohibited by design and enforced in the routing layer.

---

## JSON Message Contract

```json
{
  "message_id": "uuid-v4",
  "sender":     "pro_son | con_son | father",
  "recipient":  "father | pro_son | con_son",
  "turn":       2,
  "content":    "Argument text...",
  "sources":    ["https://example.com/article"],
  "token_count": 42,
  "timestamp":  "2026-05-25T12:00:00+00:00"
}
```

---

## Verdict Format

```json
{
  "verdict_id": "uuid-v4",
  "winner":     "pro_son",
  "draw":       false,
  "reasoning":  "pro_son scored 23/30, con_son scored 21/30...",
  "turn_count": 21,
  "timestamp":  "2026-05-25T13:00:00+00:00"
}
```

`draw` is always `false` — a tiebreaker (last-4-turn momentum) resolves
equal scores.

---

## State Machine

```
INITIALIZATION → IN_PROGRESS → EVALUATION → TERMINATED
```

`StateManager` transitions the state automatically as messages and the
verdict are recorded.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Agent hangs > 30 s | `Watchdog` retries once, then raises `WatchdogError` |
| Budget cap reached | Turn loop exits early; `evaluate()` still runs |
| Position drift | Son agent retries up to 2×; raises `AgentFailureError` after |
| Invalid JSON from LLM | `MessageParseError` raised in `parse_response` |
| Schema violation | `jsonschema.ValidationError` caught → `MessageParseError` |

---

## Persuasiveness Rubric

The Father scores each debater on three dimensions (1–10 each):

| Dimension | Criterion |
|---|---|
| Clarity | How clearly were arguments expressed? |
| Evidence Quality | How well were claims supported by cited sources? |
| Logical Consistency | Were arguments internally consistent across all turns? |

Total = Clarity + Evidence + Logic (max 30). Higher total wins.

---

## Extensibility

New tools are added by subclassing `AgentSkill`:

```python
class MyTool(AgentSkill):
    skill_name = "my_tool"

    def execute(self, query: str) -> SkillResult:
        ...
```

Inject the instance into `engine.pro_son.skills` or `engine.con_son.skills`.
The `LogicAnalyzerTool` (offline, zero network calls) is included as a
fallback when `SEARCH_API_KEY` is unavailable.

---

## License

MIT

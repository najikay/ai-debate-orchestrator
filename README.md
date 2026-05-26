# AI Debate System

**Group:** NajAmjad | **Course:** AI Orchestration | **Version:** 2.0.1

> A production-quality multi-agent orchestration system: three Claude-powered agents
> conduct a fully scored, structured debate on any topic you supply — with live cost
> tracking, Chain-of-Thought reasoning, and a responsive web UI.

---

## Introduction

The AI Debate System wires three LLM agents into a structured debate protocol.
**Father** (Claude Sonnet) moderates and judges; **Pro Son** and **Con Son**
(Claude Haiku) argue for and against the topic respectively. Every inter-agent
message is a validated JSON envelope. After a minimum of 20 turns the Father
scores both debaters on a three-dimension rubric and declares a non-draw winner.

**Key technical strengths:**

| Strength | Implementation |
|---|---|
| Custom Agent SDK | `BaseAgent` ABC with JSON schema validation, retry logic, and Gatekeeper routing — no LangChain dependency |
| Chain-of-Thought reasoning | Structured `{opponent_analysis, debate_strategy, argument}` CoT JSON forces explicit reasoning before every argument |
| Defensive engineering | Per-call `max_tokens=4096` cap, budget enforcement, resilient `_extract_json()` strips markdown fences, `_enforce_position` retry (max 2×) |
| Live cost tracking | `Gatekeeper` accumulates token totals → `_sync_costs()` wires them to `CostReporter` → fuzzy model-ID matching prevents silent `$0` costs |
| Watchdog recovery | `concurrent.futures` timeout with one retry; graceful `WatchdogError` shutdown saves partial state to disk |
| Web + CLI dual interface | Same `DebateEngine` serves both `uv run debate` (CLI) and `uv run debate-web` (Flask + Bootstrap 5) |

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Check: `python --version` |
| `uv` | ≥ 0.4.0 | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ANTHROPIC_API_KEY` | — | **Required.** Get yours at console.anthropic.com |
| `SEARCH_API_KEY` | — | Optional — enables live web search (Tavily / Brave) |

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd A2

# 2. Copy the environment template and fill in your API key
cp .env-example .env
# Open .env and set:
#   ANTHROPIC_API_KEY=sk-ant-...    ← required
#   SEARCH_API_KEY=...              ← optional

# 3. Install all dependencies (runtime + dev tools in one step)
uv sync --extra dev
```

> **`.env` is git-ignored** — it will never be staged or committed.
> The committed `.env-example` documents every variable with comments.

---

## How to Run

### Interactive CLI

```bash
uv run debate --topic "AI will replace human workers"
```

| Flag | Default | Description |
|---|---|---|
| `--topic TEXT` | *(required)* | The debate topic |
| `--config PATH` | `config/` | Path to the config directory |
| `--dry-run` | `False` | Validate config only; makes no LLM calls |

**Dry-run mode** — validate your setup without spending tokens:

```bash
uv run debate --topic "AI ethics" --dry-run
```

### Flask Web GUI

```bash
uv run debate-web                  # starts at http://localhost:5000
PORT=8080 uv run debate-web        # custom port via env var
```

Open `http://localhost:5000` in your browser, enter a topic, and click **Debate**.
Colour-coded chat bubbles stream each agent's turn. The **Verdict** card shows the
winner, per-dimension numerical scores (Clarity / Evidence / Logic out of 10), and
the Father's full reasoning. The **Cost** card shows live USD spend and budget
utilisation.

### Test Suite and Linter

```bash
# Unit tests only — fast, no API key required
uv run pytest -m "not slow"

# Integration tests — stubbed LLM, no API key required
uv run pytest -m slow

# Full suite with coverage enforcement (≥ 85%)
uv run pytest --cov=src --cov-fail-under=85

# Linter — zero-tolerance ruff check across the entire repo
uv run ruff check .
```

---

## Visual Walkthrough

### Main Dashboard — Topic Form and Live Debate

![Main Dashboard](docs/images/main_page.png)

### Final Verdict — Numerical Scores and Father's Reasoning

![Final Verdict](docs/images/final_verdict.png)

> Drop `main_page.png` and `final_verdict.png` into `docs/images/` to render
> these screenshots on GitHub.

---

## Architecture

See `docs/PLAN.md` for the full C4 context diagram, class hierarchy, and layered
architecture overview.

**Layers (bottom → top):**

| Layer | Key classes |
|---|---|
| Infrastructure | `ConfigLoader`, `LoggerManager`, `Gatekeeper`, `Watchdog`, `CostReporter` |
| Skills | `WebSearchTool`, `LogicAnalyzerTool` |
| Agents | `BaseAgent`, `FatherAgent`, `ProSonAgent`, `ConSonAgent` |
| Engine | `StateManager`, `DebateEngine` |
| UI | `DebateCLI` (CLI), `app.py` (Flask) |

---

## Agent Roles

| Agent | Model | Role |
|---|---|---|
| Father | `claude-sonnet-4-6` | Moderator, message router, and final judge |
| Pro Son | `claude-haiku-4-5` | Argues FOR the topic; must never concede |
| Con Son | `claude-haiku-4-5` | Argues AGAINST the topic; must never concede |

All messages route exclusively through the Father. Direct agent-to-agent
communication is prohibited by design and enforced in the routing layer.

---

## Configuration

| File | Purpose |
|---|---|
| `config/setup.json` | Agent models, turn limits, budget cap, watchdog settings |
| `config/rate_limits.json` | Per-model RPM and TPM limits |
| `config/pricing.json` | Per-token USD rates used by `CostReporter` |

Key `setup.json` fields:

```json
{
  "debate": { "min_turns_per_side": 10, "max_session_cost_usd": 2.00 },
  "agents": {
    "father":  { "model": "claude-sonnet-4-6" },
    "pro_son": { "model": "claude-haiku-4-5" },
    "con_son": { "model": "claude-haiku-4-5" }
  },
  "watchdog": { "timeout_seconds": 30, "max_retries": 1 }
}
```

`ANTHROPIC_API_KEY` is the only secret needed to run a full debate. All other
values live in config files — **no API keys in source**.

---

## Usage

### CLI

```bash
uv run debate --topic "AI will replace human workers"
```

| Flag | Default | Description |
|---|---|---|
| `--topic TEXT` | *(required)* | The debate topic |
| `--config PATH` | `config/` | Path to config directory |
| `--dry-run` | `False` | Validate config only; no LLM calls |

### Dry Run

```bash
uv run debate --topic "AI ethics" --dry-run
```

Loads and validates `setup.json`, prints agent model assignments, then
exits without making any API calls. Useful for CI config checks.

---

## Web GUI

A responsive Flask + Bootstrap 5 interface is available alongside the CLI.

```bash
uv run debate-web          # starts on http://localhost:5000
PORT=8080 uv run debate-web  # custom port via env var
```

1. Open `http://localhost:5000` in your browser.
2. Enter a debate topic and click **Debate**.
3. Colour-coded chat bubbles appear for each agent turn once the debate completes.
4. The **Verdict** card shows the winner, per-dimension numerical scores
   (Clarity / Evidence / Logic out of 10 each), and the Father's full reasoning.
5. The **Cost** card shows total spend and budget utilisation.

The web server reads the same `config/` directory and `ANTHROPIC_API_KEY` as
the CLI. No database or additional infrastructure is required.

---

## Screenshots

### Main Page — Topic Form & Live Debate

![Main page — topic input form and colour-coded debate bubbles]

[text](README.md) ![text](docs/images/1.PNG) ![text](docs/images/2.PNG) ![text](docs/images/3.PNG) ![text](docs/images/4.PNG) ![text](docs/images/5.PNG) ![text](docs/images/6.PNG) ![text](docs/images/7.PNG) ![text](docs/images/8.PNG) ![text](docs/images/9.PNG) ![text](docs/images/10.PNG) ![text](docs/images/11.PNG) ![text](docs/images/12.PNG) ![text](docs/images/13.PNG) ![text](docs/images/14.PNG) ![text](docs/images/15.PNG) ![text](docs/images/16.PNG) ![text](docs/images/17.PNG) ![text](docs/images/18.PNG) ![text](docs/images/19.PNG) ![text](docs/images/20.PNG) ![text](docs/images/21.PNG)

### Final Verdict — Scores & Reasoning

![Final verdict card with numerical scores and Father's reasoning]
![alt text](docs/images/22.PNG)

> Drop `main_page.png` and `final_verdict.png` into `docs/images/` to make these
> images visible in GitHub.

---

## Debate Output

```
[INFO]  Loading config from 'config/' ...
[INFO]  Config loaded. Schema version: 1.0
[INFO]  Agents: father=claude-sonnet-4-6 | pro_son=claude-haiku-4-5 | con_son=claude-haiku-4-5

[DEBATE STARTING]
  Topic    : AI will replace human workers
  Min turns: 10 per side (20 total)

  ... (colour-coded turn output) ...

╔══════════════════════════════════════╗
║              VERDICT                 ║
║  Winner  : pro_son                   ║
║  Turns   : 21                        ║
║  Scores  : Pro 24/30  Con 21/30      ║
╚══════════════════════════════════════╝

[COST REPORT]  Total: $0.4821 / $2.00  (24.1% of budget)
```

---

## Cost Reporting

`CostReporter` accumulates prompt and completion tokens per agent via
`DebateEngine._sync_costs()`, which pulls live totals from `Gatekeeper` at every
turn boundary. Per-model USD rates are read from `config/pricing.json`. A `[WARN]`
is logged when utilisation reaches 90% of the budget cap; the turn loop exits early
at 100%.

Fuzzy model-ID matching (`_find_rates`) handles Anthropic date-suffix IDs
(e.g. `claude-haiku-4-5-20251001`) that would otherwise miss an exact key lookup.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Agent hangs > 30 s | `Watchdog` retries once; raises `WatchdogError` on second timeout |
| Budget cap reached | Turn loop exits early; `evaluate()` still runs on partial transcript |
| Position drift | Son agent retries up to 2×; `AgentFailureError` raised after exhaustion |
| Invalid JSON from LLM | `_extract_json()` strips fences + extracts `{…}`; `MessageParseError` on failure |
| Schema violation | `jsonschema.ValidationError` caught → `MessageParseError` |
| Unknown model ID in pricing | Fuzzy prefix match (≥ 60%); flagged `"UNKNOWN PRICE"` + `[WARN]` if below threshold |

---

## Persuasiveness Rubric

The Father scores each debater on three dimensions (1–10 each, max 30):

| Dimension | Criterion |
|---|---|
| Clarity | How clearly and concisely were arguments expressed? |
| Evidence Quality | How well were claims supported by cited sources? |
| Logical Consistency | Were arguments internally consistent across all turns? |

Equal totals trigger a momentum tiebreaker (final 4 turns). Draws are
prohibited — `"draw": false` is enforced by the `verdict.json` schema.

---

## Golden Rules

Every source file in `src/` must satisfy all five simultaneously:

1. **≤ 150 lines** — split into sub-modules if exceeded
2. **0 ruff violations** — `line-length = 88`, rules E/W/F/I enforced
3. **> 85% test coverage** — enforced by `--cov-fail-under=85`
4. **TDD** — failing tests written before each implementation
5. **No hardcoded values; no direct agent-to-agent messages**

---

## Project Structure

```
A2/
├── config/
│   ├── pricing.json         USD/1K token rates per model
│   ├── rate_limits.json     Per-model RPM / TPM caps
│   └── setup.json           Agent models, turn limits, budget cap
├── docs/
│   ├── PLAN.md              C4 diagrams, class hierarchy, roadmap
│   ├── PRD.md               Product requirements and hotfix log
│   └── TODO.md              Phased execution checklist
├── src/
│   ├── agents/              FatherAgent, ProSonAgent, ConSonAgent, BaseAgent
│   ├── engine/              DebateEngine, StateManager
│   ├── infrastructure/      Gatekeeper, Watchdog, CostReporter, ConfigLoader, LoggerManager
│   ├── schemas/             debate_message.json, verdict.json
│   ├── skills/              WebSearchTool, LogicAnalyzerTool
│   └── ui/                  debate_cli.py (CLI), app.py (Flask)
├── templates/               Bootstrap 5 + jQuery web UI templates
├── tests/
│   ├── unit/                Per-module TDD test suite
│   └── integration/         Full-debate integration tests
├── .env-example             Environment variable template (safe to commit)
├── pyproject.toml           uv / ruff / pytest configuration
└── README.md
```

---

## JSON Message Contract

Every agent message is validated against `src/schemas/debate_message.json`:

```json
{
  "message_id": "uuid-v4",
  "sender":     "pro_son | con_son | father",
  "recipient":  "father | pro_son | con_son",
  "turn":       2,
  "content":    "Argument text...",
  "sources":    ["https://example.com/article"],
  "token_count": 342,
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
  "reasoning":  "pro_son scored 24/30 vs con_son 21/30...",
  "turn_count": 21,
  "timestamp":  "2026-05-25T13:00:00+00:00"
}
```

`draw` is always `false`. Equal totals resolve via the last-4-turn momentum
tiebreaker embedded in `FatherAgent.evaluate()`.

---

## State Machine

```
INITIALIZATION → IN_PROGRESS → EVALUATION → TERMINATED
```

`StateManager` transitions the state automatically as messages and the
verdict are recorded. All transitions are one-directional.

---

## Extensibility

Add a new agent skill by subclassing `AgentSkill`:

```python
class MyTool(AgentSkill):
    skill_name = "my_tool"

    def execute(self, query: str) -> SkillResult:
        ...
```

Place the module in `src/skills/` and declare it in `config/setup.json` under
`enabled_skills`. The `LogicAnalyzerTool` (offline, zero network calls) is
included as a built-in fallback when `SEARCH_API_KEY` is unavailable.

---

## License

MIT

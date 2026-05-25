# Product Requirements Document
## AI Debate System — Assignment 2
**Project:** AI Orchestration Course — Group NajAmjad
**Version:** 1.0.0
**Date:** 2026-05-25
**Status:** Draft — Pending Approval

---

## 1. Project Overview

### 1.1 Summary

The AI Debate System is a multi-agent orchestration application in which three
LLM-powered agents conduct a structured, evidence-based debate on a user-supplied
topic. All inter-agent communication is routed exclusively through a Father (Judge)
agent via JSON message envelopes. The system terminates when the Father declares a
winner based on persuasiveness; draws are explicitly prohibited.

### 1.2 User Problem

Academic and professional users need a reproducible way to stress-test arguments
from multiple perspectives. Existing single-LLM chat systems produce only one
viewpoint, lack structured turn discipline, and cannot cite live evidence. Users
have no visibility into token costs or debate state, making it hard to audit or
extend outcomes.

### 1.3 Target Audience

- Students and instructors in AI / argumentation courses.
- Researchers needing automated adversarial literature review.
- Developers learning multi-agent orchestration patterns.

---

## 2. System Goals

### 2.1 Agent Roles

| Agent | Role | Constraint |
|-------|------|-----------|
| Father | Moderator & Judge | Routes all messages; declares winner |
| Pro Son | Affirmative debater | Must argue FOR the topic at all times |
| Con Son | Negative debater | Must argue AGAINST the topic at all times |

### 2.2 Communication Contract

- Every message exchanged between agents MUST be a valid JSON object conforming to
  the `DebateMessage` schema (see Section 4.2).
- No agent may address another agent directly. All routing passes through the Father.
- The Father is the sole entity allowed to write to the shared debate log.

### 2.3 Debate Flow

1. User submits a topic string via CLI or UI.
2. Father opens the debate, assigns positions, and sends the first prompt to Pro Son.
3. Agents alternate: Pro Son → Father → Con Son → Father (one full round = 2 turns).
4. Minimum 10 turns per side (20 total exchanges) before the Father may evaluate.
5. Each agent MUST call the Web Search tool at least once every 3 turns to supply
   live evidence; responses lacking a `sources` field are rejected.
6. Father evaluates persuasiveness using a rubric (clarity, evidence quality,
   logical consistency) and posts a `VERDICT` message.
7. Verdict must name exactly one winner; the `draw` field must always be `false`.

### 2.4 Mandatory Web Search Integration

- Both Pro Son and Con Son possess a `web_search(query: str) -> SearchResult` tool.
- Tool invocations are logged with query string, timestamp, and result snippet.
- The Gatekeeper (Section 3.3) enforces rate limits on search calls to prevent
  runaway API usage.

---

## 3. Functional Requirements

### 3.1 Agent Requirements

| ID | Requirement |
|----|-------------|
| AG-01 | Father must parse every incoming JSON message and validate it against `DebateMessage` schema before routing. |
| AG-02 | Pro Son must only produce arguments supporting the topic; any deviation triggers an automatic retry (max 2). |
| AG-03 | Con Son must only produce arguments opposing the topic; same retry rule applies. |
| AG-04 | Each Son agent must embed a `sources` array in every response turn. |
| AG-05 | Agents must not fabricate citations; all sources must originate from Web Search tool output. |
| AG-06 | Father must track turn count and refuse to issue a verdict before turn 20. |

### 3.2 Debate State Requirements

| ID | Requirement |
|----|-------------|
| DS-01 | A `DebateState` object must be maintained in memory and serializable to JSON at any point. |
| DS-02 | State must record: topic, turn number, agent responses, sources, timestamps, and token counts. |
| DS-03 | State must survive a Watchdog restart without losing prior turns. |

### 3.3 API Gatekeeper Requirements

| ID | Requirement |
|----|-------------|
| GK-01 | All LLM API calls must pass through the Gatekeeper before dispatch. |
| GK-02 | Gatekeeper enforces per-model rate limits loaded from `rate_limits.json`. |
| GK-03 | Excess requests are queued (FIFO); queue depth is bounded at 50 items. |
| GK-04 | Gatekeeper exposes token-usage metrics per agent per model for cost reporting. |

---

## 4. Data Contracts

### 4.1 Environment & Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys and secrets (never committed) |
| `.env-example` | Template with placeholder values (committed) |
| `config/setup.json` | System-level parameters (model names, turn limits, log paths) |
| `config/rate_limits.json` | Per-model RPM / TPM caps |

Zero hardcoded values are permitted anywhere in application source.

### 4.2 DebateMessage JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["message_id", "sender", "recipient", "turn", "content", "sources", "token_count", "timestamp"],
  "properties": {
    "message_id": { "type": "string", "format": "uuid" },
    "sender":     { "type": "string", "enum": ["father", "pro_son", "con_son"] },
    "recipient":  { "type": "string", "enum": ["father", "pro_son", "con_son"] },
    "turn":       { "type": "integer", "minimum": 1 },
    "content":    { "type": "string", "minLength": 1 },
    "sources":    { "type": "array", "items": { "type": "string" } },
    "token_count":{ "type": "integer", "minimum": 0 },
    "timestamp":  { "type": "string", "format": "date-time" }
  }
}
```

### 4.3 Verdict JSON Schema

```json
{
  "required": ["verdict_id", "winner", "draw", "reasoning", "turn_count", "timestamp"],
  "properties": {
    "verdict_id": { "type": "string", "format": "uuid" },
    "winner":     { "type": "string", "enum": ["pro_son", "con_son"] },
    "draw":       { "type": "boolean", "const": false },
    "reasoning":  { "type": "string", "minLength": 50 },
    "turn_count": { "type": "integer", "minimum": 20 },
    "timestamp":  { "type": "string", "format": "date-time" }
  }
}
```

---

## 5. Non-Functional Requirements

### 5.1 Performance & Reliability

| ID | Requirement |
|----|-------------|
| NF-01 | Each LLM call must complete within 30 seconds; Watchdog kills and retries after timeout. |
| NF-02 | System must complete a 20-turn debate end-to-end without manual intervention. |
| NF-03 | Log rotation must maintain no more than 20 log files of 500 lines each (FIFO eviction). |

### 5.2 Code Quality (Golden Rules)

| Rule | Threshold |
|------|-----------|
| Max lines per file | 150 |
| Ruff linting violations | 0 |
| Pytest coverage | > 85 % |
| Development methodology | TDD (tests first) |

### 5.3 Security

- API keys loaded exclusively from environment variables.
- No secrets in source files or logs.
- Web Search queries sanitized before dispatch.

---

## 6. Costs & Pricing

### 6.1 Token Tracking

- Every API call records `prompt_tokens`, `completion_tokens`, and `total_tokens`
  against the calling agent and model name.
- The `CostReporter` component reads per-model pricing from `config/pricing.json`
  (USD per 1 000 tokens, input and output rates separately).
- A cost summary is printed at debate end: per-agent breakdown and total session cost.

### 6.2 Budget Controls

- `config/setup.json` exposes a `max_session_cost_usd` parameter.
- If cumulative cost exceeds the budget cap, the system emits a warning and, after
  one additional turn, gracefully terminates and triggers the verdict phase early.
- All cost data is appended to the debate state JSON for auditability.

### 6.3 Supported Models (initial)

| Model Alias | Provider | Input $/1K tok | Output $/1K tok |
|-------------|----------|----------------|-----------------|
| `claude-sonnet-4-6` | Anthropic | see pricing.json | see pricing.json |
| `claude-haiku-4-5` | Anthropic | see pricing.json | see pricing.json |

Pricing values are never hardcoded; they are read from `config/pricing.json` at
runtime so updates require no code changes.

---

## 7. Extensibility

### 7.1 Plugin Architecture

The system exposes a formal `AgentSkill` interface. New capabilities (e.g., a
`calculator` tool, a `database_lookup` tool) are registered by:

1. Implementing the `AgentSkill` abstract base class.
2. Placing the module in `src/skills/`.
3. Declaring the skill in `config/setup.json` under `enabled_skills`.

No changes to core agent or orchestration code are required.

### 7.2 Agent Extensibility

Additional debater agents (e.g., a neutral third party) can be added by subclassing
`BaseDebaterAgent` and registering the new role in `config/setup.json`. The Father's
routing table is built dynamically from the config.

### 7.3 Versioning

All config schemas are versioned via a `schema_version` field. The loader validates
the version on startup and raises a `ConfigVersionError` if incompatible.

---

## 8. Configuration Portability

- All environment-specific values (API keys, base URLs, model names) reside in `.env`.
- Path values in `setup.json` use relative paths resolved from the project root.
- The project is runnable on any POSIX system with Python 3.11+ and `uv` without
  modification to source files.
- A single `make setup` (or `uv sync`) command installs all dependencies and
  scaffolds the config directory from `.env-example` and `config/` templates.

---

## 9. Acceptance Criteria & KPIs

| ID | Criterion | Pass Threshold |
|----|-----------|---------------|
| AC-01 | Minimum turns per side before verdict | 10 turns each (20 total) |
| AC-02 | Web Search invocations per side | At least once every 3 turns |
| AC-03 | JSON schema validation pass rate | 100 % of messages |
| AC-04 | Timeout recovery (Watchdog) | Stuck call killed and retried within 35 s |
| AC-05 | Debate completes without manual intervention | 100 % of runs |
| AC-06 | Verdict is non-draw | Always; `draw: false` enforced by schema |
| AC-07 | Ruff violations on final commit | 0 |
| AC-08 | Test coverage | > 85 % |
| AC-09 | No hardcoded secrets or values | 0 occurrences (CI check) |
| AC-10 | Cost report generated at debate end | Present in every run output |

---

## 10. Out of Scope (v1.0)

- Real-time streaming of agent responses to the UI.
- Multi-topic / bracket-style tournament mode.
- Fine-tuning or RLHF on debate outcomes.
- Persistent storage beyond a single session's JSON state file.

# Product Requirements Document
## AI Debate System — Assignment 2
**Project:** AI Orchestration Course — Group NajAmjad
**Version:** 2.0.0
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
  the `DebateMessage` schema (see Section 5.2).
- No agent may address another agent directly. All routing passes through the Father.
- The Father is the sole entity allowed to write to the shared debate log.

### 2.3 Debate Flow

1. User submits a topic string via CLI or UI.
2. Father opens the debate, assigns positions, and sends the first prompt to Pro Son.
3. Agents alternate: Pro Son → Father → Con Son → Father (one full round = 2 turns).
4. Minimum 10 turns per side (20 total exchanges) before the Father may evaluate.
5. Each agent MUST call the Web Search tool at least once every 3 turns to supply
   live evidence; responses lacking a `sources` field are rejected.
6. Father evaluates persuasiveness using the rubric defined in Section 9 and posts
   a `VERDICT` message.
7. Verdict must name exactly one winner; the `draw` field must always be `false`.

### 2.4 Mandatory Web Search Integration

- Both Pro Son and Con Son possess a `web_search(query: str) -> SearchResult` tool.
- Tool invocations are logged with query string, timestamp, and result snippet.
- The Gatekeeper enforces rate limits on search calls to prevent runaway API usage.

### 2.5 Offline Logic Analyzer Tool (Fallback & Analytical Aid)

- Both Son agents also possess a `logic_analyze(query: str) -> SkillResult` tool
  implemented by `LogicAnalyzerTool`.
- This skill is **purely local** — it performs string analysis with zero network calls,
  making it available regardless of API key availability or network connectivity.
- **Primary use:** fallback when `SEARCH_API_KEY` is absent or rate-limit exhausted;
  also used by agents to self-audit the logical structure of their own arguments before
  submission.
- **Analysis provided:** premise-keyword count, conclusion-keyword count, word count,
  sentence count, and average sentence length — distilled into a rubric snippet list.
- The `setup.json` key `enabled_skills` controls which tools are injected at runtime
  (e.g. `["web_search", "logic_analyzer"]`); the engine reads this at startup.

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

## 4. State Machine & Transitions

### 4.1 DebateState Lifecycle

The `DebateState` object passes through exactly four named states. Transitions are
one-directional; there is no rollback path once a state is left.

```
┌──────────────────┐
│  INITIALIZATION  │  ← User supplies topic; config validated; agents instantiated.
└────────┬─────────┘
         │ trigger: DebateEngine.start() called
         ▼
┌──────────────────┐
│   IN_PROGRESS    │  ← Turn loop executing; messages exchanged; costs tracked.
└────────┬─────────┘
         │ trigger: turn_count ≥ 20 AND Father requests evaluation
         ▼           OR budget cap exceeded (early exit path)
┌──────────────────┐
│   EVALUATION     │  ← Father scoring transcript; rubric applied; winner selected.
└────────┬─────────┘
         │ trigger: Verdict object produced and validated
         ▼
┌──────────────────┐
│   TERMINATED     │  ← Verdict written; cost report printed; log files flushed.
└──────────────────┘
```

### 4.2 State Transition Table

| From | To | Trigger | Guard | Side Effects |
|------|----|---------|-------|-------------|
| — | INITIALIZATION | `DebateEngine.__init__()` | Config files exist; API keys in env | `DebateState` object created with empty transcript |
| INITIALIZATION | IN_PROGRESS | `DebateEngine.start(topic)` | Topic is non-empty string | `open_debate()` called; turn counter set to 0 |
| IN_PROGRESS | IN_PROGRESS | Each completed agent turn | Turn count < 20 OR budget not exceeded | Message appended to transcript; token costs recorded |
| IN_PROGRESS | EVALUATION | Turn count reaches 20 | Father calls `_check_min_turns()` → True | Rubric scoring begins; no further agent arguments accepted |
| IN_PROGRESS | EVALUATION | Budget cap exceeded mid-turn | `_check_budget()` → True | WARNING logged; current turn completed; evaluation forced |
| EVALUATION | TERMINATED | `Verdict` produced | `draw == false`; winner is `pro_son` or `con_son` | `record_verdict()` called; cost report printed; CLI exits |
| Any | TERMINATED | `WatchdogError` (after max retries) | Two consecutive timeouts | ERROR logged; partial state saved to JSON; exit code 1 |

### 4.3 State Object Fields

```json
{
  "state_id": "<uuid>",
  "status": "INITIALIZATION | IN_PROGRESS | EVALUATION | TERMINATED",
  "topic": "<string>",
  "turn_count": 0,
  "transcript": [],
  "verdict": null,
  "events": [],
  "cost_summary": null,
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>"
}
```

### 4.4 Event Log Format

All state transitions and anomalies are appended to `DebateState.events`:

```json
{
  "event_id": "<uuid>",
  "event_type": "STATE_TRANSITION | WATCHDOG_TIMEOUT | BUDGET_WARNING | RETRY",
  "from_status": "<status>",
  "to_status": "<status>",
  "detail": "<human-readable description>",
  "timestamp": "<ISO-8601>"
}
```

---

## 5. Data Contracts

### 5.1 Environment & Configuration Files

| File | Committed | Contains |
|------|-----------|---------|
| `.env` | No | `ANTHROPIC_API_KEY`, `SEARCH_API_KEY` |
| `.env-example` | Yes | Placeholder keys, comments |
| `config/setup.json` | Yes | Model names, turn limits, log paths |
| `config/rate_limits.json` | Yes | Per-model RPM/TPM caps |
| `config/pricing.json` | Yes | USD/1K token rates per model |

Zero hardcoded values are permitted anywhere in application source.

### 5.2 DebateMessage JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["message_id","sender","recipient","turn","content","sources","token_count","timestamp"],
  "properties": {
    "message_id": { "type": "string", "format": "uuid" },
    "sender":     { "type": "string", "enum": ["father","pro_son","con_son"] },
    "recipient":  { "type": "string", "enum": ["father","pro_son","con_son"] },
    "turn":       { "type": "integer", "minimum": 1 },
    "content":    { "type": "string", "minLength": 1 },
    "sources":    { "type": "array",  "items": { "type": "string" } },
    "token_count":{ "type": "integer","minimum": 0 },
    "timestamp":  { "type": "string", "format": "date-time" }
  }
}
```

### 5.3 Verdict JSON Schema

```json
{
  "required": ["verdict_id","winner","draw","reasoning","turn_count","timestamp"],
  "properties": {
    "verdict_id": { "type": "string",  "format": "uuid" },
    "winner":     { "type": "string",  "enum": ["pro_son","con_son"] },
    "draw":       { "type": "boolean", "const": false },
    "reasoning":  { "type": "string",  "minLength": 50 },
    "turn_count": { "type": "integer", "minimum": 20 },
    "timestamp":  { "type": "string",  "format": "date-time" }
  }
}
```

---

## 6. Edge-Case & Error Handling Matrix

Every failure mode has an explicit, deterministic resolution path. The system
never silently swallows errors.

### 6.1 Web Search API Failures

| Failure Mode | Trigger | Immediate Action | Recovery | User-Visible Output |
|-------------|---------|-----------------|----------|-------------------|
| HTTP 5xx from search API | Search call returns 500/502/503 | `SkillError` raised in `WebSearchTool.execute()` | Agent retries search with same query (once); if still fails, uses empty `sources: []` | `[WARN] Web search failed on turn N. Agent will proceed without new sources.` |
| HTTP 429 (rate limit) | Search API rate limit exceeded | `SkillError` raised | Gatekeeper queues next search; waits for RPM window reset (up to 60 s) | `[WARN] Search rate limit hit. Waiting Xs before retry.` |
| Network timeout (> 10 s) | No response from search API | `requests.Timeout` caught | Treated as 5xx — same single retry | `[WARN] Search timed out on turn N.` |
| Malformed search response | API returns non-JSON or missing keys | `_parse_response()` raises `SkillError` | Agent continues with empty `sources: []` | `[WARN] Search response unparseable on turn N.` |
| API key missing | `SEARCH_API_KEY` not in `.env` | `ValueError` raised at startup | System exits with code 1 before debate starts | `[ERROR] SEARCH_API_KEY is not set. Add it to .env.` |

### 6.2 Agent JSON Hallucination / Malformed Output

| Failure Mode | Trigger | Immediate Action | Recovery | User-Visible Output |
|-------------|---------|-----------------|----------|-------------------|
| Non-JSON response from LLM | `json.loads()` fails in `parse_response()` | `MessageParseError` raised | Agent retried (max 2 attempts); prompt re-sent with stricter JSON instruction | `[WARN] Agent pro_son returned non-JSON on turn N. Retrying (1/2).` |
| JSON valid but schema invalid | `jsonschema.validate()` fails | `MessageParseError` raised | Retry with JSON repair prompt | `[WARN] Schema violation in pro_son response on turn N. Retrying (2/2).` |
| Both retries fail | 2 consecutive `MessageParseError` | `AgentFailureError` raised | Father skips the turn, logs it as a forfeit, and proceeds | `[ERROR] pro_son failed after 2 retries on turn N. Turn forfeited.` |
| Position violation (Pro argues Con) | `_enforce_position()` detects negative argument | Position enforcer raises retry signal | Re-prompt with explicit position reminder (max 2 retries) | `[WARN] pro_son broke position on turn N. Retrying.` |
| `sources` field empty | `sources: []` in response | Logged as warning | Accepted as-is (search enforcement is per 3-turn window, not per turn) | `[WARN] pro_son provided no sources on turn N.` |

### 6.3 Watchdog Thread Failures

| Failure Mode | Trigger | Immediate Action | Recovery | User-Visible Output |
|-------------|---------|-----------------|----------|-------------------|
| LLM call hangs (first timeout) | `concurrent.futures` timeout at N seconds | Future cancelled; `WatchdogTimeout` logged | `_kill_and_retry()` re-submits call once | `[WATCHDOG] Timeout on turn N (attempt 1). Retrying.` |
| LLM call hangs (second timeout) | Second timeout after retry | `WatchdogError` raised | Debate engine catches error; saves partial state to JSON; exits with code 1 | `[WATCHDOG] Fatal timeout on turn N after retry. State saved to logs/.` |
| Thread pool exhausted | All executor threads occupied | New submission blocks | Gatekeeper queue absorbs backpressure up to 50 items; logs queue depth | `[WARN] Gatekeeper queue at N/50 items.` |
| Watchdog misconfigured (timeout = 0) | `setup.json` has `timeout_seconds: 0` | `ConfigValidationError` at startup | System exits before debate starts | `[ERROR] watchdog.timeout_seconds must be > 0.` |

### 6.4 Budget Cap Hit Mid-Turn

| Failure Mode | Trigger | Immediate Action | Recovery | User-Visible Output |
|-------------|---------|-----------------|----------|-------------------|
| Cost approaches cap (90%) | `_check_budget()` → cost ≥ 0.9 × cap | WARNING emitted; debate continues for 1 more turn | Allows current turn to finish cleanly | `[WARN] Session cost at 90% of budget cap ($X.XX / $Y.YY).` |
| Cost exceeds cap | `_check_budget()` → cost > cap | IN_PROGRESS → EVALUATION transition forced | Father evaluates on partial transcript (even if < 20 turns) | `[WARN] Budget cap exceeded. Forcing early evaluation.` |
| Budget cap set to 0 | `setup.json` has `max_session_cost_usd: 0` | `ConfigValidationError` at startup | System exits before debate starts | `[ERROR] max_session_cost_usd must be > 0.` |
| Pricing file missing model | `compute()` finds model not in `pricing.json` | `KeyError` caught; model cost treated as $0 | Debate continues; cost report flags model as "UNKNOWN PRICE" | `[WARN] No pricing entry for model X. Cost may be understated.` |

### 6.5 Configuration & Startup Failures

| Failure Mode | Trigger | Immediate Action | Recovery | User-Visible Output |
|-------------|---------|-----------------|----------|-------------------|
| Config file missing | `ConfigLoader.load_all()` cannot find file | `FileNotFoundError` raised | No recovery; system exits code 1 | `[ERROR] config/setup.json not found. Run 'make setup'.` |
| Schema version mismatch | `schema_version` field does not match expected | `ConfigVersionError` raised | No recovery; system exits code 1 | `[ERROR] setup.json schema_version mismatch. Expected 1.0.` |
| `ANTHROPIC_API_KEY` missing | Not in `.env` at startup | `ValueError` raised | No recovery; system exits code 1 | `[ERROR] ANTHROPIC_API_KEY is not set. Add it to .env.` |
| Topic string empty | `--topic ""` passed to CLI | `argparse` error | No recovery; exits code 2 | `error: --topic must be a non-empty string.` |

---

## 7. Granular CLI / UI Flow

The following is the exact sequence of terminal output a user observes for a
successful 20-turn debate. All output goes to `stdout`; errors go to `stderr`.

### 7.1 Startup Phase

```
[INFO]  Loading config from config/setup.json ...
[INFO]  Config loaded. Schema version: 1.0
[INFO]  Agents: father=claude-sonnet-4-6 | pro_son=claude-haiku-4-5 | con_son=claude-haiku-4-5
[INFO]  Rate limits: claude-sonnet-4-6 → 50 RPM / 40000 TPM
[INFO]  Budget cap: $2.00
[INFO]  Watchdog timeout: 30s | max retries: 1
[INFO]  Initializing Web Search tool ...
[INFO]  Web Search tool ready (30 RPM limit)
```

### 7.2 Debate Opening

```
╔══════════════════════════════════════════════════════════════╗
║              AI DEBATE SYSTEM — NajAmjad Group               ║
╚══════════════════════════════════════════════════════════════╝

[DEBATE STARTING]
  Topic    : <topic string from --topic flag>
  Min turns: 10 per side (20 total)
  Status   : INITIALIZATION → IN_PROGRESS

[FATHER] Opening statement dispatched to Pro Son.
```

### 7.3 Per-Turn Output (repeated for each turn)

```
──────────────────────────────────────────────────────────────
[TURN 1 / 20+]  Father → Pro Son
[SEARCH]  Pro Son querying: "<search query string>"
[SEARCH]  Result: <first 80 chars of top snippet> ...
[PRO SON] Argument received (342 tokens | 1 source)
[FATHER]  Validated ✓ | Schema OK | Position: PRO ✓

[TURN 2 / 20+]  Father → Con Son
[SEARCH]  Con Son querying: "<search query string>"
[SEARCH]  Result: <first 80 chars of top snippet> ...
[CON SON] Argument received (298 tokens | 2 sources)
[FATHER]  Validated ✓ | Schema OK | Position: CON ✓
```

### 7.4 Watchdog Event (conditional)

```
[WATCHDOG] ⚠  Timeout on turn N (attempt 1/1). Retrying call ...
[WATCHDOG]    Retry succeeded. Continuing.
```

### 7.5 Budget Warning (conditional)

```
[BUDGET]  ⚠  Session cost at 90% of cap: $1.80 / $2.00
[BUDGET]  Allowing 1 additional turn before forced evaluation.
```

### 7.6 Evaluation Phase

```
──────────────────────────────────────────────────────────────
[EVALUATION]  Turn count: 22 | Budget used: $1.65 / $2.00
[EVALUATION]  Father scoring transcript using persuasiveness rubric ...
[EVALUATION]  Rubric scores:
              Pro Son — Clarity: 8/10 | Evidence: 9/10 | Logic: 7/10 → 24/30
              Con Son — Clarity: 6/10 | Evidence: 7/10 | Logic: 8/10 → 21/30
[EVALUATION]  Winner selected: pro_son
```

### 7.7 Verdict Output

```
╔══════════════════════════════════════════════════════════════╗
║                         VERDICT                              ║
╠══════════════════════════════════════════════════════════════╣
║  Winner  : PRO SON                                           ║
║  Draw    : false                                             ║
║  Turns   : 22                                                ║
║  Reasoning: Pro Son consistently supported claims with        ║
║             current evidence and maintained clear logical     ║
║             structure throughout all 11 turns.               ║
╚══════════════════════════════════════════════════════════════╝
```

### 7.8 Cost Report Output

```
╔══════════════════════════════════════════════════════════════╗
║                      COST REPORT                             ║
╠══════════════════════════════════════════════════════════════╣
║  Agent       Model                  Tokens  In  Out   Cost   ║
║  ─────────── ────────────────────── ──────  ─── ───── ────── ║
║  father      claude-sonnet-4-6      12,400  9.2K 3.2K $0.043 ║
║  pro_son     claude-haiku-4-5       8,200   6.1K 2.1K $0.009 ║
║  con_son     claude-haiku-4-5       7,900   5.9K 2.0K $0.009 ║
║  ─────────── ────────────────────── ──────  ─── ───── ────── ║
║  TOTAL                              28,500              $0.061 ║
║  Budget utilisation: 3.1% of $2.00                           ║
╚══════════════════════════════════════════════════════════════╝
[INFO]  Debate state saved to logs/debate_<timestamp>.json
[INFO]  Session complete. Exit code: 0
```

### 7.9 Fatal Error Output (stderr)

```
[ERROR]  WatchdogError: Fatal timeout on turn 7 after 1 retry.
[ERROR]  Partial debate state saved to logs/debate_<timestamp>_partial.json
[INFO]   Exit code: 1
```

---

## 8. Non-Functional Requirements

### 8.1 Performance & Reliability

| ID | Requirement |
|----|-------------|
| NF-01 | Each LLM call must complete within 30 seconds; Watchdog kills and retries after timeout. |
| NF-02 | System must complete a 20-turn debate end-to-end without manual intervention. |
| NF-03 | Log rotation must maintain no more than 20 log files of 500 lines each (FIFO eviction). |

### 8.2 Code Quality (Golden Rules)

| Rule | Threshold |
|------|-----------|
| Max lines per file | 150 |
| Ruff linting violations | 0 |
| Pytest coverage | > 85 % |
| Development methodology | TDD (tests written before implementation) |

### 8.3 Security

- API keys loaded exclusively from environment variables.
- No secrets in source files or logs.
- Web Search queries sanitized before dispatch (max 200 chars, stripped whitespace).

---

## 9. Persuasiveness Rubric

The Father agent must evaluate each debater's total performance across the full
transcript using exactly three dimensions, each scored from 1 to 10. The rubric
is embedded in the Father's evaluation prompt verbatim to prevent drift.

### 9.1 Dimension Definitions

#### Dimension 1 — Clarity (1–10)

Measures how clearly and concisely the debater expressed each argument.

| Score | Descriptor |
|-------|-----------|
| 9–10 | Arguments are immediately understandable; structured with clear premise → reasoning → conclusion; no unnecessary filler. |
| 7–8 | Mostly clear; occasional verbose or ambiguous phrasing. |
| 5–6 | Understandable but frequently convoluted; key points buried in prose. |
| 3–4 | Difficult to follow; arguments require significant interpretation. |
| 1–2 | Incomprehensible or entirely off-topic. |

#### Dimension 2 — Evidence Quality (1–10)

Measures how well the debater supported claims with sourced, relevant, and recent evidence.

| Score | Descriptor |
|-------|-----------|
| 9–10 | Every major claim backed by a specific, credible, recent source from Web Search; sources directly support the argument. |
| 7–8 | Most claims sourced; one or two unsupported assertions. |
| 5–6 | Mix of sourced and unsourced claims; some sources tangential. |
| 3–4 | Mostly unsourced or sources are clearly irrelevant. |
| 1–2 | No sources provided or all sources fabricated. |

#### Dimension 3 — Logical Consistency (1–10)

Measures whether arguments follow logically, avoid fallacies, and build a coherent case
across all turns.

| Score | Descriptor |
|-------|-----------|
| 9–10 | Arguments are internally consistent across all turns; no contradictions; reasoning is deductively or inductively sound. |
| 7–8 | Mostly consistent; minor internal tension between turns. |
| 5–6 | Noticeable contradictions or logical leaps; some fallacies. |
| 3–4 | Frequent contradictions; argument structure collapses across turns. |
| 1–2 | No discernible logical structure. |

### 9.2 Scoring Formula

```
total_score = clarity + evidence_quality + logical_consistency   (max 30)
winner = agent with higher total_score
```

If scores are **arithmetically equal** after all three dimensions, the Father must
apply a fourth tiebreaker: **turn-by-turn persuasive momentum** — the agent whose
scores were improving across the final 4 turns wins. Draws are not permitted under
any scoring outcome.

### 9.3 Rubric Prompt Template

The following template is embedded verbatim in `FatherAgent.evaluate()`. No paraphrasing.

```
You are the debate judge. Score each debater on:
1. Clarity (1-10): How clearly were arguments expressed?
2. Evidence Quality (1-10): How well were claims supported by cited sources?
3. Logical Consistency (1-10): Were arguments internally consistent across all turns?

Transcript:
{transcript}

Return ONLY valid JSON matching this schema:
{
  "scores": {
    "pro_son": {"clarity": N, "evidence": N, "logic": N, "total": N},
    "con_son":  {"clarity": N, "evidence": N, "logic": N, "total": N}
  },
  "winner": "pro_son" | "con_son",
  "draw": false,
  "reasoning": "<min 50 chars>"
}
```

---

## 10. Costs & Pricing

### 10.1 Token Tracking

- Every API call records `prompt_tokens`, `completion_tokens`, and `total_tokens`
  against the calling agent and model name.
- The `CostReporter` reads per-model pricing from `config/pricing.json`
  (USD per 1 000 tokens, input and output rates separately).
- A cost summary is printed at debate end: per-agent breakdown and total session cost.

### 10.2 Budget Controls

- `config/setup.json` exposes a `max_session_cost_usd` parameter.
- At 90% of cap: WARNING emitted; debate continues for one more turn.
- At 100%+ of cap: evaluation forced; cost report generated immediately.

### 10.3 Supported Models (initial)

| Model Alias | Provider | Rate |
|-------------|----------|------|
| `claude-sonnet-4-6` | Anthropic | per `pricing.json` |
| `claude-haiku-4-5` | Anthropic | per `pricing.json` |

---

## 11. Extensibility

### 11.1 Plugin Architecture

New capabilities are registered by:
1. Implementing the `AgentSkill` abstract base class.
2. Placing the module in `src/skills/`.
3. Declaring the skill in `config/setup.json` under `enabled_skills`.

### 11.2 Agent Extensibility

Additional debater agents can be added by subclassing `BaseDebaterAgent` and
registering the new role in `config/setup.json`. The Father's routing table is
built dynamically from the config.

### 11.3 Versioning

All config schemas carry a `schema_version` field validated at startup.

---

## 12. Configuration Portability

- All environment-specific values reside in `.env`.
- Path values in `setup.json` use relative paths resolved from project root.
- Runnable on any POSIX system with Python 3.11+ and `uv` without source changes.
- `uv sync` installs all dependencies and scaffolds config from templates.

---

## 13. Acceptance Criteria & KPIs

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
| AC-09 | No hardcoded secrets or values | 0 occurrences (CI grep check) |
| AC-10 | Cost report generated at debate end | Present in every run output |

---

## 14. Out of Scope (v1.0)

- Real-time streaming of agent responses to the UI.
- Multi-topic / bracket-style tournament mode.
- Fine-tuning or RLHF on debate outcomes.
- Persistent storage beyond a single session's JSON state file.

# Execution Checklist
## AI Debate System — Assignment 2
**Project:** AI Orchestration Course — Group NajAmjad
**Version:** 1.0.0
**Date:** 2026-05-25
**Status:** Draft — Pending Approval

---

## Golden Rules (apply to every task below)

- [ ] Max **150 lines** per source file — split if exceeded.
- [ ] **0 ruff violations** — run `uv run ruff check .` before every commit.
- [ ] **> 85 % test coverage** — run `uv run pytest --cov=src` before every commit.
- [ ] **TDD workflow** — write the test first, then the implementation.
- [ ] **No hardcoded values** — all config via `setup.json`, `rate_limits.json`, or `.env`.
- [ ] **No direct agent-to-agent messages** — all routing through Father.

---

## Phase 1: Infrastructure & Configuration

### 1.1 Project Scaffold

- [ ] `P1-01` Initialize `uv` project: `uv init` and confirm `pyproject.toml` created.
- [ ] `P1-02` Add runtime dependencies: `anthropic`, `jsonschema`, `python-dotenv`, `requests`.
- [ ] `P1-03` Add dev dependencies: `ruff`, `pytest`, `pytest-cov`.
- [ ] `P1-04` Configure `ruff` in `pyproject.toml` (line-length 88, select E/W/F/I rules).
- [ ] `P1-05` Configure `pytest` in `pyproject.toml` (testpaths, cov source, cov fail-under 85).
- [ ] `P1-06` Create `.gitignore` (`.env`, `logs/`, `__pycache__`, `.venv`, `*.pyc`).
- [ ] `P1-07` Create `.env-example` with `ANTHROPIC_API_KEY` and `SEARCH_API_KEY` placeholders.
- [ ] `P1-08` Create `config/` directory with empty `setup.json`, `rate_limits.json`, `pricing.json`.
- [ ] `P1-09` Populate `config/setup.json` with full schema (see PLAN.md §5.2).
- [ ] `P1-10` Populate `config/rate_limits.json` with per-model RPM/TPM values.
- [ ] `P1-11` Populate `config/pricing.json` with USD/1K token rates for each model.
- [ ] `P1-12` Create `src/schemas/debate_message.json` (JSON Schema from PRD §4.2).
- [ ] `P1-13` Create `src/schemas/verdict.json` (JSON Schema from PRD §4.3).

### 1.2 ConfigLoader

- [ ] `P1-14` **[TEST FIRST]** Write `tests/unit/test_config_loader.py`:
  - Loads all three config files successfully.
  - Raises `ConfigVersionError` on mismatched `schema_version`.
  - Raises `FileNotFoundError` if a config file is missing.
- [ ] `P1-15` Implement `src/infrastructure/config_loader.py` (`ConfigLoader` class, ≤150 lines).
- [ ] `P1-16` Verify: `uv run ruff check src/infrastructure/config_loader.py` → 0 violations.
- [ ] `P1-17` Verify: tests pass and coverage ≥ 85 % for this module.

### 1.3 LoggerManager

- [ ] `P1-18` **[TEST FIRST]** Write `tests/unit/test_logger_manager.py`:
  - Writes a log entry and confirms file creation in `logs/`.
  - Rotates file after 500 lines (FIFO eviction of oldest when > 20 files).
  - Log format matches `{ISO-timestamp} | {level} | {component} | {message}`.
- [ ] `P1-19` Implement `src/infrastructure/logger_manager.py` (`LoggerManager` class, ≤150 lines).
- [ ] `P1-20` Verify ruff + coverage.

### 1.4 API Gatekeeper

- [ ] `P1-21` **[TEST FIRST]** Write `tests/unit/test_gatekeeper.py`:
  - Dispatches a mocked API request successfully.
  - Queues excess requests when RPM limit is hit.
  - `get_usage(agent_id)` returns correct cumulative token counts.
  - Queue rejects new items when depth > 50.
- [ ] `P1-22` Implement `src/infrastructure/gatekeeper.py` (`Gatekeeper` class, ≤150 lines).
- [ ] `P1-23` Verify ruff + coverage.

### 1.5 Watchdog

- [ ] `P1-24` **[TEST FIRST]** Write `tests/unit/test_watchdog.py`:
  - Returns result when function completes within timeout.
  - Retries once on timeout; succeeds on retry.
  - Raises `WatchdogError` on two consecutive timeouts.
  - Logs a WARNING on each timeout event.
- [ ] `P1-25` Implement `src/infrastructure/watchdog.py` (`Watchdog` class, ≤150 lines).
- [ ] `P1-26` Verify ruff + coverage.

---

## Phase 2: Agent SDK & Tools

### 2.1 Base Skill Interface

- [ ] `P2-01` **[TEST FIRST]** Write `tests/unit/test_base_skill.py`:
  - Confirms `AgentSkill` is abstract and cannot be instantiated directly.
  - Subclass with `execute()` implemented is instantiable.
- [ ] `P2-02` Implement `src/skills/base_skill.py` (`AgentSkill` ABC, ≤50 lines).
- [ ] `P2-03` Verify ruff + coverage.

### 2.2 Web Search Tool

- [ ] `P2-04` **[TEST FIRST]** Write `tests/unit/test_web_search_tool.py`:
  - `execute(query)` returns `SkillResult` with non-empty `snippets` list.
  - Query is sanitized (strips leading/trailing whitespace, max 200 chars).
  - Raises `SkillError` on HTTP error response (mocked).
  - API key loaded from environment, not hardcoded.
- [ ] `P2-05` Implement `src/skills/web_search_tool.py` (`WebSearchTool` class, ≤150 lines).
- [ ] `P2-06` Write `tests/integration/test_web_search_integration.py` (live API, marked slow).
- [ ] `P2-07` Verify ruff + coverage.

### 2.3 Base Agent

- [ ] `P2-08` **[TEST FIRST]** Write `tests/unit/test_base_agent.py`:
  - Confirms `BaseAgent` is abstract.
  - `parse_response()` raises `MessageParseError` on invalid JSON.
  - `parse_response()` raises `MessageParseError` on schema violation.
  - `call_api()` routes through `Gatekeeper`.
- [ ] `P2-09` Implement `src/agents/base_agent.py` (`BaseAgent` ABC, ≤150 lines).
- [ ] `P2-10` Verify ruff + coverage.

### 2.4 Pro Son Agent

- [ ] `P2-11` **[TEST FIRST]** Write `tests/unit/test_pro_son_agent.py`:
  - `generate_argument()` returns a valid `DebateMessage`.
  - Position enforcer rejects a "con" response and triggers retry.
  - `sources` field is non-empty in every returned message.
- [ ] `P2-12` Implement `src/agents/pro_son_agent.py` (`ProSonAgent`, ≤150 lines).
- [ ] `P2-13` Verify ruff + coverage.

### 2.5 Con Son Agent

- [ ] `P2-14` **[TEST FIRST]** Write `tests/unit/test_con_son_agent.py`:
  - Mirror of Pro Son tests with opposite position constraint.
- [ ] `P2-15` Implement `src/agents/con_son_agent.py` (`ConSonAgent`, ≤150 lines).
- [ ] `P2-16` Verify ruff + coverage.

### 2.6 Father Agent

- [ ] `P2-17` **[TEST FIRST]** Write `tests/unit/test_father_agent.py`:
  - `open_debate()` returns a valid `DebateMessage` with `sender: "father"`.
  - `route()` correctly forwards messages based on `recipient` field.
  - `_validate_message()` rejects messages missing required fields.
  - `evaluate()` raises `NotEnoughTurnsError` if turn count < 20.
  - `evaluate()` returns a `Verdict` with `draw: false`.
- [ ] `P2-18` Implement `src/agents/father_agent.py` (`FatherAgent`, ≤150 lines).
- [ ] `P2-19` Verify ruff + coverage.

---

## Phase 3: The Debate Engine

### 3.1 State Manager

- [ ] `P3-01` **[TEST FIRST]** Write `tests/unit/test_state_manager.py`:
  - `record_message()` appends to transcript and increments turn count.
  - `to_json()` produces valid JSON that round-trips via `from_json()`.
  - State survives serialization of token counts and timestamps.
- [ ] `P3-02` Implement `src/engine/state_manager.py` (`StateManager`, ≤150 lines).
- [ ] `P3-03` Verify ruff + coverage.

### 3.2 Debate Engine

- [ ] `P3-04` **[TEST FIRST]** Write `tests/unit/test_debate_engine.py`:
  - `start()` orchestrates a full turn loop with mocked agents.
  - Turn loop stops only after 20 turns minimum.
  - Watchdog timeout during a turn does not corrupt state.
  - Budget cap triggers early verdict phase when exceeded.
  - Final output is a `Verdict` with `draw: false`.
- [ ] `P3-05` Implement `src/engine/debate_engine.py` (`DebateEngine`, ≤150 lines).
- [ ] `P3-06` Verify ruff + coverage.

### 3.3 Integration Test: Full Debate

- [ ] `P3-07` Write `tests/integration/test_full_debate.py` (marked slow, requires API keys):
  - Runs a complete debate on a fixed test topic.
  - Asserts transcript has ≥ 20 messages.
  - Asserts every message is valid against JSON schema.
  - Asserts verdict `draw == false`.
  - Asserts web search was invoked at least once per 3 turns per side.
- [ ] `P3-08` Run integration test and confirm passage. Fix any issues found.

### 3.4 Cost Reporter

- [ ] `P3-09` **[TEST FIRST]** Write `tests/unit/test_cost_reporter.py`:
  - `compute()` returns correct USD totals from mock usage stats.
  - Per-agent breakdown sums to session total.
  - Pricing read from `config/pricing.json`, not hardcoded.
- [ ] `P3-10` Implement `src/infrastructure/cost_reporter.py` (`CostReporter`, ≤150 lines).
- [ ] `P3-11` Verify ruff + coverage.

---

## Phase 4: UI / CLI & Cost Reporting

### 4.1 Debate CLI

- [ ] `P4-01` **[TEST FIRST]** Write `tests/unit/test_debate_cli.py`:
  - `--topic` argument is required; missing arg exits with code 2.
  - Successful run exits with code 0 and prints verdict to stdout.
  - `--dry-run` flag validates config without calling API.
- [ ] `P4-02` Implement `src/ui/debate_cli.py` (argparse entry point, ≤150 lines).
  - Accepts `--topic "..."`, `--config path`, `--dry-run` flags.
  - Calls `DebateEngine.start()` and prints formatted verdict + cost report.
- [ ] `P4-03` Register CLI entry point in `pyproject.toml` (`[project.scripts]`).
- [ ] `P4-04` Verify ruff + coverage.

### 4.2 Cost Report Output

- [ ] `P4-05` Implement `CostReporter.print_report()` with human-readable table output.
- [ ] `P4-06` Confirm report includes: per-agent token counts, per-agent cost USD,
  session total cost USD, and budget-cap utilisation %.
- [ ] `P4-07` Write test asserting report output contains all required fields.

### 4.3 Final Validation

- [ ] `P4-08` Run full ruff check on entire repo: `uv run ruff check .` → **0 violations**.
- [ ] `P4-09` Run full test suite: `uv run pytest --cov=src --cov-fail-under=85` → **passes**.
- [ ] `P4-10` Run `grep -r "sk-ant\|api_key\s*=" src/` → **0 hardcoded secrets**.
- [ ] `P4-11` Verify no source file exceeds 150 lines: `awk 'END{if(NR>150)exit 1}' src/**/*.py`.
- [ ] `P4-12` Run end-to-end integration test with a real topic and confirm clean output.
- [ ] `P4-13` Commit final working state: `git commit -m "feat: complete AI debate system"`.

---

## Dependency Graph (Phase ordering)

```
Phase 1 (Infrastructure) ──► Phase 2 (Agent SDK)
                                    │
                                    ▼
                             Phase 3 (Engine)
                                    │
                                    ▼
                             Phase 4 (CLI/UI)
```

Within Phase 1: `ConfigLoader` → `LoggerManager` → `Gatekeeper` → `Watchdog`
Within Phase 2: `BaseSkill` → `WebSearchTool` → `BaseAgent` → Sons → `FatherAgent`
Within Phase 3: `StateManager` → `DebateEngine` → Integration Tests → `CostReporter`

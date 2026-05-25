# Execution Checklist
## AI Debate System — Assignment 2
**Project:** AI Orchestration Course — Group NajAmjad
**Version:** 2.0.0
**Date:** 2026-05-25
**Status:** Draft — Pending Approval

> **Golden Rules** — every task below must satisfy all five:
> Max 150 lines per source file · 0 ruff violations · >85% test coverage · TDD (test first) · No hardcoded values · No direct agent-to-agent messages

---

## Phase 0 — Project Scaffold & Repository Setup

### 0.1 uv & Python Environment

- [ ] Install `uv` globally via the official installer script.
- [ ] Verify `uv --version` outputs 0.4.0 or higher.
- [ ] Run `uv init` in the project root to generate `pyproject.toml`.
- [ ] Confirm `pyproject.toml` was created and is syntactically valid TOML.
- [ ] Set `name = "ai-debate-system"` in `pyproject.toml`.
- [ ] Set `version = "0.1.0"` and `requires-python = ">=3.11"` in `pyproject.toml`.
- [ ] Set `description` and `authors = [{name = "NajAmjad"}]` in `pyproject.toml`.
- [ ] Add `anthropic`, `jsonschema`, `python-dotenv`, `requests` to `[project.dependencies]`.
- [ ] Add `[project.optional-dependencies]` dev section with `ruff`, `pytest`, `pytest-cov`.
- [ ] Add `[tool.ruff]` with `line-length = 88` and `[tool.ruff.lint]` with `select = ["E","W","F","I"]`.
- [ ] Add `[tool.pytest.ini_options]` with `testpaths`, `addopts = "--cov=src --cov-fail-under=85"`.
- [ ] Run `uv sync` and confirm `.venv/` is created.
- [ ] Run `uv run python --version` — confirm Python 3.11+.
- [ ] Run `uv run ruff --version` — confirm ruff is available.
- [ ] Run `uv run pytest --version` — confirm pytest is available.
- [ ] Run `uv run python -c "import anthropic; import jsonschema"` — confirm imports work.

### 0.2 Directory Structure & __init__ Files

- [ ] Create directories: `src/`, `src/agents/`, `src/engine/`, `src/infrastructure/`, `src/schemas/`, `src/skills/`, `src/ui/`.
- [ ] Create directories: `tests/`, `tests/unit/`, `tests/integration/`, `config/`, `examples/`.
- [ ] Create `src/__init__.py`, `src/agents/__init__.py`, `src/engine/__init__.py` as empty files.
- [ ] Create `src/infrastructure/__init__.py`, `src/skills/__init__.py`, `src/ui/__init__.py` as empty files.
- [ ] Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` as empty files.
- [ ] Verify all `__init__.py` files are empty (0 bytes).

### 0.3 .gitignore

- [ ] Create `.gitignore` in project root.
- [ ] Add `.env`, `logs/`, `__pycache__/`, `.venv/`, `*.pyc`, `*.pyo` to `.gitignore`.
- [ ] Add `.coverage`, `htmlcov/`, `.pytest_cache/`, `dist/`, `*.egg-info/` to `.gitignore`.
- [ ] Add `.idea/`, `.vscode/` to `.gitignore`.
- [ ] Verify `git status` does not show `.venv/` or `logs/` as untracked.

### 0.4 .env-example

- [ ] Create `.env-example` with comment block `# Anthropic Claude API`.
- [ ] Add `ANTHROPIC_API_KEY=your_anthropic_key_here` to `.env-example`.
- [ ] Add `SEARCH_API_KEY=your_search_key_here` to `.env-example`.
- [ ] Add `SEARCH_BASE_URL=https://api.example.com/search` to `.env-example`.
- [ ] Copy `.env-example` to local `.env` and fill real API keys (do NOT commit `.env`).
- [ ] Confirm `.env` is listed in `.gitignore` and will not be staged.

### 0.5 config/setup.json

- [ ] Create `config/setup.json` with `schema_version`, `debate`, `agents`, `watchdog`, `logging`, `enabled_skills` top-level keys.
- [ ] Set `debate.min_turns_per_side = 10` and `debate.max_session_cost_usd = 2.00`.
- [ ] Set agent models: `father = "claude-sonnet-4-6"`, `pro_son = con_son = "claude-haiku-4-5"`.
- [ ] Set `watchdog.timeout_seconds = 30` and `watchdog.max_retries = 1`.
- [ ] Set `logging.log_dir = "logs/"`, `logging.max_files = 20`, `logging.max_lines_per_file = 500`.
- [ ] Set `enabled_skills = ["web_search"]`.
- [ ] Validate `setup.json` is valid JSON: `python -m json.tool config/setup.json`.

### 0.6 config/rate_limits.json

- [ ] Create `config/rate_limits.json` with `schema_version` field.
- [ ] Add `models.claude-sonnet-4-6: {rpm: 50, tpm: 40000}` and `models.claude-haiku-4-5: {rpm: 100, tpm: 100000}`.
- [ ] Add `web_search: {rpm: 30}`.
- [ ] Validate `rate_limits.json` is valid JSON.

### 0.7 config/pricing.json

- [ ] Create `config/pricing.json` with `schema_version` field.
- [ ] Add `models.claude-sonnet-4-6` and `models.claude-haiku-4-5` entries with `input_per_1k` and `output_per_1k` USD values.
- [ ] Validate `pricing.json` is valid JSON.

### 0.8 JSON Schema Files

- [ ] Create `src/schemas/debate_message.json` with `$schema`, `type: object`, and `required` array.
- [ ] Add all 8 properties: `message_id` (uuid), `sender` (enum), `recipient` (enum), `turn` (int ≥1), `content` (string), `sources` (array), `token_count` (int ≥0), `timestamp` (date-time).
- [ ] Validate `debate_message.json` with `python -c "import jsonschema, json; jsonschema.Draft7Validator(json.load(open('src/schemas/debate_message.json')))"`.
- [ ] Create `src/schemas/verdict.json` with `required` array.
- [ ] Add all 6 properties: `verdict_id` (uuid), `winner` (enum: pro_son|con_son), `draw` (const: false), `reasoning` (string ≥50), `turn_count` (int ≥20), `timestamp` (date-time).
- [ ] Validate `verdict.json` with `python -c "import jsonschema, json; jsonschema.Draft7Validator(json.load(open('src/schemas/verdict.json')))"`.

### 0.9 Test Configuration

- [ ] Create `tests/conftest.py` with `slow` custom mark definition.
- [ ] Register `slow` marker in `pyproject.toml` under `[tool.pytest.ini_options]`.
- [ ] Create `tests/integration/conftest.py` with `pytestmark = pytest.mark.slow`.

### 0.10 Initial README & First Commit

- [ ] Create `README.md` with title, group name, one-paragraph overview, and placeholder sections.
- [ ] Stage all Phase 0 files: `git add .`.
- [ ] Git commit: `chore: scaffold project structure and configuration files`.

---

## Phase 1 — Infrastructure Layer

### 1.1 ConfigLoader

- [ ] Create `src/infrastructure/config_loader.py`.
- [ ] Add imports: `import json`, `import os`, `from pathlib import Path`, `from typing import Any`.
- [ ] Define `ConfigVersionError(Exception)` class in `config_loader.py`.
- [ ] Create `tests/unit/test_config_loader.py`.
- [ ] Add imports: `import pytest`, `from src.infrastructure.config_loader import ConfigLoader, ConfigVersionError`.
- [ ] Define `tmp_config_dir` fixture: temp dir pre-populated with valid JSON config files.
- [ ] Define `valid_setup_data` fixture: minimal valid setup dict.
- [ ] Write failing test: `test_config_loader_init_sets_config_dir` — asserts `loader.config_dir` is set.
- [ ] Implement `ConfigLoader.__init__(self, config_dir: str)` with Google-style docstring.
- [ ] Run `uv run pytest tests/unit/test_config_loader.py::test_config_loader_init_sets_config_dir` — confirm pass.
- [ ] Write failing test: `test_load_setup_returns_dict` — happy path, valid `setup.json`.
- [ ] Implement `ConfigLoader.load_setup(self) -> dict`.
- [ ] Write failing test: `test_load_setup_raises_file_not_found` — `setup.json` absent.
- [ ] Implement `FileNotFoundError` handling in `load_setup`.
- [ ] Write failing test: `test_load_setup_raises_on_invalid_json` — file contains malformed JSON.
- [ ] Implement `json.JSONDecodeError` handling in `load_setup`.
- [ ] Run `uv run pytest` on all `load_setup` tests — confirm all pass.
- [ ] Write failing test: `test_load_rate_limits_returns_dict` — happy path.
- [ ] Implement `ConfigLoader.load_rate_limits(self) -> dict`.
- [ ] Write failing test: `test_load_rate_limits_raises_file_not_found`.
- [ ] Implement `FileNotFoundError` handling in `load_rate_limits`.
- [ ] Run `uv run pytest` on all `load_rate_limits` tests — confirm all pass.
- [ ] Write failing test: `test_load_pricing_returns_dict` — happy path.
- [ ] Implement `ConfigLoader.load_pricing(self) -> dict`.
- [ ] Write failing test: `test_load_pricing_raises_file_not_found`.
- [ ] Implement `FileNotFoundError` handling in `load_pricing`.
- [ ] Run `uv run pytest` on all `load_pricing` tests — confirm all pass.
- [ ] Write failing test: `test_validate_schema_version_passes_on_matching_version`.
- [ ] Write failing test: `test_validate_schema_version_raises_config_version_error_on_mismatch`.
- [ ] Implement `ConfigLoader._validate_schema_version(self, data: dict, expected: str) -> None`.
- [ ] Run `uv run pytest` on all `_validate_schema_version` tests — confirm all pass.
- [ ] Write failing test: `test_load_all_populates_setup_rate_limits_and_pricing`.
- [ ] Implement `ConfigLoader.load_all(self) -> None` calling all three loaders.
- [ ] Write failing test: `test_load_all_raises_config_version_error_on_bad_schema_version`.
- [ ] Implement version validation inside `load_all`.
- [ ] Run `uv run pytest` on all `load_all` tests — confirm all pass.
- [ ] Run `uv run ruff check src/infrastructure/config_loader.py` — confirm 0 violations.
- [ ] Run `wc -l src/infrastructure/config_loader.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement ConfigLoader with schema version validation`.

### 1.2 LoggerManager

- [ ] Create `src/infrastructure/logger_manager.py`.
- [ ] Add imports: `import logging`, `from datetime import datetime, timezone`, `from pathlib import Path`, `import os`.
- [ ] Create `tests/unit/test_logger_manager.py`.
- [ ] Add imports: `import pytest`, `from pathlib import Path`, `from src.infrastructure.logger_manager import LoggerManager`.
- [ ] Define `tmp_log_dir` fixture using `tmp_path` pytest built-in.
- [ ] Define `logger` fixture: `LoggerManager(tmp_log_dir, max_files=5, max_lines=10)`.
- [ ] Write failing test: `test_logger_manager_init_creates_log_dir` — directory exists after init.
- [ ] Implement `LoggerManager.__init__(self, log_dir: str, max_files: int, max_lines: int)` with Google-style docstring.
- [ ] Run `uv run pytest tests/unit/test_logger_manager.py::test_logger_manager_init_creates_log_dir` — confirm pass.
- [ ] Write failing test: `test_write_creates_log_file` — first `write()` creates a `.log` file.
- [ ] Implement `LoggerManager.write(self, level: str, component: str, message: str) -> None`.
- [ ] Write failing test: `test_write_format_matches_spec` — line format is `ISO | LEVEL | COMPONENT | MESSAGE`.
- [ ] Implement log-line format enforcement in `write`.
- [ ] Write failing test: `test_write_rejects_unknown_level` — invalid level string raises `ValueError`.
- [ ] Implement level validation (DEBUG/INFO/WARNING/ERROR) in `write`.
- [ ] Run `uv run pytest` on all `write` tests — confirm all pass.
- [ ] Write failing test: `test_get_current_file_returns_existing_path`.
- [ ] Implement `LoggerManager._get_current_file(self) -> Path`.
- [ ] Write failing test: `test_get_current_file_opens_new_file_after_line_limit` — 10 lines written (fixture limit), next write goes to new file.
- [ ] Implement line-count check and new-file creation in `_get_current_file`.
- [ ] Run `uv run pytest` on all `_get_current_file` tests — confirm all pass.
- [ ] Write failing test: `test_rotate_deletes_oldest_file_when_max_files_exceeded` — 5-file fixture limit, sixth file triggers eviction.
- [ ] Implement `LoggerManager._rotate(self) -> None` with FIFO eviction logic.
- [ ] Write failing test: `test_rotate_does_not_delete_when_below_max_files_limit`.
- [ ] Implement below-limit guard in `_rotate`.
- [ ] Run `uv run pytest` on all `_rotate` tests — confirm all pass.
- [ ] Run `uv run ruff check src/infrastructure/logger_manager.py` — confirm 0 violations.
- [ ] Run `wc -l src/infrastructure/logger_manager.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement LoggerManager with FIFO rotation`.

### 1.3 Gatekeeper

- [ ] Create `src/infrastructure/gatekeeper.py`.
- [ ] Add imports: `import threading`, `from collections import deque`, `import time`, `from dataclasses import dataclass, field`, `from typing import Any`.
- [ ] Define `QueueFullError(Exception)` in `gatekeeper.py`.
- [ ] Define `APIRequest` dataclass (agent_id, model, payload) in `gatekeeper.py`.
- [ ] Define `APIResponse` dataclass (content, prompt_tokens, completion_tokens) in `gatekeeper.py`.
- [ ] Define `UsageStats` dataclass (prompt_tokens, completion_tokens, total_tokens) in `gatekeeper.py`.
- [ ] Create `tests/unit/test_gatekeeper.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import patch, MagicMock`.
- [ ] Add `from src.infrastructure.gatekeeper import Gatekeeper, QueueFullError, APIRequest, APIResponse, UsageStats`.
- [ ] Define `mock_rate_limits` fixture with low rpm/tpm for fast testing.
- [ ] Define `gatekeeper` fixture initialised with `mock_rate_limits`.
- [ ] Define `sample_request` fixture as a valid `APIRequest` object.
- [ ] Write failing test: `test_gatekeeper_init_creates_empty_queue`.
- [ ] Write failing test: `test_gatekeeper_init_stores_rate_limits`.
- [ ] Implement `Gatekeeper.__init__(self, rate_limits: dict)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_dispatch_returns_api_response` — mocked HTTP, happy path.
- [ ] Implement `Gatekeeper.dispatch(self, request: APIRequest) -> APIResponse`.
- [ ] Write failing test: `test_dispatch_records_token_usage_for_agent`.
- [ ] Implement token-usage recording in `dispatch`.
- [ ] Write failing test: `test_dispatch_queues_request_when_rate_limit_enforced`.
- [ ] Implement queue insertion path in `dispatch`.
- [ ] Run `uv run pytest` on all `dispatch` tests — confirm all pass.
- [ ] Write failing test: `test_enforce_limits_blocks_when_rpm_bucket_depleted`.
- [ ] Implement `Gatekeeper._enforce_limits(self, model: str) -> None` with token-bucket logic.
- [ ] Write failing test: `test_enforce_limits_allows_call_within_rpm`.
- [ ] Run `uv run pytest` on all `_enforce_limits` tests — confirm all pass.
- [ ] Write failing test: `test_enqueue_adds_request_to_deque`.
- [ ] Implement `Gatekeeper._enqueue(self, request: APIRequest) -> None`.
- [ ] Write failing test: `test_enqueue_raises_queue_full_error_when_depth_exceeds_50`.
- [ ] Implement depth-50 guard and `QueueFullError` raise in `_enqueue`.
- [ ] Run `uv run pytest` on all `_enqueue` tests — confirm all pass.
- [ ] Write failing test: `test_dequeue_returns_oldest_request_fifo`.
- [ ] Implement `Gatekeeper._dequeue(self) -> APIRequest`.
- [ ] Write failing test: `test_dequeue_raises_when_queue_is_empty`.
- [ ] Implement empty-queue guard in `_dequeue`.
- [ ] Run `uv run pytest` on all `_dequeue` tests — confirm all pass.
- [ ] Write failing test: `test_get_usage_returns_correct_stats_for_known_agent`.
- [ ] Implement `Gatekeeper.get_usage(self, agent_id: str) -> UsageStats`.
- [ ] Write failing test: `test_get_usage_returns_zero_stats_for_unknown_agent`.
- [ ] Implement zero-default for unknown agents in `get_usage`.
- [ ] Write failing test: `test_gatekeeper_is_thread_safe` — concurrent dispatches do not corrupt usage totals.
- [ ] Verify `threading.Lock` guards `dispatch` and `get_usage`.
- [ ] Run `uv run pytest` on all `get_usage` and thread-safety tests — confirm all pass.
- [ ] Run `uv run ruff check src/infrastructure/gatekeeper.py` — confirm 0 violations.
- [ ] Run `wc -l src/infrastructure/gatekeeper.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement Gatekeeper with token-bucket rate limiting and FIFO queue`.

### 1.4 Watchdog

- [ ] Create `src/infrastructure/watchdog.py`.
- [ ] Add imports: `import concurrent.futures`, `import logging`, `from typing import Any, Callable`.
- [ ] Define `WatchdogError(Exception)` in `watchdog.py`.
- [ ] Create `tests/unit/test_watchdog.py`.
- [ ] Add imports: `import pytest`, `import time`, `from src.infrastructure.watchdog import Watchdog, WatchdogError`.
- [ ] Define `fast_watchdog` fixture: `Watchdog(timeout_seconds=0.05, max_retries=1)`.
- [ ] Write failing test: `test_watchdog_init_sets_timeout_seconds`.
- [ ] Write failing test: `test_watchdog_init_sets_max_retries`.
- [ ] Implement `Watchdog.__init__(self, timeout_seconds: int, max_retries: int)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_run_returns_result_when_function_completes_within_timeout`.
- [ ] Implement `Watchdog.run(self, fn: Callable, args: dict) -> Any`.
- [ ] Write failing test: `test_run_retries_once_on_first_timeout` — fn sleeps > timeout on first call, succeeds on retry.
- [ ] Implement retry logic inside `run`.
- [ ] Write failing test: `test_run_raises_watchdog_error_on_two_consecutive_timeouts`.
- [ ] Implement `WatchdogError` raise after max retries exceeded.
- [ ] Run `uv run pytest` on all `run` tests — confirm all pass.
- [ ] Write failing test: `test_kill_and_retry_cancels_the_timed_out_future`.
- [ ] Implement `Watchdog._kill_and_retry(self, fn: Callable, args: dict) -> Any`.
- [ ] Write failing test: `test_kill_and_retry_emits_warning_log_on_each_timeout`.
- [ ] Implement `logging.warning(...)` call in `_kill_and_retry`.
- [ ] Run `uv run pytest` on all `_kill_and_retry` tests — confirm all pass.
- [ ] Run `uv run ruff check src/infrastructure/watchdog.py` — confirm 0 violations.
- [ ] Run `wc -l src/infrastructure/watchdog.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement Watchdog with thread-pool timeout and retry logic`.

### 1.5 CostReporter

- [ ] Create `src/infrastructure/cost_reporter.py`.
- [ ] Add imports: `from dataclasses import dataclass, field`, `from typing import Dict`.
- [ ] Define `AgentUsage` dataclass (prompt_tokens, completion_tokens, model) in `cost_reporter.py`.
- [ ] Define `CostSummary` dataclass (per_agent, total_usd, budget_cap_usd, utilisation_pct) in `cost_reporter.py`.
- [ ] Create `tests/unit/test_cost_reporter.py`.
- [ ] Add imports: `import pytest`, `from src.infrastructure.cost_reporter import CostReporter, CostSummary`.
- [ ] Define `mock_pricing` fixture with known per-token USD rates.
- [ ] Define `cost_reporter` fixture: `CostReporter(mock_pricing, budget_cap_usd=2.00)`.
- [ ] Write failing test: `test_cost_reporter_init_stores_pricing`.
- [ ] Write failing test: `test_cost_reporter_init_stores_budget_cap`.
- [ ] Implement `CostReporter.__init__(self, pricing: dict, budget_cap_usd: float)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_record_usage_accumulates_prompt_tokens_for_agent`.
- [ ] Implement `CostReporter.record_usage(self, agent_id: str, model: str, prompt_tokens: int, completion_tokens: int) -> None`.
- [ ] Write failing test: `test_record_usage_creates_new_entry_for_first_call_per_agent`.
- [ ] Implement new-agent-entry creation in `record_usage`.
- [ ] Write failing test: `test_record_usage_accumulates_tokens_across_multiple_calls`.
- [ ] Verify token accumulation is additive in `record_usage`.
- [ ] Run `uv run pytest` on all `record_usage` tests — confirm all pass.
- [ ] Write failing test: `test_compute_returns_correct_total_usd_for_known_inputs`.
- [ ] Implement `CostReporter.compute(self) -> CostSummary`.
- [ ] Write failing test: `test_compute_per_agent_costs_sum_to_session_total`.
- [ ] Implement per-agent cost breakdown in `compute`.
- [ ] Write failing test: `test_compute_returns_zero_summary_when_no_usage_recorded`.
- [ ] Implement zero-usage guard in `compute`.
- [ ] Write failing test: `test_compute_calculates_utilisation_pct_correctly` — known cost / cap × 100.
- [ ] Implement utilisation percentage in `compute`.
- [ ] Run `uv run pytest` on all `compute` tests — confirm all pass.
- [ ] Write failing test: `test_print_report_writes_non_empty_output_to_stdout`.
- [ ] Implement `CostReporter.print_report(self, summary: CostSummary) -> None`.
- [ ] Write failing test: `test_print_report_output_contains_each_agent_name`.
- [ ] Write failing test: `test_print_report_output_contains_total_usd_line`.
- [ ] Write failing test: `test_print_report_output_contains_budget_utilisation_percentage`.
- [ ] Run `uv run pytest` on all `print_report` tests — confirm all pass.
- [ ] Run `uv run ruff check src/infrastructure/cost_reporter.py` — confirm 0 violations.
- [ ] Run `wc -l src/infrastructure/cost_reporter.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement CostReporter with per-agent USD breakdown`.

---

## Phase 2 — Agent SDK & Tools Layer

### 2.1 AgentSkill ABC

- [ ] Create `src/skills/base_skill.py`.
- [ ] Add imports: `from abc import ABC, abstractmethod`, `from dataclasses import dataclass`.
- [ ] Define `SkillError(Exception)` class in `base_skill.py`.
- [ ] Define `SkillResult` dataclass: fields `query: str`, `snippets: list[str]`, `raw_response: dict`.
- [ ] Define `AgentSkill(ABC)` with `skill_name: str` attribute and `@abstractmethod execute(query: str) -> SkillResult`.
- [ ] Create `tests/unit/test_base_skill.py`.
- [ ] Add imports: `import pytest`, `from src.skills.base_skill import AgentSkill, SkillResult, SkillError`.
- [ ] Write failing test: `test_agent_skill_cannot_be_instantiated_directly` — raises `TypeError`.
- [ ] Write failing test: `test_concrete_subclass_missing_execute_is_still_abstract`.
- [ ] Write failing test: `test_concrete_subclass_with_execute_is_instantiable`.
- [ ] Write failing test: `test_skill_result_dataclass_has_query_snippets_raw_response_fields`.
- [ ] Write failing test: `test_skill_error_is_subclass_of_exception`.
- [ ] Run `uv run pytest tests/unit/test_base_skill.py` — confirm all pass.
- [ ] Run `uv run ruff check src/skills/base_skill.py` — confirm 0 violations.
- [ ] Run `wc -l src/skills/base_skill.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement AgentSkill ABC and SkillResult dataclass`.

### 2.2 WebSearchTool

- [ ] Create `src/skills/web_search_tool.py`.
- [ ] Add imports: `import os`, `import requests`, `from src.skills.base_skill import AgentSkill, SkillResult, SkillError`.
- [ ] Create `tests/unit/test_web_search_tool.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import patch, MagicMock`.
- [ ] Add `from src.skills.web_search_tool import WebSearchTool`.
- [ ] Define `mock_search_response` fixture: valid search API JSON dict.
- [ ] Define `web_search_tool` fixture with env vars patched via `monkeypatch`.
- [ ] Write failing test: `test_web_search_tool_init_reads_api_key_from_env`.
- [ ] Write failing test: `test_web_search_tool_init_reads_base_url_from_env`.
- [ ] Implement `WebSearchTool.__init__(self, api_key: str, base_url: str)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_sanitize_strips_leading_and_trailing_whitespace`.
- [ ] Implement `WebSearchTool._sanitize(self, query: str) -> str`.
- [ ] Write failing test: `test_sanitize_truncates_query_to_200_characters`.
- [ ] Implement 200-char truncation in `_sanitize`.
- [ ] Write failing test: `test_sanitize_returns_empty_string_for_whitespace_only_input`.
- [ ] Implement whitespace-only guard in `_sanitize`.
- [ ] Run `uv run pytest` on all `_sanitize` tests — confirm all pass.
- [ ] Write failing test: `test_parse_response_returns_skill_result_with_non_empty_snippets`.
- [ ] Implement `WebSearchTool._parse_response(self, raw: dict) -> SkillResult`.
- [ ] Write failing test: `test_parse_response_raises_skill_error_on_missing_results_key`.
- [ ] Implement missing-key guard in `_parse_response`.
- [ ] Write failing test: `test_parse_response_raises_skill_error_on_empty_results_list`.
- [ ] Implement empty-results guard in `_parse_response`.
- [ ] Run `uv run pytest` on all `_parse_response` tests — confirm all pass.
- [ ] Write failing test: `test_execute_returns_skill_result_on_http_200` — mocked happy path.
- [ ] Implement `WebSearchTool.execute(self, query: str) -> SkillResult`.
- [ ] Write failing test: `test_execute_calls_sanitize_before_dispatching_query`.
- [ ] Verify `_sanitize` is invoked inside `execute`.
- [ ] Write failing test: `test_execute_raises_skill_error_on_http_500`.
- [ ] Implement HTTP-5xx error handling in `execute`.
- [ ] Write failing test: `test_execute_raises_skill_error_on_http_429`.
- [ ] Implement HTTP-429 handling in `execute`.
- [ ] Write failing test: `test_execute_raises_skill_error_on_requests_timeout`.
- [ ] Implement `requests.Timeout` handling in `execute`.
- [ ] Run `uv run pytest` on all `execute` tests — confirm all pass.
- [ ] Create `tests/integration/test_web_search_integration.py` marked `@pytest.mark.slow`.
- [ ] Write integration test: `test_web_search_live_returns_non_empty_snippets`.
- [ ] Run `uv run ruff check src/skills/web_search_tool.py` — confirm 0 violations.
- [ ] Run `wc -l src/skills/web_search_tool.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement WebSearchTool with sanitization and error handling`.

### 2.3 BaseAgent ABC

- [ ] Create `src/agents/base_agent.py`.
- [ ] Add imports: `import json`, `from abc import ABC, abstractmethod`, `import jsonschema`, `from pathlib import Path`.
- [ ] Add `from src.infrastructure.gatekeeper import Gatekeeper, APIRequest`.
- [ ] Define `MessageParseError(Exception)` in `base_agent.py`.
- [ ] Define `AgentFailureError(Exception)` in `base_agent.py`.
- [ ] Define `DebateMessage` dataclass in `base_agent.py` with all 8 fields from schema.
- [ ] Create `tests/unit/test_base_agent.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [ ] Add `from src.agents.base_agent import BaseAgent, MessageParseError, AgentFailureError, DebateMessage`.
- [ ] Define `mock_gatekeeper` fixture as `MagicMock(spec=Gatekeeper)`.
- [ ] Define `mock_config` fixture with minimal agent config dict.
- [ ] Define `ConcreteAgent` helper subclass (implements all abstract methods) inside test file.
- [ ] Define `concrete_agent` fixture instantiating `ConcreteAgent`.
- [ ] Write failing test: `test_base_agent_cannot_be_instantiated_directly` — raises `TypeError`.
- [ ] Write failing test: `test_base_agent_init_sets_agent_id`.
- [ ] Write failing test: `test_base_agent_init_sets_role`.
- [ ] Write failing test: `test_base_agent_init_stores_gatekeeper_reference`.
- [ ] Implement `BaseAgent.__init__(self, agent_id: str, role: str, gatekeeper: Gatekeeper, config: dict)` with Google-style docstring.
- [ ] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_parse_response_returns_debate_message_on_valid_json`.
- [ ] Implement `BaseAgent.parse_response(self, raw: str) -> DebateMessage`.
- [ ] Write failing test: `test_parse_response_raises_message_parse_error_on_invalid_json`.
- [ ] Implement `json.JSONDecodeError` handling in `parse_response`.
- [ ] Write failing test: `test_parse_response_raises_message_parse_error_on_schema_violation`.
- [ ] Implement `jsonschema.ValidationError` handling in `parse_response`.
- [ ] Run `uv run pytest` on all `parse_response` tests — confirm all pass.
- [ ] Write failing test: `test_validate_schema_returns_true_on_valid_message_dict`.
- [ ] Implement `BaseAgent._validate_schema(self, msg: dict) -> bool`.
- [ ] Write failing test: `test_validate_schema_returns_false_on_missing_required_field`.
- [ ] Write failing test: `test_validate_schema_returns_false_on_wrong_sender_enum_value`.
- [ ] Run `uv run pytest` on all `_validate_schema` tests — confirm all pass.
- [ ] Write failing test: `test_call_api_dispatches_through_gatekeeper`.
- [ ] Implement `BaseAgent.call_api(self, prompt: str) -> str`.
- [ ] Write failing test: `test_call_api_uses_model_from_config_dict`.
- [ ] Implement model lookup from `self.config` in `call_api`.
- [ ] Write failing test: `test_call_api_includes_agent_id_in_request`.
- [ ] Verify `agent_id` is included in the `APIRequest` object.
- [ ] Run `uv run pytest` on all `call_api` tests — confirm all pass.
- [ ] Run `uv run ruff check src/agents/base_agent.py` — confirm 0 violations.
- [ ] Run `wc -l src/agents/base_agent.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement BaseAgent ABC with JSON schema validation`.

### 2.4 ProSonAgent

- [ ] Create `src/agents/pro_son_agent.py`.
- [ ] Add imports: `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError, AgentFailureError`.
- [ ] Add `from src.skills.base_skill import AgentSkill`.
- [ ] Create `tests/unit/test_pro_son_agent.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [ ] Add `from src.agents.pro_son_agent import ProSonAgent`.
- [ ] Define `mock_gatekeeper` fixture for pro son tests.
- [ ] Define `mock_skill` fixture as `MagicMock(spec=AgentSkill)`.
- [ ] Define `pro_son_config` fixture with model and agent_id fields.
- [ ] Define `pro_son_agent` fixture instantiating `ProSonAgent`.
- [ ] Write failing test: `test_pro_son_init_sets_position_attribute_to_pro`.
- [ ] Write failing test: `test_pro_son_init_stores_skills_list`.
- [ ] Implement `ProSonAgent.__init__(self, config: dict, gatekeeper, skills: list)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_build_prompt_returns_non_empty_string`.
- [ ] Implement `ProSonAgent.build_prompt(self, context) -> str`.
- [ ] Write failing test: `test_build_prompt_contains_pro_position_instruction`.
- [ ] Implement pro-position instruction injection in `build_prompt`.
- [ ] Write failing test: `test_build_prompt_embeds_topic_from_debate_state`.
- [ ] Run `uv run pytest` on all `build_prompt` tests — confirm all pass.
- [ ] Write failing test: `test_enforce_position_returns_content_unchanged_for_pro_argument`.
- [ ] Implement `ProSonAgent._enforce_position(self, content: str) -> str`.
- [ ] Write failing test: `test_enforce_position_raises_retry_signal_when_con_stance_detected`.
- [ ] Implement con-content detection and retry signal in `_enforce_position`.
- [ ] Run `uv run pytest` on all `_enforce_position` tests — confirm all pass.
- [ ] Write failing test: `test_generate_argument_returns_valid_debate_message` — mocked API, happy path.
- [ ] Implement `ProSonAgent.generate_argument(self, prompt: DebateMessage) -> DebateMessage`.
- [ ] Write failing test: `test_generate_argument_sources_field_is_non_empty`.
- [ ] Implement sources enforcement (web search results embedded) in `generate_argument`.
- [ ] Write failing test: `test_generate_argument_retries_up_to_2_times_on_position_violation`.
- [ ] Implement max-2-retries logic in `generate_argument`.
- [ ] Write failing test: `test_generate_argument_raises_agent_failure_error_after_2_retries`.
- [ ] Implement `AgentFailureError` raise after retries exhausted.
- [ ] Run `uv run pytest` on all `generate_argument` tests — confirm all pass.
- [ ] Run `uv run ruff check src/agents/pro_son_agent.py` — confirm 0 violations.
- [ ] Run `wc -l src/agents/pro_son_agent.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement ProSonAgent with position enforcement and retry`.

### 2.5 ConSonAgent

- [ ] Create `src/agents/con_son_agent.py`.
- [ ] Add imports: `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError, AgentFailureError`.
- [ ] Add `from src.skills.base_skill import AgentSkill`.
- [ ] Create `tests/unit/test_con_son_agent.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [ ] Add `from src.agents.con_son_agent import ConSonAgent`.
- [ ] Define `mock_gatekeeper` fixture for con son tests.
- [ ] Define `mock_skill` fixture as `MagicMock(spec=AgentSkill)`.
- [ ] Define `con_son_config` fixture with model and agent_id fields.
- [ ] Define `con_son_agent` fixture instantiating `ConSonAgent`.
- [ ] Write failing test: `test_con_son_init_sets_position_attribute_to_con`.
- [ ] Write failing test: `test_con_son_init_stores_skills_list`.
- [ ] Implement `ConSonAgent.__init__(self, config: dict, gatekeeper, skills: list)` with Google-style docstring.
- [ ] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_build_prompt_returns_non_empty_string`.
- [ ] Implement `ConSonAgent.build_prompt(self, context) -> str`.
- [ ] Write failing test: `test_build_prompt_contains_con_position_instruction`.
- [ ] Implement con-position instruction injection in `build_prompt`.
- [ ] Write failing test: `test_build_prompt_embeds_topic_from_debate_state`.
- [ ] Run `uv run pytest` on all `build_prompt` tests — confirm all pass.
- [ ] Write failing test: `test_enforce_position_returns_content_unchanged_for_con_argument`.
- [ ] Implement `ConSonAgent._enforce_position(self, content: str) -> str`.
- [ ] Write failing test: `test_enforce_position_raises_retry_signal_when_pro_stance_detected`.
- [ ] Implement pro-content detection and retry signal in `_enforce_position`.
- [ ] Run `uv run pytest` on all `_enforce_position` tests — confirm all pass.
- [ ] Write failing test: `test_generate_argument_returns_valid_debate_message` — mocked API, happy path.
- [ ] Implement `ConSonAgent.generate_argument(self, prompt: DebateMessage) -> DebateMessage`.
- [ ] Write failing test: `test_generate_argument_sources_field_is_non_empty`.
- [ ] Implement sources enforcement in `generate_argument`.
- [ ] Write failing test: `test_generate_argument_retries_up_to_2_times_on_position_violation`.
- [ ] Implement max-2-retries logic in `generate_argument`.
- [ ] Write failing test: `test_generate_argument_raises_agent_failure_error_after_2_retries`.
- [ ] Implement `AgentFailureError` raise after retries exhausted.
- [ ] Run `uv run pytest` on all `generate_argument` tests — confirm all pass.
- [ ] Run `uv run ruff check src/agents/con_son_agent.py` — confirm 0 violations.
- [ ] Run `wc -l src/agents/con_son_agent.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement ConSonAgent with position enforcement and retry`.

### 2.6 FatherAgent

- [ ] Create `src/agents/father_agent.py`.
- [ ] Add imports: `import json`, `import uuid`, `from datetime import datetime, timezone`.
- [ ] Add `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError`.
- [ ] Define `NotEnoughTurnsError(Exception)` in `father_agent.py`.
- [ ] Define `Verdict` dataclass with fields: `verdict_id`, `winner`, `draw`, `reasoning`, `turn_count`, `timestamp`.
- [ ] Create `tests/unit/test_father_agent.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [ ] Add `from src.agents.father_agent import FatherAgent, NotEnoughTurnsError, Verdict`.
- [ ] Define `mock_gatekeeper` fixture for father tests.
- [ ] Define `father_config` fixture with model and agent_id fields.
- [ ] Define `father_agent` fixture instantiating `FatherAgent`.
- [ ] Define `sample_debate_state` fixture with 20+ transcript messages.
- [ ] Define `short_debate_state` fixture with only 10 messages.
- [ ] Write failing test: `test_father_agent_init_sets_role_to_father`.
- [ ] Implement `FatherAgent.__init__(self, config: dict, gatekeeper)` with Google-style docstring.
- [ ] Run `uv run pytest` on `__init__` test — confirm pass.
- [ ] Write failing test: `test_open_debate_returns_debate_message`.
- [ ] Implement `FatherAgent.open_debate(self, topic: str) -> DebateMessage`.
- [ ] Write failing test: `test_open_debate_sender_field_is_father`.
- [ ] Write failing test: `test_open_debate_recipient_field_is_pro_son`.
- [ ] Write failing test: `test_open_debate_message_id_is_valid_uuid`.
- [ ] Implement all field constraints in `open_debate`.
- [ ] Run `uv run pytest` on all `open_debate` tests — confirm all pass.
- [ ] Write failing test: `test_validate_message_returns_true_on_complete_valid_message`.
- [ ] Implement `FatherAgent._validate_message(self, msg: DebateMessage) -> bool`.
- [ ] Write failing test: `test_validate_message_returns_false_on_missing_content`.
- [ ] Implement missing-content detection in `_validate_message`.
- [ ] Write failing test: `test_validate_message_returns_false_on_invalid_sender_value`.
- [ ] Implement sender-enum validation in `_validate_message`.
- [ ] Write failing test: `test_validate_message_returns_false_on_empty_sources_on_turn_divisible_by_3`.
- [ ] Implement per-3-turn sources check in `_validate_message`.
- [ ] Run `uv run pytest` on all `_validate_message` tests — confirm all pass.
- [ ] Write failing test: `test_route_returns_pro_son_identifier_for_pro_son_recipient`.
- [ ] Implement `FatherAgent.route(self, msg: DebateMessage) -> str`.
- [ ] Write failing test: `test_route_returns_con_son_identifier_for_con_son_recipient`.
- [ ] Implement con son routing branch.
- [ ] Write failing test: `test_route_raises_value_error_on_invalid_recipient_value`.
- [ ] Implement invalid-recipient guard in `route`.
- [ ] Run `uv run pytest` on all `route` tests — confirm all pass.
- [ ] Write failing test: `test_check_min_turns_returns_false_when_turn_count_is_19`.
- [ ] Implement `FatherAgent._check_min_turns(self, state) -> bool`.
- [ ] Write failing test: `test_check_min_turns_returns_true_when_turn_count_is_20`.
- [ ] Write failing test: `test_check_min_turns_returns_true_when_turn_count_exceeds_20`.
- [ ] Run `uv run pytest` on all `_check_min_turns` tests — confirm all pass.
- [ ] Write failing test: `test_score_persuasiveness_returns_dict_with_pro_and_con_keys`.
- [ ] Implement `FatherAgent._score_persuasiveness(self, transcript: list) -> dict`.
- [ ] Write failing test: `test_score_persuasiveness_each_entry_has_clarity_evidence_logic_total`.
- [ ] Implement rubric-dimension extraction (clarity, evidence, logic) in `_score_persuasiveness`.
- [ ] Write failing test: `test_score_persuasiveness_uses_rubric_prompt_template_verbatim`.
- [ ] Verify rubric prompt from PRD §9.3 is embedded unchanged in `_score_persuasiveness`.
- [ ] Run `uv run pytest` on all `_score_persuasiveness` tests — confirm all pass.
- [ ] Write failing test: `test_evaluate_raises_not_enough_turns_error_when_turn_count_below_20`.
- [ ] Implement `FatherAgent.evaluate(self, state) -> Verdict`.
- [ ] Write failing test: `test_evaluate_returns_verdict_with_draw_false`.
- [ ] Implement `draw=False` enforcement in `evaluate`.
- [ ] Write failing test: `test_evaluate_winner_is_exactly_pro_son_or_con_son`.
- [ ] Implement winner-selection from rubric totals in `evaluate`.
- [ ] Write failing test: `test_evaluate_reasoning_field_is_at_least_50_characters`.
- [ ] Implement reasoning-length enforcement in `evaluate`.
- [ ] Write failing test: `test_evaluate_applies_tiebreaker_when_total_scores_are_equal`.
- [ ] Implement momentum tiebreaker (last 4 turns) in `evaluate`.
- [ ] Run `uv run pytest` on all `evaluate` tests — confirm all pass.
- [ ] Run `uv run ruff check src/agents/father_agent.py` — confirm 0 violations.
- [ ] Run `wc -l src/agents/father_agent.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement FatherAgent with routing and persuasiveness evaluation`.

---

## Phase 3 — Debate Engine

### 3.1 StateManager

- [ ] Create `src/engine/state_manager.py`.
- [ ] Add imports: `import json`, `import uuid`, `from dataclasses import dataclass, field`, `from datetime import datetime, timezone`.
- [ ] Define `DebateState` dataclass with all fields from PRD §4.3.
- [ ] Create `tests/unit/test_state_manager.py`.
- [ ] Add imports: `import pytest`, `from src.engine.state_manager import StateManager, DebateState`.
- [ ] Define `state_manager` fixture: fresh `StateManager()`.
- [ ] Define `sample_message` fixture: valid `DebateMessage` dict.
- [ ] Define `sample_verdict` fixture: valid `Verdict` dict.
- [ ] Write failing test: `test_state_manager_init_status_is_initialization`.
- [ ] Write failing test: `test_state_manager_init_turn_count_is_zero`.
- [ ] Write failing test: `test_state_manager_init_transcript_is_empty_list`.
- [ ] Implement `StateManager.__init__(self)` with Google-style docstring.
- [ ] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_record_message_appends_to_transcript`.
- [ ] Implement `StateManager.record_message(self, msg) -> None`.
- [ ] Write failing test: `test_record_message_increments_turn_count_by_one`.
- [ ] Implement turn-count increment in `record_message`.
- [ ] Write failing test: `test_record_message_refreshes_updated_at_timestamp`.
- [ ] Implement `updated_at` refresh in `record_message`.
- [ ] Run `uv run pytest` on all `record_message` tests — confirm all pass.
- [ ] Write failing test: `test_record_verdict_stores_verdict_object`.
- [ ] Implement `StateManager.record_verdict(self, v) -> None`.
- [ ] Write failing test: `test_record_verdict_raises_if_verdict_already_exists`.
- [ ] Implement duplicate-verdict guard in `record_verdict`.
- [ ] Run `uv run pytest` on all `record_verdict` tests — confirm all pass.
- [ ] Write failing test: `test_get_turn_count_returns_zero_on_fresh_state`.
- [ ] Write failing test: `test_get_turn_count_returns_correct_value_after_n_messages`.
- [ ] Implement `StateManager.get_turn_count(self) -> int`.
- [ ] Run `uv run pytest` on `get_turn_count` tests — confirm all pass.
- [ ] Write failing test: `test_to_json_output_is_a_string`.
- [ ] Implement `StateManager.to_json(self) -> str`.
- [ ] Write failing test: `test_to_json_output_is_parseable_json`.
- [ ] Write failing test: `test_to_json_includes_topic_and_turn_count_and_transcript`.
- [ ] Run `uv run pytest` on all `to_json` tests — confirm all pass.
- [ ] Write failing test: `test_from_json_restores_topic_field`.
- [ ] Implement `StateManager.from_json(self, data: str) -> DebateState`.
- [ ] Write failing test: `test_from_json_restores_turn_count`.
- [ ] Write failing test: `test_from_json_restores_full_transcript_array`.
- [ ] Write failing test: `test_from_json_raises_value_error_on_malformed_json`.
- [ ] Implement JSON parse error handling in `from_json`.
- [ ] Run `uv run pytest` on all `from_json` tests — confirm all pass.
- [ ] Run `uv run ruff check src/engine/state_manager.py` — confirm 0 violations.
- [ ] Run `wc -l src/engine/state_manager.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement StateManager with JSON serialization round-trip`.

### 3.2 DebateEngine

- [ ] Create `src/engine/debate_engine.py`.
- [ ] Add `import logging` to `debate_engine.py`.
- [ ] Add imports for `FatherAgent`, `ProSonAgent`, `ConSonAgent`, `StateManager`, `Watchdog`, `WatchdogError`, `CostReporter`, `Gatekeeper`, `ConfigLoader`.
- [ ] Create `tests/unit/test_debate_engine.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch, call`.
- [ ] Add `from src.engine.debate_engine import DebateEngine`.
- [ ] Define `mock_config` fixture with short turn limit for fast unit testing.
- [ ] Define `mock_father`, `mock_pro_son`, `mock_con_son`, `mock_state_manager`, `mock_watchdog`, `mock_cost_reporter` fixtures.
- [ ] Define `debate_engine` fixture wiring all mocks.
- [ ] Write failing test: `test_debate_engine_init_creates_father_agent`.
- [ ] Write failing test: `test_debate_engine_init_creates_pro_son_agent`.
- [ ] Write failing test: `test_debate_engine_init_creates_con_son_agent`.
- [ ] Write failing test: `test_debate_engine_init_creates_state_manager`.
- [ ] Write failing test: `test_debate_engine_init_creates_watchdog_with_configured_timeout`.
- [ ] Implement `DebateEngine.__init__(self, config: dict)` with Google-style docstring.
- [ ] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [ ] Write failing test: `test_run_turn_loop_executes_at_least_min_turns`.
- [ ] Implement `DebateEngine._run_turn_loop(self) -> None`.
- [ ] Write failing test: `test_run_turn_loop_alternates_pro_son_and_con_son_each_round`.
- [ ] Implement alternation logic (pro → father → con → father) in `_run_turn_loop`.
- [ ] Write failing test: `test_run_turn_loop_calls_record_message_after_every_turn`.
- [ ] Implement `state_manager.record_message()` call in `_run_turn_loop`.
- [ ] Write failing test: `test_run_turn_loop_routes_all_responses_through_father`.
- [ ] Verify `father.route()` is called for each agent response.
- [ ] Run `uv run pytest` on all `_run_turn_loop` tests — confirm all pass.
- [ ] Write failing test: `test_check_budget_returns_false_when_cost_below_cap`.
- [ ] Implement `DebateEngine._check_budget(self) -> bool`.
- [ ] Write failing test: `test_check_budget_returns_true_when_cost_exceeds_cap`.
- [ ] Implement cost-cap comparison using `CostReporter.compute()`.
- [ ] Write failing test: `test_check_budget_logs_warning_at_90_percent_threshold`.
- [ ] Implement 90%-threshold warning log in `_check_budget`.
- [ ] Run `uv run pytest` on all `_check_budget` tests — confirm all pass.
- [ ] Write failing test: `test_handle_watchdog_error_logs_error_to_logger`.
- [ ] Implement `DebateEngine._handle_watchdog_error(self, error: WatchdogError) -> None`.
- [ ] Write failing test: `test_handle_watchdog_error_appends_event_to_state`.
- [ ] Implement state-event append in `_handle_watchdog_error`.
- [ ] Write failing test: `test_handle_watchdog_error_saves_partial_state_json_to_logs`.
- [ ] Implement partial-state JSON dump in `_handle_watchdog_error`.
- [ ] Run `uv run pytest` on all `_handle_watchdog_error` tests — confirm all pass.
- [ ] Write failing test: `test_start_returns_verdict_object`.
- [ ] Implement `DebateEngine.start(self, topic: str) -> Verdict`.
- [ ] Write failing test: `test_start_calls_father_open_debate_with_topic_string`.
- [ ] Write failing test: `test_start_verdict_draw_field_is_always_false`.
- [ ] Write failing test: `test_start_forces_early_evaluation_when_budget_cap_exceeded`.
- [ ] Implement early-evaluation branch in `start`.
- [ ] Write failing test: `test_start_propagates_watchdog_error_after_max_retries`.
- [ ] Implement `WatchdogError` propagation in `start`.
- [ ] Run `uv run pytest` on all `start` tests — confirm all pass.
- [ ] Run `uv run ruff check src/engine/debate_engine.py` — confirm 0 violations.
- [ ] Run `wc -l src/engine/debate_engine.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement DebateEngine orchestration loop with budget guard`.

### 3.3 Integration Tests — Full Debate

- [ ] Create `tests/integration/test_full_debate.py`.
- [ ] Add `import pytest`, `import os`, `from src.engine.debate_engine import DebateEngine`.
- [ ] Add `from src.infrastructure.config_loader import ConfigLoader`.
- [ ] Add `pytestmark = pytest.mark.slow` at module level.
- [ ] Define `live_config` fixture loading from real `config/setup.json`.
- [ ] Define `debate_engine_live` fixture with real API keys from `.env`.
- [ ] Write integration test: `test_full_debate_completes_without_raising_exception`.
- [ ] Write integration test: `test_full_debate_returns_verdict_object`.
- [ ] Write integration test: `test_full_debate_transcript_has_at_least_20_messages`.
- [ ] Write integration test: `test_full_debate_all_messages_validate_against_debate_message_schema`.
- [ ] Write integration test: `test_full_debate_verdict_draw_field_is_false`.
- [ ] Write integration test: `test_full_debate_verdict_winner_is_pro_son_or_con_son`.
- [ ] Write integration test: `test_full_debate_web_search_invoked_at_least_once_per_3_turns_per_side`.
- [ ] Write integration test: `test_full_debate_cost_report_generated_at_session_end`.
- [ ] Write integration test: `test_no_message_sent_directly_from_pro_son_to_con_son`.
- [ ] Write integration test: `test_no_message_sent_directly_from_con_son_to_pro_son`.
- [ ] Run `uv run pytest -m slow tests/integration/test_full_debate.py` — confirm all pass.
- [ ] Fix any integration failures and re-run until green.
- [ ] Git commit: `test: add full-debate integration test suite`.

---

## Phase 4 — CLI, Reporting & Final Delivery

### 4.1 DebateCLI

- [ ] Create `src/ui/debate_cli.py`.
- [ ] Add imports: `import argparse`, `import sys`.
- [ ] Add `from src.engine.debate_engine import DebateEngine`.
- [ ] Add `from src.infrastructure.config_loader import ConfigLoader`.
- [ ] Add `from src.infrastructure.cost_reporter import CostReporter`.
- [ ] Add `from src.infrastructure.watchdog import WatchdogError`.
- [ ] Create `tests/unit/test_debate_cli.py`.
- [ ] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [ ] Add `from src.ui.debate_cli import parse_args, run`.
- [ ] Write failing test: `test_parse_args_exits_with_code_2_when_topic_is_missing`.
- [ ] Implement `parse_args() -> argparse.Namespace` with required `--topic` argument.
- [ ] Write failing test: `test_parse_args_returns_namespace_with_topic_string`.
- [ ] Write failing test: `test_parse_args_accepts_optional_config_flag`.
- [ ] Implement optional `--config PATH` flag in `parse_args`.
- [ ] Write failing test: `test_parse_args_accepts_optional_dry_run_flag`.
- [ ] Implement optional `--dry-run` boolean flag in `parse_args`.
- [ ] Run `uv run pytest` on all `parse_args` tests — confirm all pass.
- [ ] Write failing test: `test_run_returns_0_on_successful_debate` — mocked engine.
- [ ] Implement `run() -> int` entry function.
- [ ] Write failing test: `test_run_calls_debate_engine_start_with_topic_string`.
- [ ] Verify `engine.start(topic)` is called inside `run`.
- [ ] Write failing test: `test_run_prints_verdict_output_to_stdout`.
- [ ] Implement `_print_verdict(verdict) -> None` and wire into `run`.
- [ ] Write failing test: `test_run_prints_cost_report_to_stdout`.
- [ ] Implement `_print_cost_report(summary) -> None` and wire into `run`.
- [ ] Write failing test: `test_run_dry_run_validates_config_without_calling_llm_api`.
- [ ] Implement dry-run config-only validation in `run`.
- [ ] Write failing test: `test_run_dry_run_prints_config_loaded_message`.
- [ ] Write failing test: `test_run_returns_1_on_watchdog_error`.
- [ ] Implement `WatchdogError` → exit code 1 in `run`.
- [ ] Run `uv run pytest` on all `run` tests — confirm all pass.
- [ ] Add `debate = "src.ui.debate_cli:run"` to `[project.scripts]` in `pyproject.toml`.
- [ ] Run `uv sync` to register the new entry point.
- [ ] Run `uv run debate --help` — confirm help text prints without error.
- [ ] Run `uv run debate --topic "AI is beneficial" --dry-run` — confirm dry-run output matches PRD §7.1.
- [ ] Run `uv run ruff check src/ui/debate_cli.py` — confirm 0 violations.
- [ ] Run `wc -l src/ui/debate_cli.py` — confirm ≤ 150 lines.
- [ ] Git commit: `feat: implement DebateCLI with argparse, dry-run, and cost report`.

### 4.2 Live CLI Output Verification

- [ ] Run `uv run debate --topic "AI will replace human workers"` with real API keys.
- [ ] Verify terminal shows `[INFO]  Loading config from config/setup.json ...`.
- [ ] Verify terminal shows `[INFO]  Config loaded. Schema version: 1.0`.
- [ ] Verify terminal shows agent model assignments line.
- [ ] Verify terminal shows `[DEBATE STARTING]` block with topic string.
- [ ] Verify terminal shows `[TURN N / 20+]` announcement for each turn.
- [ ] Verify terminal shows `[SEARCH]` lines for each web search invocation.
- [ ] Verify terminal shows `[PRO SON] Argument received` with token count.
- [ ] Verify terminal shows `[CON SON] Argument received` with token count.
- [ ] Verify terminal shows `[EVALUATION]` block with per-dimension rubric scores.
- [ ] Verify terminal shows `[VERDICT]` box with winner name and reasoning text.
- [ ] Verify terminal shows cost report table with all three agent rows and totals.
- [ ] Verify exit code 0 on success: `echo $?`.
- [ ] Git commit: `test: verify live CLI output matches PRD §7 specification`.

### 4.3 Final Code Quality Gate

- [ ] Run `uv run ruff check .` across entire repo.
- [ ] Fix every ruff violation found (zero tolerance policy).
- [ ] Run `uv run ruff check .` again — confirm output is completely empty.
- [ ] Run `uv run pytest --cov=src --cov-report=term-missing`.
- [ ] Identify every module below 85% coverage from the report.
- [ ] Write additional unit tests for each under-covered module.
- [ ] Re-run `uv run pytest --cov=src --cov-fail-under=85` — confirm it passes.
- [ ] Run `grep -rn "sk-ant" src/` — confirm 0 matches (no hardcoded Anthropic keys).
- [ ] Run `grep -rn "api_key\s*=\s*['\"]" src/` — confirm 0 matches.
- [ ] Run `grep -rn "ANTHROPIC_API_KEY\s*=\s*['\"]sk-" src/` — confirm 0 matches.
- [ ] Audit every `.py` file in `src/` for hardcoded base URLs or IP addresses.
- [ ] Check every source file: `for f in $(find src -name "*.py"); do c=$(wc -l < "$f"); [ "$c" -gt 150 ] && echo "$f: $c lines"; done`.
- [ ] Split any file that exceeds 150 lines into appropriate sub-modules.
- [ ] Re-run ruff and pytest after any splits — confirm both still pass.
- [ ] Validate all three config JSON files: `python -m json.tool config/setup.json`, `rate_limits.json`, `pricing.json`.
- [ ] Run `uv run python -c "from src.engine.debate_engine import DebateEngine"` — no import error.
- [ ] Run `uv run python -c "from src.ui.debate_cli import run"` — no import error.
- [ ] Confirm `logs/` is not tracked: `git ls-files logs/` returns empty.
- [ ] Confirm `.env` is not tracked: `git ls-files .env` returns empty.
- [ ] Git commit: `chore: code quality gate — 0 ruff violations, ≥85% coverage`.

### 4.4 README Completion

- [ ] Write `## Overview` section with full system description in `README.md`.
- [ ] Write `## Architecture` section referencing PLAN.md C4 diagrams.
- [ ] Write `## Prerequisites` section: Python 3.11+, uv, API keys required.
- [ ] Write `## Installation` section: step-by-step `uv sync` and `.env` setup.
- [ ] Write `## Configuration` section describing all config files and key fields.
- [ ] Write `## Usage` section with `uv run debate --topic "..."` example.
- [ ] Write `## Dry Run` section showing `--dry-run` flag usage.
- [ ] Write `## Debate Output` section describing each terminal output stage per PRD §7.
- [ ] Write `## Running Tests` section: unit (`uv run pytest`) and integration (`uv run pytest -m slow`).
- [ ] Write `## Cost Reporting` section explaining the cost table columns and budget cap.
- [ ] Write `## Golden Rules` section: 150-line limit, ruff, 85% coverage, TDD.
- [ ] Write `## Project Structure` section with full directory tree.
- [ ] Write `## Agent Roles` section with three-agent table (Father/Pro Son/Con Son).
- [ ] Write `## JSON Message Contract` section with example `DebateMessage` JSON.
- [ ] Write `## Verdict Format` section with example `Verdict` JSON.
- [ ] Write `## State Machine` section summarising the four lifecycle states.
- [ ] Write `## Error Handling` section with condensed edge-case table from PRD §6.
- [ ] Write `## Persuasiveness Rubric` section with the three scoring dimensions.
- [ ] Write `## Extensibility` section explaining the `AgentSkill` plugin pattern.
- [ ] Write `## License` section (MIT).
- [ ] Proof-read README for accuracy against final implementation.
- [ ] Git commit: `docs: complete README with architecture, usage, and examples`.

### 4.5 Sample Output & Acceptance Verification

- [ ] Run full live debate on topic `"Remote work is better than office work"`.
- [ ] Save terminal output to `examples/sample_output.txt`.
- [ ] Copy final debate state JSON from `logs/` to `examples/sample_debate.json`.
- [ ] Verify `examples/sample_debate.json` transcript array has ≥ 20 entries.
- [ ] Verify `examples/sample_debate.json` verdict has `draw == false`.
- [ ] Verify `examples/sample_debate.json` has non-null `cost_summary`.
- [ ] Verify AC-01: transcript length ≥ 20 (10 per side).
- [ ] Verify AC-02: `sources` field non-empty at least once every 3 turns per side.
- [ ] Verify AC-03: run schema validator on every message in sample — 100% pass.
- [ ] Verify AC-04: simulate 31-second API hang (mock) — Watchdog fires within 35 s.
- [ ] Verify AC-05: run three debates on different topics — all complete without intervention.
- [ ] Verify AC-06: verdict `draw` is `false` in all three sample runs.
- [ ] Verify AC-07: `uv run ruff check .` output is empty.
- [ ] Verify AC-08: `uv run pytest --cov=src --cov-fail-under=85` passes.
- [ ] Verify AC-09: `grep -rn "sk-ant\|api_key.*=" src/` returns 0 matches.
- [ ] Verify AC-10: cost report table printed before exit in all sample runs.
- [ ] Add `examples/` directory and files to git.
- [ ] Git commit: `examples: add sample debate output and acceptance verification results`.

### 4.6 Release Tagging

- [ ] Run full unit test suite: `uv run pytest` — confirm all green.
- [ ] Run full integration suite: `uv run pytest -m slow` — confirm all green.
- [ ] Run `uv run ruff check .` — confirm 0 violations (final check).
- [ ] Run `uv run pytest --cov=src --cov-fail-under=85` — confirm passes (final check).
- [ ] Review git log: confirm every commit follows `type: description` convention.
- [ ] Confirm `docs/PRD.md` reflects all implemented features accurately.
- [ ] Confirm `docs/PLAN.md` class diagram matches actual class hierarchy in `src/`.
- [ ] Confirm all tasks in `docs/TODO.md` are checked off.
- [ ] Create git tag: `git tag v1.0.0`.
- [ ] Git commit: `release: v1.0.0 — AI Debate System complete`.

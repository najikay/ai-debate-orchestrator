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

- [x] Install `uv` globally via the official installer script.
- [x] Verify `uv --version` outputs 0.4.0 or higher.
- [x] Run `uv init` in the project root to generate `pyproject.toml`.
- [x] Confirm `pyproject.toml` was created and is syntactically valid TOML.
- [x] Set `name = "ai-debate-system"` in `pyproject.toml`.
- [x] Set `version = "0.1.0"` and `requires-python = ">=3.11"` in `pyproject.toml`.
- [x] Set `description` and `authors = [{name = "NajAmjad"}]` in `pyproject.toml`.
- [x] Add `anthropic`, `jsonschema`, `python-dotenv`, `requests` to `[project.dependencies]`.
- [x] Add `[project.optional-dependencies]` dev section with `ruff`, `pytest`, `pytest-cov`.
- [x] Add `[tool.ruff]` with `line-length = 88` and `[tool.ruff.lint]` with `select = ["E","W","F","I"]`.
- [x] Add `[tool.pytest.ini_options]` with `testpaths`, `addopts = "--cov=src --cov-fail-under=85"`.
- [x] Run `uv sync` and confirm `.venv/` is created.
- [x] Run `uv run python --version` — confirm Python 3.11+.
- [x] Run `uv run ruff --version` — confirm ruff is available.
- [x] Run `uv run pytest --version` — confirm pytest is available.
- [x] Run `uv run python -c "import anthropic; import jsonschema"` — confirm imports work.

### 0.2 Directory Structure & __init__ Files

- [x] Create directories: `src/`, `src/agents/`, `src/engine/`, `src/infrastructure/`, `src/schemas/`, `src/skills/`, `src/ui/`.
- [x] Create directories: `tests/`, `tests/unit/`, `tests/integration/`, `config/`, `examples/`.
- [x] Create `src/__init__.py`, `src/agents/__init__.py`, `src/engine/__init__.py` as empty files.
- [x] Create `src/infrastructure/__init__.py`, `src/skills/__init__.py`, `src/ui/__init__.py` as empty files.
- [x] Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` as empty files.
- [x] Verify all `__init__.py` files are empty (0 bytes).

### 0.3 .gitignore

- [x] Create `.gitignore` in project root.
- [x] Add `.env`, `logs/`, `__pycache__/`, `.venv/`, `*.pyc`, `*.pyo` to `.gitignore`.
- [x] Add `.coverage`, `htmlcov/`, `.pytest_cache/`, `dist/`, `*.egg-info/` to `.gitignore`.
- [x] Add `.idea/`, `.vscode/` to `.gitignore`.
- [x] Verify `git status` does not show `.venv/` or `logs/` as untracked.

### 0.4 .env-example

- [x] Create `.env-example` with comment block `# Anthropic Claude API`.
- [x] Add `ANTHROPIC_API_KEY=your_anthropic_key_here` to `.env-example`.
- [x] Add `SEARCH_API_KEY=your_search_key_here` to `.env-example`.
- [x] Add `SEARCH_BASE_URL=https://api.example.com/search` to `.env-example`.
- [x] Copy `.env-example` to local `.env` and fill real API keys (do NOT commit `.env`).
- [x] Confirm `.env` is listed in `.gitignore` and will not be staged.

### 0.5 config/setup.json

- [x] Create `config/setup.json` with `schema_version`, `debate`, `agents`, `watchdog`, `logging`, `enabled_skills` top-level keys.
- [x] Set `debate.min_turns_per_side = 10` and `debate.max_session_cost_usd = 2.00`.
- [x] Set agent models: `father = "claude-sonnet-4-6"`, `pro_son = con_son = "claude-haiku-4-5"`.
- [x] Set `watchdog.timeout_seconds = 30` and `watchdog.max_retries = 1`.
- [x] Set `logging.log_dir = "logs/"`, `logging.max_files = 20`, `logging.max_lines_per_file = 500`.
- [x] Set `enabled_skills = ["web_search"]`.
- [x] Validate `setup.json` is valid JSON: `python -m json.tool config/setup.json`.

### 0.6 config/rate_limits.json

- [x] Create `config/rate_limits.json` with `schema_version` field.
- [x] Add `models.claude-sonnet-4-6: {rpm: 50, tpm: 40000}` and `models.claude-haiku-4-5: {rpm: 100, tpm: 100000}`.
- [x] Add `web_search: {rpm: 30}`.
- [x] Validate `rate_limits.json` is valid JSON.

### 0.7 config/pricing.json

- [x] Create `config/pricing.json` with `schema_version` field.
- [x] Add `models.claude-sonnet-4-6` and `models.claude-haiku-4-5` entries with `input_per_1k` and `output_per_1k` USD values.
- [x] Validate `pricing.json` is valid JSON.

### 0.8 JSON Schema Files

- [x] Create `src/schemas/debate_message.json` with `$schema`, `type: object`, and `required` array.
- [x] Add all 8 properties: `message_id` (uuid), `sender` (enum), `recipient` (enum), `turn` (int ≥1), `content` (string), `sources` (array), `token_count` (int ≥0), `timestamp` (date-time).
- [x] Validate `debate_message.json` with `python -c "import jsonschema, json; jsonschema.Draft7Validator(json.load(open('src/schemas/debate_message.json')))"`.
- [x] Create `src/schemas/verdict.json` with `required` array.
- [x] Add all 6 properties: `verdict_id` (uuid), `winner` (enum: pro_son|con_son), `draw` (const: false), `reasoning` (string ≥50), `turn_count` (int ≥20), `timestamp` (date-time).
- [x] Validate `verdict.json` with `python -c "import jsonschema, json; jsonschema.Draft7Validator(json.load(open('src/schemas/verdict.json')))"`.

### 0.9 Test Configuration

- [x] Create `tests/conftest.py` with `slow` custom mark definition.
- [x] Register `slow` marker in `pyproject.toml` under `[tool.pytest.ini_options]`.
- [x] Create `tests/integration/conftest.py` with `pytestmark = pytest.mark.slow`.

### 0.10 Initial README & First Commit

- [x] Create `README.md` with title, group name, one-paragraph overview, and placeholder sections.
- [x] Stage all Phase 0 files: `git add .`.
- [x] Git commit: `chore: scaffold project structure and configuration files`.

---

## Phase 1 — Infrastructure Layer

### 1.1 ConfigLoader

- [x] Create `src/infrastructure/config_loader.py`.
- [x] Add imports: `import json`, `import os`, `from pathlib import Path`, `from typing import Any`.
- [x] Define `ConfigVersionError(Exception)` class in `config_loader.py`.
- [x] Create `tests/unit/test_config_loader.py`.
- [x] Add imports: `import pytest`, `from src.infrastructure.config_loader import ConfigLoader, ConfigVersionError`.
- [x] Define `tmp_config_dir` fixture: temp dir pre-populated with valid JSON config files.
- [x] Define `valid_setup_data` fixture: minimal valid setup dict.
- [x] Write failing test: `test_config_loader_init_sets_config_dir` — asserts `loader.config_dir` is set.
- [x] Implement `ConfigLoader.__init__(self, config_dir: str)` with Google-style docstring.
- [x] Run `uv run pytest tests/unit/test_config_loader.py::test_config_loader_init_sets_config_dir` — confirm pass.
- [x] Write failing test: `test_load_setup_returns_dict` — happy path, valid `setup.json`.
- [x] Implement `ConfigLoader.load_setup(self) -> dict`.
- [x] Write failing test: `test_load_setup_raises_file_not_found` — `setup.json` absent.
- [x] Implement `FileNotFoundError` handling in `load_setup`.
- [x] Write failing test: `test_load_setup_raises_on_invalid_json` — file contains malformed JSON.
- [x] Implement `json.JSONDecodeError` handling in `load_setup`.
- [x] Run `uv run pytest` on all `load_setup` tests — confirm all pass.
- [x] Write failing test: `test_load_rate_limits_returns_dict` — happy path.
- [x] Implement `ConfigLoader.load_rate_limits(self) -> dict`.
- [x] Write failing test: `test_load_rate_limits_raises_file_not_found`.
- [x] Implement `FileNotFoundError` handling in `load_rate_limits`.
- [x] Run `uv run pytest` on all `load_rate_limits` tests — confirm all pass.
- [x] Write failing test: `test_load_pricing_returns_dict` — happy path.
- [x] Implement `ConfigLoader.load_pricing(self) -> dict`.
- [x] Write failing test: `test_load_pricing_raises_file_not_found`.
- [x] Implement `FileNotFoundError` handling in `load_pricing`.
- [x] Run `uv run pytest` on all `load_pricing` tests — confirm all pass.
- [x] Write failing test: `test_validate_schema_version_passes_on_matching_version`.
- [x] Write failing test: `test_validate_schema_version_raises_config_version_error_on_mismatch`.
- [x] Implement `ConfigLoader._validate_schema_version(self, data: dict, expected: str) -> None`.
- [x] Run `uv run pytest` on all `_validate_schema_version` tests — confirm all pass.
- [x] Write failing test: `test_load_all_populates_setup_rate_limits_and_pricing`.
- [x] Implement `ConfigLoader.load_all(self) -> None` calling all three loaders.
- [x] Write failing test: `test_load_all_raises_config_version_error_on_bad_schema_version`.
- [x] Implement version validation inside `load_all`.
- [x] Run `uv run pytest` on all `load_all` tests — confirm all pass.
- [x] Run `uv run ruff check src/infrastructure/config_loader.py` — confirm 0 violations.
- [x] Run `wc -l src/infrastructure/config_loader.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement ConfigLoader with schema version validation`.

### 1.2 LoggerManager

- [x] Create `src/infrastructure/logger_manager.py`.
- [x] Add imports: `import logging`, `from datetime import datetime, timezone`, `from pathlib import Path`, `import os`.
- [x] Create `tests/unit/test_logger_manager.py`.
- [x] Add imports: `import pytest`, `from pathlib import Path`, `from src.infrastructure.logger_manager import LoggerManager`.
- [x] Define `tmp_log_dir` fixture using `tmp_path` pytest built-in.
- [x] Define `logger` fixture: `LoggerManager(tmp_log_dir, max_files=5, max_lines=10)`.
- [x] Write failing test: `test_logger_manager_init_creates_log_dir` — directory exists after init.
- [x] Implement `LoggerManager.__init__(self, log_dir: str, max_files: int, max_lines: int)` with Google-style docstring.
- [x] Run `uv run pytest tests/unit/test_logger_manager.py::test_logger_manager_init_creates_log_dir` — confirm pass.
- [x] Write failing test: `test_write_creates_log_file` — first `write()` creates a `.log` file.
- [x] Implement `LoggerManager.write(self, level: str, component: str, message: str) -> None`.
- [x] Write failing test: `test_write_format_matches_spec` — line format is `ISO | LEVEL | COMPONENT | MESSAGE`.
- [x] Implement log-line format enforcement in `write`.
- [x] Write failing test: `test_write_rejects_unknown_level` — invalid level string raises `ValueError`.
- [x] Implement level validation (DEBUG/INFO/WARNING/ERROR) in `write`.
- [x] Run `uv run pytest` on all `write` tests — confirm all pass.
- [x] Write failing test: `test_get_current_file_returns_existing_path`.
- [x] Implement `LoggerManager._get_current_file(self) -> Path`.
- [x] Write failing test: `test_get_current_file_opens_new_file_after_line_limit` — 10 lines written (fixture limit), next write goes to new file.
- [x] Implement line-count check and new-file creation in `_get_current_file`.
- [x] Run `uv run pytest` on all `_get_current_file` tests — confirm all pass.
- [x] Write failing test: `test_rotate_deletes_oldest_file_when_max_files_exceeded` — 5-file fixture limit, sixth file triggers eviction.
- [x] Implement `LoggerManager._rotate(self) -> None` with FIFO eviction logic.
- [x] Write failing test: `test_rotate_does_not_delete_when_below_max_files_limit`.
- [x] Implement below-limit guard in `_rotate`.
- [x] Run `uv run pytest` on all `_rotate` tests — confirm all pass.
- [x] Run `uv run ruff check src/infrastructure/logger_manager.py` — confirm 0 violations.
- [x] Run `wc -l src/infrastructure/logger_manager.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement LoggerManager with FIFO rotation`.

### 1.3 Gatekeeper

- [x] Create `src/infrastructure/gatekeeper.py`.
- [x] Add imports: `import threading`, `from collections import deque`, `import time`, `from dataclasses import dataclass, field`, `from typing import Any`.
- [x] Define `QueueFullError(Exception)` in `gatekeeper.py`.
- [x] Define `APIRequest` dataclass (agent_id, model, payload) in `gatekeeper.py`.
- [x] Define `APIResponse` dataclass (content, prompt_tokens, completion_tokens) in `gatekeeper.py`.
- [x] Define `UsageStats` dataclass (prompt_tokens, completion_tokens, total_tokens) in `gatekeeper.py`.
- [x] Create `tests/unit/test_gatekeeper.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import patch, MagicMock`.
- [x] Add `from src.infrastructure.gatekeeper import Gatekeeper, QueueFullError, APIRequest, APIResponse, UsageStats`.
- [x] Define `mock_rate_limits` fixture with low rpm/tpm for fast testing.
- [x] Define `gatekeeper` fixture initialised with `mock_rate_limits`.
- [x] Define `sample_request` fixture as a valid `APIRequest` object.
- [x] Write failing test: `test_gatekeeper_init_creates_empty_queue`.
- [x] Write failing test: `test_gatekeeper_init_stores_rate_limits`.
- [x] Implement `Gatekeeper.__init__(self, rate_limits: dict)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_dispatch_returns_api_response` — mocked HTTP, happy path.
- [x] Implement `Gatekeeper.dispatch(self, request: APIRequest) -> APIResponse`.
- [x] Write failing test: `test_dispatch_records_token_usage_for_agent`.
- [x] Implement token-usage recording in `dispatch`.
- [x] Write failing test: `test_dispatch_queues_request_when_rate_limit_enforced`.
- [x] Implement queue insertion path in `dispatch`.
- [x] Run `uv run pytest` on all `dispatch` tests — confirm all pass.
- [x] Write failing test: `test_enforce_limits_blocks_when_rpm_bucket_depleted`.
- [x] Implement `Gatekeeper._enforce_limits(self, model: str) -> None` with token-bucket logic.
- [x] Write failing test: `test_enforce_limits_allows_call_within_rpm`.
- [x] Run `uv run pytest` on all `_enforce_limits` tests — confirm all pass.
- [x] Write failing test: `test_enqueue_adds_request_to_deque`.
- [x] Implement `Gatekeeper._enqueue(self, request: APIRequest) -> None`.
- [x] Write failing test: `test_enqueue_raises_queue_full_error_when_depth_exceeds_50`.
- [x] Implement depth-50 guard and `QueueFullError` raise in `_enqueue`.
- [x] Run `uv run pytest` on all `_enqueue` tests — confirm all pass.
- [x] Write failing test: `test_dequeue_returns_oldest_request_fifo`.
- [x] Implement `Gatekeeper._dequeue(self) -> APIRequest`.
- [x] Write failing test: `test_dequeue_raises_when_queue_is_empty`.
- [x] Implement empty-queue guard in `_dequeue`.
- [x] Run `uv run pytest` on all `_dequeue` tests — confirm all pass.
- [x] Write failing test: `test_get_usage_returns_correct_stats_for_known_agent`.
- [x] Implement `Gatekeeper.get_usage(self, agent_id: str) -> UsageStats`.
- [x] Write failing test: `test_get_usage_returns_zero_stats_for_unknown_agent`.
- [x] Implement zero-default for unknown agents in `get_usage`.
- [x] Write failing test: `test_gatekeeper_is_thread_safe` — concurrent dispatches do not corrupt usage totals.
- [x] Verify `threading.Lock` guards `dispatch` and `get_usage`.
- [x] Run `uv run pytest` on all `get_usage` and thread-safety tests — confirm all pass.
- [x] Run `uv run ruff check src/infrastructure/gatekeeper.py` — confirm 0 violations.
- [x] Run `wc -l src/infrastructure/gatekeeper.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement Gatekeeper with token-bucket rate limiting and FIFO queue`.

### 1.4 Watchdog

- [x] Create `src/infrastructure/watchdog.py`.
- [x] Add imports: `import concurrent.futures`, `import logging`, `from typing import Any, Callable`.
- [x] Define `WatchdogError(Exception)` in `watchdog.py`.
- [x] Create `tests/unit/test_watchdog.py`.
- [x] Add imports: `import pytest`, `import time`, `from src.infrastructure.watchdog import Watchdog, WatchdogError`.
- [x] Define `fast_watchdog` fixture: `Watchdog(timeout_seconds=0.05, max_retries=1)`.
- [x] Write failing test: `test_watchdog_init_sets_timeout_seconds`.
- [x] Write failing test: `test_watchdog_init_sets_max_retries`.
- [x] Implement `Watchdog.__init__(self, timeout_seconds: int, max_retries: int)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_run_returns_result_when_function_completes_within_timeout`.
- [x] Implement `Watchdog.run(self, fn: Callable, args: dict) -> Any`.
- [x] Write failing test: `test_run_retries_once_on_first_timeout` — fn sleeps > timeout on first call, succeeds on retry.
- [x] Implement retry logic inside `run`.
- [x] Write failing test: `test_run_raises_watchdog_error_on_two_consecutive_timeouts`.
- [x] Implement `WatchdogError` raise after max retries exceeded.
- [x] Run `uv run pytest` on all `run` tests — confirm all pass.
- [x] Write failing test: `test_kill_and_retry_cancels_the_timed_out_future`.
- [x] Implement `Watchdog._kill_and_retry(self, fn: Callable, args: dict) -> Any`.
- [x] Write failing test: `test_kill_and_retry_emits_warning_log_on_each_timeout`.
- [x] Implement `logging.warning(...)` call in `_kill_and_retry`.
- [x] Run `uv run pytest` on all `_kill_and_retry` tests — confirm all pass.
- [x] Run `uv run ruff check src/infrastructure/watchdog.py` — confirm 0 violations.
- [x] Run `wc -l src/infrastructure/watchdog.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement Watchdog with thread-pool timeout and retry logic`.

### 1.5 CostReporter

- [x] Create `src/infrastructure/cost_reporter.py`.
- [x] Add imports: `from dataclasses import dataclass, field`, `from typing import Dict`.
- [x] Define `AgentUsage` dataclass (prompt_tokens, completion_tokens, model) in `cost_reporter.py`.
- [x] Define `CostSummary` dataclass (per_agent, total_usd, budget_cap_usd, utilisation_pct) in `cost_reporter.py`.
- [x] Create `tests/unit/test_cost_reporter.py`.
- [x] Add imports: `import pytest`, `from src.infrastructure.cost_reporter import CostReporter, CostSummary`.
- [x] Define `mock_pricing` fixture with known per-token USD rates.
- [x] Define `cost_reporter` fixture: `CostReporter(mock_pricing, budget_cap_usd=2.00)`.
- [x] Write failing test: `test_cost_reporter_init_stores_pricing`.
- [x] Write failing test: `test_cost_reporter_init_stores_budget_cap`.
- [x] Implement `CostReporter.__init__(self, pricing: dict, budget_cap_usd: float)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_record_usage_accumulates_prompt_tokens_for_agent`.
- [x] Implement `CostReporter.record_usage(self, agent_id: str, model: str, prompt_tokens: int, completion_tokens: int) -> None`.
- [x] Write failing test: `test_record_usage_creates_new_entry_for_first_call_per_agent`.
- [x] Implement new-agent-entry creation in `record_usage`.
- [x] Write failing test: `test_record_usage_accumulates_tokens_across_multiple_calls`.
- [x] Verify token accumulation is additive in `record_usage`.
- [x] Run `uv run pytest` on all `record_usage` tests — confirm all pass.
- [x] Write failing test: `test_compute_returns_correct_total_usd_for_known_inputs`.
- [x] Implement `CostReporter.compute(self) -> CostSummary`.
- [x] Write failing test: `test_compute_per_agent_costs_sum_to_session_total`.
- [x] Implement per-agent cost breakdown in `compute`.
- [x] Write failing test: `test_compute_returns_zero_summary_when_no_usage_recorded`.
- [x] Implement zero-usage guard in `compute`.
- [x] Write failing test: `test_compute_calculates_utilisation_pct_correctly` — known cost / cap × 100.
- [x] Implement utilisation percentage in `compute`.
- [x] Run `uv run pytest` on all `compute` tests — confirm all pass.
- [x] Write failing test: `test_print_report_writes_non_empty_output_to_stdout`.
- [x] Implement `CostReporter.print_report(self, summary: CostSummary) -> None`.
- [x] Write failing test: `test_print_report_output_contains_each_agent_name`.
- [x] Write failing test: `test_print_report_output_contains_total_usd_line`.
- [x] Write failing test: `test_print_report_output_contains_budget_utilisation_percentage`.
- [x] Run `uv run pytest` on all `print_report` tests — confirm all pass.
- [x] Run `uv run ruff check src/infrastructure/cost_reporter.py` — confirm 0 violations.
- [x] Run `wc -l src/infrastructure/cost_reporter.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement CostReporter with per-agent USD breakdown`.

---

## Phase 2 — Agent SDK & Tools Layer

### 2.1 AgentSkill ABC

- [x] Create `src/skills/base_skill.py`.
- [x] Add imports: `from abc import ABC, abstractmethod`, `from dataclasses import dataclass`.
- [x] Define `SkillError(Exception)` class in `base_skill.py`.
- [x] Define `SkillResult` dataclass: fields `query: str`, `snippets: list[str]`, `raw_response: dict`.
- [x] Define `AgentSkill(ABC)` with `skill_name: str` attribute and `@abstractmethod execute(query: str) -> SkillResult`.
- [x] Create `tests/unit/test_base_skill.py`.
- [x] Add imports: `import pytest`, `from src.skills.base_skill import AgentSkill, SkillResult, SkillError`.
- [x] Write failing test: `test_agent_skill_cannot_be_instantiated_directly` — raises `TypeError`.
- [x] Write failing test: `test_concrete_subclass_missing_execute_is_still_abstract`.
- [x] Write failing test: `test_concrete_subclass_with_execute_is_instantiable`.
- [x] Write failing test: `test_skill_result_dataclass_has_query_snippets_raw_response_fields`.
- [x] Write failing test: `test_skill_error_is_subclass_of_exception`.
- [x] Run `uv run pytest tests/unit/test_base_skill.py` — confirm all pass.
- [x] Run `uv run ruff check src/skills/base_skill.py` — confirm 0 violations.
- [x] Run `wc -l src/skills/base_skill.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement AgentSkill ABC and SkillResult dataclass`.

### 2.2 WebSearchTool


- [x] Create `src/skills/web_search_tool.py`.
- [x] Add imports: `import os`, `import requests`, `from src.skills.base_skill import AgentSkill, SkillResult, SkillError`.
- [x] Create `tests/unit/test_web_search_tool.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import patch, MagicMock`.
- [x] Add `from src.skills.web_search_tool import WebSearchTool`.
- [x] Define `mock_search_response` fixture: valid search API JSON dict.
- [x] Define `web_search_tool` fixture with env vars patched via `monkeypatch`.
- [x] Write failing test: `test_web_search_tool_init_reads_api_key_from_env`.
- [x] Write failing test: `test_web_search_tool_init_reads_base_url_from_env`.
- [x] Implement `WebSearchTool.__init__(self, api_key: str, base_url: str)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_sanitize_strips_leading_and_trailing_whitespace`.
- [x] Implement `WebSearchTool._sanitize(self, query: str) -> str`.
- [x] Write failing test: `test_sanitize_truncates_query_to_200_characters`.
- [x] Implement 200-char truncation in `_sanitize`.
- [x] Write failing test: `test_sanitize_returns_empty_string_for_whitespace_only_input`.
- [x] Implement whitespace-only guard in `_sanitize`.
- [x] Run `uv run pytest` on all `_sanitize` tests — confirm all pass.
- [x] Write failing test: `test_parse_response_returns_skill_result_with_non_empty_snippets`.
- [x] Implement `WebSearchTool._parse_response(self, raw: dict) -> SkillResult`.
- [x] Write failing test: `test_parse_response_raises_skill_error_on_missing_results_key`.
- [x] Implement missing-key guard in `_parse_response`.
- [x] Write failing test: `test_parse_response_raises_skill_error_on_empty_results_list`.
- [x] Implement empty-results guard in `_parse_response`.
- [x] Run `uv run pytest` on all `_parse_response` tests — confirm all pass.
- [x] Write failing test: `test_execute_returns_skill_result_on_http_200` — mocked happy path.
- [x] Implement `WebSearchTool.execute(self, query: str) -> SkillResult`.
- [x] Write failing test: `test_execute_calls_sanitize_before_dispatching_query`.
- [x] Verify `_sanitize` is invoked inside `execute`.
- [x] Write failing test: `test_execute_raises_skill_error_on_http_500`.
- [x] Implement HTTP-5xx error handling in `execute`.
- [x] Write failing test: `test_execute_raises_skill_error_on_http_429`.
- [x] Implement HTTP-429 handling in `execute`.
- [x] Write failing test: `test_execute_raises_skill_error_on_requests_timeout`.
- [x] Implement `requests.Timeout` handling in `execute`.
- [x] Run `uv run pytest` on all `execute` tests — confirm all pass.
- [x] Create `tests/integration/test_web_search_integration.py` marked `@pytest.mark.slow`.
- [x] Write integration test: `test_web_search_live_returns_non_empty_snippets`.
- [x] Run `uv run ruff check src/skills/web_search_tool.py` — confirm 0 violations.
- [x] Run `wc -l src/skills/web_search_tool.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement WebSearchTool with sanitization and error handling`.

### 2.2b Local Logic Analyzer Tool

- [x] Create `src/skills/logic_analyzer_tool.py`.
- [x] Inherit from `AgentSkill`; `skill_name = "logic_analyzer"`.
- [x] Implement `execute(query: str) -> SkillResult` — purely local string analysis (no network calls).
- [x] Count premise keywords (because, since, given that, as, if) and conclusion keywords (therefore, thus, hence, so, consequently).
- [x] Return `SkillResult` with `snippets` containing a rubric summary (keyword counts, word count, sentence count, avg sentence length).
- [x] Create `tests/unit/test_logic_analyzer_tool.py`.
- [x] Write failing test: `test_logic_analyzer_skill_name_is_logic_analyzer`.
- [x] Write failing test: `test_execute_returns_skill_result`.
- [x] Write failing test: `test_execute_snippets_are_non_empty`.
- [x] Write failing test: `test_execute_detects_premise_keywords`.
- [x] Write failing test: `test_execute_detects_conclusion_keywords`.
- [x] Write failing test: `test_execute_counts_words`.
- [x] Write failing test: `test_execute_empty_query_returns_result_without_raising`.
- [x] Write failing test: `test_execute_makes_no_network_calls` — patch `socket.getaddrinfo` to confirm it is never called.
- [x] Run `uv run pytest tests/unit/test_logic_analyzer_tool.py` — confirm all pass.
- [x] Run `uv run ruff check src/skills/logic_analyzer_tool.py` — confirm 0 violations.
- [x] Run `wc -l src/skills/logic_analyzer_tool.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement offline LogicAnalyzerTool`.

### 2.3 BaseAgent ABC

- [x] Create `src/agents/base_agent.py`.
- [x] Add imports: `import json`, `from abc import ABC, abstractmethod`, `import jsonschema`, `from pathlib import Path`.
- [x] Add `from src.infrastructure.gatekeeper import Gatekeeper, APIRequest`.
- [x] Define `MessageParseError(Exception)` in `base_agent.py`.
- [x] Define `AgentFailureError(Exception)` in `base_agent.py`.
- [x] Define `DebateMessage` dataclass in `base_agent.py` with all 8 fields from schema.
- [x] Create `tests/unit/test_base_agent.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [x] Add `from src.agents.base_agent import BaseAgent, MessageParseError, AgentFailureError, DebateMessage`.
- [x] Define `mock_gatekeeper` fixture as `MagicMock(spec=Gatekeeper)`.
- [x] Define `mock_config` fixture with minimal agent config dict.
- [x] Define `ConcreteAgent` helper subclass (implements all abstract methods) inside test file.
- [x] Define `concrete_agent` fixture instantiating `ConcreteAgent`.
- [x] Write failing test: `test_base_agent_cannot_be_instantiated_directly` — raises `TypeError`.
- [x] Write failing test: `test_base_agent_init_sets_agent_id`.
- [x] Write failing test: `test_base_agent_init_sets_role`.
- [x] Write failing test: `test_base_agent_init_stores_gatekeeper_reference`.
- [x] Implement `BaseAgent.__init__(self, agent_id: str, role: str, gatekeeper: Gatekeeper, config: dict)` with Google-style docstring.
- [x] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [x] Write failing test: `test_parse_response_returns_debate_message_on_valid_json`.
- [x] Implement `BaseAgent.parse_response(self, raw: str) -> DebateMessage`.
- [x] Write failing test: `test_parse_response_raises_message_parse_error_on_invalid_json`.
- [x] Implement `json.JSONDecodeError` handling in `parse_response`.
- [x] Write failing test: `test_parse_response_raises_message_parse_error_on_schema_violation`.
- [x] Implement `jsonschema.ValidationError` handling in `parse_response`.
- [x] Run `uv run pytest` on all `parse_response` tests — confirm all pass.
- [x] Write failing test: `test_validate_schema_returns_true_on_valid_message_dict`.
- [x] Implement `BaseAgent._validate_schema(self, msg: dict) -> bool`.
- [x] Write failing test: `test_validate_schema_returns_false_on_missing_required_field`.
- [x] Write failing test: `test_validate_schema_returns_false_on_wrong_sender_enum_value`.
- [x] Run `uv run pytest` on all `_validate_schema` tests — confirm all pass.
- [x] Write failing test: `test_call_api_dispatches_through_gatekeeper`.
- [x] Implement `BaseAgent.call_api(self, prompt: str) -> str`.
- [x] Write failing test: `test_call_api_uses_model_from_config_dict`.
- [x] Implement model lookup from `self.config` in `call_api`.
- [x] Write failing test: `test_call_api_includes_agent_id_in_request`.
- [x] Verify `agent_id` is included in the `APIRequest` object.
- [x] Run `uv run pytest` on all `call_api` tests — confirm all pass.
- [x] Run `uv run ruff check src/agents/base_agent.py` — confirm 0 violations.
- [x] Run `wc -l src/agents/base_agent.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement BaseAgent ABC with JSON schema validation`.

### 2.4 ProSonAgent

- [x] Create `src/agents/pro_son_agent.py`.
- [x] Add imports: `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError, AgentFailureError`.
- [x] Add `from src.skills.base_skill import AgentSkill`.
- [x] Create `tests/unit/test_pro_son_agent.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [x] Add `from src.agents.pro_son_agent import ProSonAgent`.
- [x] Define `mock_gatekeeper` fixture for pro son tests.
- [x] Define `mock_skill` fixture as `MagicMock(spec=AgentSkill)`.
- [x] Define `pro_son_config` fixture with model and agent_id fields.
- [x] Define `pro_son_agent` fixture instantiating `ProSonAgent`.
- [x] Write failing test: `test_pro_son_init_sets_position_attribute_to_pro`.
- [x] Write failing test: `test_pro_son_init_stores_skills_list`.
- [x] Implement `ProSonAgent.__init__(self, config: dict, gatekeeper, skills: list)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_build_prompt_returns_non_empty_string`.
- [x] Implement `ProSonAgent.build_prompt(self, context) -> str`.
- [x] Write failing test: `test_build_prompt_contains_pro_position_instruction`.
- [x] Implement pro-position instruction injection in `build_prompt`.
- [x] Write failing test: `test_build_prompt_embeds_topic_from_debate_state`.
- [x] Run `uv run pytest` on all `build_prompt` tests — confirm all pass.
- [x] Write failing test: `test_enforce_position_returns_content_unchanged_for_pro_argument`.
- [x] Implement `ProSonAgent._enforce_position(self, content: str) -> str`.
- [x] Write failing test: `test_enforce_position_raises_retry_signal_when_con_stance_detected`.
- [x] Implement con-content detection and retry signal in `_enforce_position`.
- [x] Run `uv run pytest` on all `_enforce_position` tests — confirm all pass.
- [x] Write failing test: `test_generate_argument_returns_valid_debate_message` — mocked API, happy path.
- [x] Implement `ProSonAgent.generate_argument(self, prompt: DebateMessage) -> DebateMessage`.
- [x] Write failing test: `test_generate_argument_sources_field_is_non_empty`.
- [x] Implement sources enforcement (web search results embedded) in `generate_argument`.
- [x] Write failing test: `test_generate_argument_retries_up_to_2_times_on_position_violation`.
- [x] Implement max-2-retries logic in `generate_argument`.
- [x] Write failing test: `test_generate_argument_raises_agent_failure_error_after_2_retries`.
- [x] Implement `AgentFailureError` raise after retries exhausted.
- [x] Run `uv run pytest` on all `generate_argument` tests — confirm all pass.
- [x] Run `uv run ruff check src/agents/pro_son_agent.py` — confirm 0 violations.
- [x] Run `wc -l src/agents/pro_son_agent.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement ProSonAgent with position enforcement and retry`.

### 2.5 ConSonAgent

- [x] Create `src/agents/con_son_agent.py`.
- [x] Add imports: `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError, AgentFailureError`.
- [x] Add `from src.skills.base_skill import AgentSkill`.
- [x] Create `tests/unit/test_con_son_agent.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [x] Add `from src.agents.con_son_agent import ConSonAgent`.
- [x] Define `mock_gatekeeper` fixture for con son tests.
- [x] Define `mock_skill` fixture as `MagicMock(spec=AgentSkill)`.
- [x] Define `con_son_config` fixture with model and agent_id fields.
- [x] Define `con_son_agent` fixture instantiating `ConSonAgent`.
- [x] Write failing test: `test_con_son_init_sets_position_attribute_to_con`.
- [x] Write failing test: `test_con_son_init_stores_skills_list`.
- [x] Implement `ConSonAgent.__init__(self, config: dict, gatekeeper, skills: list)` with Google-style docstring.
- [x] Run `uv run pytest` on both `__init__` tests — confirm all pass.
- [x] Write failing test: `test_build_prompt_returns_non_empty_string`.
- [x] Implement `ConSonAgent.build_prompt(self, context) -> str`.
- [x] Write failing test: `test_build_prompt_contains_con_position_instruction`.
- [x] Implement con-position instruction injection in `build_prompt`.
- [x] Write failing test: `test_build_prompt_embeds_topic_from_debate_state`.
- [x] Run `uv run pytest` on all `build_prompt` tests — confirm all pass.
- [x] Write failing test: `test_enforce_position_returns_content_unchanged_for_con_argument`.
- [x] Implement `ConSonAgent._enforce_position(self, content: str) -> str`.
- [x] Write failing test: `test_enforce_position_raises_retry_signal_when_pro_stance_detected`.
- [x] Implement pro-content detection and retry signal in `_enforce_position`.
- [x] Run `uv run pytest` on all `_enforce_position` tests — confirm all pass.
- [x] Write failing test: `test_generate_argument_returns_valid_debate_message` — mocked API, happy path.
- [x] Implement `ConSonAgent.generate_argument(self, prompt: DebateMessage) -> DebateMessage`.
- [x] Write failing test: `test_generate_argument_sources_field_is_non_empty`.
- [x] Implement sources enforcement in `generate_argument`.
- [x] Write failing test: `test_generate_argument_retries_up_to_2_times_on_position_violation`.
- [x] Implement max-2-retries logic in `generate_argument`.
- [x] Write failing test: `test_generate_argument_raises_agent_failure_error_after_2_retries`.
- [x] Implement `AgentFailureError` raise after retries exhausted.
- [x] Run `uv run pytest` on all `generate_argument` tests — confirm all pass.
- [x] Run `uv run ruff check src/agents/con_son_agent.py` — confirm 0 violations.
- [x] Run `wc -l src/agents/con_son_agent.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement ConSonAgent with position enforcement and retry`.

### 2.6 FatherAgent

- [x] Create `src/agents/father_agent.py`.
- [x] Add imports: `import json`, `import uuid`, `from datetime import datetime, timezone`.
- [x] Add `from src.agents.base_agent import BaseAgent, DebateMessage, MessageParseError`.
- [x] Define `NotEnoughTurnsError(Exception)` in `father_agent.py`.
- [x] Define `Verdict` dataclass with fields: `verdict_id`, `winner`, `draw`, `reasoning`, `turn_count`, `timestamp`.
- [x] Create `tests/unit/test_father_agent.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [x] Add `from src.agents.father_agent import FatherAgent, NotEnoughTurnsError, Verdict`.
- [x] Define `mock_gatekeeper` fixture for father tests.
- [x] Define `father_config` fixture with model and agent_id fields.
- [x] Define `father_agent` fixture instantiating `FatherAgent`.
- [x] Define `sample_debate_state` fixture with 20+ transcript messages.
- [x] Define `short_debate_state` fixture with only 10 messages.
- [x] Write failing test: `test_father_agent_init_sets_role_to_father`.
- [x] Implement `FatherAgent.__init__(self, config: dict, gatekeeper)` with Google-style docstring.
- [x] Run `uv run pytest` on `__init__` test — confirm pass.
- [x] Write failing test: `test_open_debate_returns_debate_message`.
- [x] Implement `FatherAgent.open_debate(self, topic: str) -> DebateMessage`.
- [x] Write failing test: `test_open_debate_sender_field_is_father`.
- [x] Write failing test: `test_open_debate_recipient_field_is_pro_son`.
- [x] Write failing test: `test_open_debate_message_id_is_valid_uuid`.
- [x] Implement all field constraints in `open_debate`.
- [x] Run `uv run pytest` on all `open_debate` tests — confirm all pass.
- [x] Write failing test: `test_validate_message_returns_true_on_complete_valid_message`.
- [x] Implement `FatherAgent._validate_message(self, msg: DebateMessage) -> bool`.
- [x] Write failing test: `test_validate_message_returns_false_on_missing_content`.
- [x] Implement missing-content detection in `_validate_message`.
- [x] Write failing test: `test_validate_message_returns_false_on_invalid_sender_value`.
- [x] Implement sender-enum validation in `_validate_message`.
- [x] Write failing test: `test_validate_message_returns_false_on_empty_sources_on_turn_divisible_by_3`.
- [x] Implement per-3-turn sources check in `_validate_message`.
- [x] Run `uv run pytest` on all `_validate_message` tests — confirm all pass.
- [x] Write failing test: `test_route_returns_pro_son_identifier_for_pro_son_recipient`.
- [x] Implement `FatherAgent.route(self, msg: DebateMessage) -> str`.
- [x] Write failing test: `test_route_returns_con_son_identifier_for_con_son_recipient`.
- [x] Implement con son routing branch.
- [x] Write failing test: `test_route_raises_value_error_on_invalid_recipient_value`.
- [x] Implement invalid-recipient guard in `route`.
- [x] Run `uv run pytest` on all `route` tests — confirm all pass.
- [x] Write failing test: `test_check_min_turns_returns_false_when_turn_count_is_19`.
- [x] Implement `FatherAgent._check_min_turns(self, state) -> bool`.
- [x] Write failing test: `test_check_min_turns_returns_true_when_turn_count_is_20`.
- [x] Write failing test: `test_check_min_turns_returns_true_when_turn_count_exceeds_20`.
- [x] Run `uv run pytest` on all `_check_min_turns` tests — confirm all pass.
- [x] Write failing test: `test_score_persuasiveness_returns_dict_with_pro_and_con_keys`.
- [x] Implement `FatherAgent._score_persuasiveness(self, transcript: list) -> dict`.
- [x] Write failing test: `test_score_persuasiveness_each_entry_has_clarity_evidence_logic_total`.
- [x] Implement rubric-dimension extraction (clarity, evidence, logic) in `_score_persuasiveness`.
- [x] Write failing test: `test_score_persuasiveness_uses_rubric_prompt_template_verbatim`.
- [x] Verify rubric prompt from PRD §9.3 is embedded unchanged in `_score_persuasiveness`.
- [x] Run `uv run pytest` on all `_score_persuasiveness` tests — confirm all pass.
- [x] Write failing test: `test_evaluate_raises_not_enough_turns_error_when_turn_count_below_20`.
- [x] Implement `FatherAgent.evaluate(self, state) -> Verdict`.
- [x] Write failing test: `test_evaluate_returns_verdict_with_draw_false`.
- [x] Implement `draw=False` enforcement in `evaluate`.
- [x] Write failing test: `test_evaluate_winner_is_exactly_pro_son_or_con_son`.
- [x] Implement winner-selection from rubric totals in `evaluate`.
- [x] Write failing test: `test_evaluate_reasoning_field_is_at_least_50_characters`.
- [x] Implement reasoning-length enforcement in `evaluate`.
- [x] Write failing test: `test_evaluate_applies_tiebreaker_when_total_scores_are_equal`.
- [x] Implement momentum tiebreaker (last 4 turns) in `evaluate`.
- [x] Run `uv run pytest` on all `evaluate` tests — confirm all pass.
- [x] Run `uv run ruff check src/agents/father_agent.py` — confirm 0 violations.
- [x] Run `wc -l src/agents/father_agent.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement FatherAgent with routing and persuasiveness evaluation`.

---

## Phase 3 — Debate Engine

### 3.1 StateManager

- [x] Create `src/engine/state_manager.py`.
- [x] Add imports: `import json`, `import uuid`, `from dataclasses import dataclass, field`, `from datetime import datetime, timezone`.
- [x] Define `DebateState` dataclass with all fields from PRD §4.3.
- [x] Create `tests/unit/test_state_manager.py`.
- [x] Add imports: `import pytest`, `from src.engine.state_manager import StateManager, DebateState`.
- [x] Define `state_manager` fixture: fresh `StateManager()`.
- [x] Define `sample_message` fixture: valid `DebateMessage` dict.
- [x] Define `sample_verdict` fixture: valid `Verdict` dict.
- [x] Write failing test: `test_state_manager_init_status_is_initialization`.
- [x] Write failing test: `test_state_manager_init_turn_count_is_zero`.
- [x] Write failing test: `test_state_manager_init_transcript_is_empty_list`.
- [x] Implement `StateManager.__init__(self)` with Google-style docstring.
- [x] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [x] Write failing test: `test_record_message_appends_to_transcript`.
- [x] Implement `StateManager.record_message(self, msg) -> None`.
- [x] Write failing test: `test_record_message_increments_turn_count_by_one`.
- [x] Implement turn-count increment in `record_message`.
- [x] Write failing test: `test_record_message_refreshes_updated_at_timestamp`.
- [x] Implement `updated_at` refresh in `record_message`.
- [x] Run `uv run pytest` on all `record_message` tests — confirm all pass.
- [x] Write failing test: `test_record_verdict_stores_verdict_object`.
- [x] Implement `StateManager.record_verdict(self, v) -> None`.
- [x] Write failing test: `test_record_verdict_raises_if_verdict_already_exists`.
- [x] Implement duplicate-verdict guard in `record_verdict`.
- [x] Run `uv run pytest` on all `record_verdict` tests — confirm all pass.
- [x] Write failing test: `test_get_turn_count_returns_zero_on_fresh_state`.
- [x] Write failing test: `test_get_turn_count_returns_correct_value_after_n_messages`.
- [x] Implement `StateManager.get_turn_count(self) -> int`.
- [x] Run `uv run pytest` on `get_turn_count` tests — confirm all pass.
- [x] Write failing test: `test_to_json_output_is_a_string`.
- [x] Implement `StateManager.to_json(self) -> str`.
- [x] Write failing test: `test_to_json_output_is_parseable_json`.
- [x] Write failing test: `test_to_json_includes_topic_and_turn_count_and_transcript`.
- [x] Run `uv run pytest` on all `to_json` tests — confirm all pass.
- [x] Write failing test: `test_from_json_restores_topic_field`.
- [x] Implement `StateManager.from_json(self, data: str) -> DebateState`.
- [x] Write failing test: `test_from_json_restores_turn_count`.
- [x] Write failing test: `test_from_json_restores_full_transcript_array`.
- [x] Write failing test: `test_from_json_raises_value_error_on_malformed_json`.
- [x] Implement JSON parse error handling in `from_json`.
- [x] Run `uv run pytest` on all `from_json` tests — confirm all pass.
- [x] Run `uv run ruff check src/engine/state_manager.py` — confirm 0 violations.
- [x] Run `wc -l src/engine/state_manager.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement StateManager with JSON serialization round-trip`.

### 3.2 DebateEngine

- [x] Create `src/engine/debate_engine.py`.
- [x] Add `import logging` to `debate_engine.py`.
- [x] Add imports for `FatherAgent`, `ProSonAgent`, `ConSonAgent`, `StateManager`, `Watchdog`, `WatchdogError`, `CostReporter`, `Gatekeeper`, `ConfigLoader`.
- [x] Create `tests/unit/test_debate_engine.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch, call`.
- [x] Add `from src.engine.debate_engine import DebateEngine`.
- [x] Define `mock_config` fixture with short turn limit for fast unit testing.
- [x] Define `mock_father`, `mock_pro_son`, `mock_con_son`, `mock_state_manager`, `mock_watchdog`, `mock_cost_reporter` fixtures.
- [x] Define `debate_engine` fixture wiring all mocks.
- [x] Write failing test: `test_debate_engine_init_creates_father_agent`.
- [x] Write failing test: `test_debate_engine_init_creates_pro_son_agent`.
- [x] Write failing test: `test_debate_engine_init_creates_con_son_agent`.
- [x] Write failing test: `test_debate_engine_init_creates_state_manager`.
- [x] Write failing test: `test_debate_engine_init_creates_watchdog_with_configured_timeout`.
- [x] Implement `DebateEngine.__init__(self, config: dict)` with Google-style docstring.
- [x] Run `uv run pytest` on all `__init__` tests — confirm all pass.
- [x] Write failing test: `test_run_turn_loop_executes_at_least_min_turns`.
- [x] Implement `DebateEngine._run_turn_loop(self) -> None`.
- [x] Write failing test: `test_run_turn_loop_alternates_pro_son_and_con_son_each_round`.
- [x] Implement alternation logic (pro → father → con → father) in `_run_turn_loop`.
- [x] Write failing test: `test_run_turn_loop_calls_record_message_after_every_turn`.
- [x] Implement `state_manager.record_message()` call in `_run_turn_loop`.
- [x] Write failing test: `test_run_turn_loop_routes_all_responses_through_father`.
- [x] Verify `father.route()` is called for each agent response.
- [x] Run `uv run pytest` on all `_run_turn_loop` tests — confirm all pass.
- [x] Write failing test: `test_check_budget_returns_false_when_cost_below_cap`.
- [x] Implement `DebateEngine._check_budget(self) -> bool`.
- [x] Write failing test: `test_check_budget_returns_true_when_cost_exceeds_cap`.
- [x] Implement cost-cap comparison using `CostReporter.compute()`.
- [x] Write failing test: `test_check_budget_logs_warning_at_90_percent_threshold`.
- [x] Implement 90%-threshold warning log in `_check_budget`.
- [x] Run `uv run pytest` on all `_check_budget` tests — confirm all pass.
- [x] Write failing test: `test_handle_watchdog_error_logs_error_to_logger`.
- [x] Implement `DebateEngine._handle_watchdog_error(self, error: WatchdogError) -> None`.
- [x] Write failing test: `test_handle_watchdog_error_appends_event_to_state`.
- [x] Implement state-event append in `_handle_watchdog_error`.
- [x] Write failing test: `test_handle_watchdog_error_saves_partial_state_json_to_logs`.
- [x] Implement partial-state JSON dump in `_handle_watchdog_error`.
- [x] Run `uv run pytest` on all `_handle_watchdog_error` tests — confirm all pass.
- [x] Write failing test: `test_start_returns_verdict_object`.
- [x] Implement `DebateEngine.start(self, topic: str) -> Verdict`.
- [x] Write failing test: `test_start_calls_father_open_debate_with_topic_string`.
- [x] Write failing test: `test_start_verdict_draw_field_is_always_false`.
- [x] Write failing test: `test_start_forces_early_evaluation_when_budget_cap_exceeded`.
- [x] Implement early-evaluation branch in `start`.
- [x] Write failing test: `test_start_propagates_watchdog_error_after_max_retries`.
- [x] Implement `WatchdogError` propagation in `start`.
- [x] Run `uv run pytest` on all `start` tests — confirm all pass.
- [x] Run `uv run ruff check src/engine/debate_engine.py` — confirm 0 violations.
- [x] Run `wc -l src/engine/debate_engine.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement DebateEngine orchestration loop with budget guard`.

### 3.3 Integration Tests — Full Debate

- [x] Create `tests/integration/test_full_debate.py`.
- [x] Add `import pytest`, `import os`, `from src.engine.debate_engine import DebateEngine`.
- [x] Add `from src.infrastructure.config_loader import ConfigLoader`.
- [x] Add `pytestmark = pytest.mark.slow` at module level.
- [x] Define `live_config` fixture loading from real `config/setup.json`.
- [x] Define `debate_engine_live` fixture with real API keys from `.env`.
- [x] Write integration test: `test_full_debate_completes_without_raising_exception`.
- [x] Write integration test: `test_full_debate_returns_verdict_object`.
- [x] Write integration test: `test_full_debate_transcript_has_at_least_20_messages`.
- [x] Write integration test: `test_full_debate_all_messages_validate_against_debate_message_schema`.
- [x] Write integration test: `test_full_debate_verdict_draw_field_is_false`.
- [x] Write integration test: `test_full_debate_verdict_winner_is_pro_son_or_con_son`.
- [x] Write integration test: `test_full_debate_web_search_invoked_at_least_once_per_3_turns_per_side`.
- [x] Write integration test: `test_full_debate_cost_report_generated_at_session_end`.
- [x] Write integration test: `test_no_message_sent_directly_from_pro_son_to_con_son`.
- [x] Write integration test: `test_no_message_sent_directly_from_con_son_to_pro_son`.
- [x] Run `uv run pytest -m slow tests/integration/test_full_debate.py` — confirm all pass.
- [x] Fix any integration failures and re-run until green.
- [x] Git commit: `test: add full-debate integration test suite`.

---

## Phase 4 — CLI, Reporting & Final Delivery

### 4.1 DebateCLI

- [x] Create `src/ui/debate_cli.py`.
- [x] Add imports: `import argparse`, `import sys`.
- [x] Add `from src.engine.debate_engine import DebateEngine`.
- [x] Add `from src.infrastructure.config_loader import ConfigLoader`.
- [x] Add `from src.infrastructure.cost_reporter import CostReporter`.
- [x] Add `from src.infrastructure.watchdog import WatchdogError`.
- [x] Create `tests/unit/test_debate_cli.py`.
- [x] Add imports: `import pytest`, `from unittest.mock import MagicMock, patch`.
- [x] Add `from src.ui.debate_cli import parse_args, run`.
- [x] Write failing test: `test_parse_args_exits_with_code_2_when_topic_is_missing`.
- [x] Implement `parse_args() -> argparse.Namespace` with required `--topic` argument.
- [x] Write failing test: `test_parse_args_returns_namespace_with_topic_string`.
- [x] Write failing test: `test_parse_args_accepts_optional_config_flag`.
- [x] Implement optional `--config PATH` flag in `parse_args`.
- [x] Write failing test: `test_parse_args_accepts_optional_dry_run_flag`.
- [x] Implement optional `--dry-run` boolean flag in `parse_args`.
- [x] Run `uv run pytest` on all `parse_args` tests — confirm all pass.
- [x] Write failing test: `test_run_returns_0_on_successful_debate` — mocked engine.
- [x] Implement `run() -> int` entry function.
- [x] Write failing test: `test_run_calls_debate_engine_start_with_topic_string`.
- [x] Verify `engine.start(topic)` is called inside `run`.
- [x] Write failing test: `test_run_prints_verdict_output_to_stdout`.
- [x] Implement `_print_verdict(verdict) -> None` and wire into `run`.
- [x] Write failing test: `test_run_prints_cost_report_to_stdout`.
- [x] Implement `_print_cost_report(summary) -> None` and wire into `run`.
- [x] Write failing test: `test_run_dry_run_validates_config_without_calling_llm_api`.
- [x] Implement dry-run config-only validation in `run`.
- [x] Write failing test: `test_run_dry_run_prints_config_loaded_message`.
- [x] Write failing test: `test_run_returns_1_on_watchdog_error`.
- [x] Implement `WatchdogError` → exit code 1 in `run`.
- [x] Run `uv run pytest` on all `run` tests — confirm all pass.
- [x] Add `debate = "src.ui.debate_cli:run"` to `[project.scripts]` in `pyproject.toml`.
- [x] Run `uv sync` to register the new entry point.
- [x] Run `uv run debate --help` — confirm help text prints without error.
- [x] Run `uv run debate --topic "AI is beneficial" --dry-run` — confirm dry-run output matches PRD §7.1.
- [x] Run `uv run ruff check src/ui/debate_cli.py` — confirm 0 violations.
- [x] Run `wc -l src/ui/debate_cli.py` — confirm ≤ 150 lines.
- [x] Git commit: `feat: implement DebateCLI with argparse, dry-run, and cost report`.

### 4.2 Live CLI Output Verification

- [x] Run `uv run debate --topic "AI will replace human workers"` with real API keys.
- [x] Verify terminal shows `[INFO]  Loading config from config/setup.json ...`.
- [x] Verify terminal shows `[INFO]  Config loaded. Schema version: 1.0`.
- [x] Verify terminal shows agent model assignments line.
- [x] Verify terminal shows `[DEBATE STARTING]` block with topic string.
- [x] Verify terminal shows `[VERDICT]` box with winner name and reasoning text.
- [x] Verify terminal shows cost report table and totals.
- [x] Verify exit code 0 on success: `echo $?`.
- [x] Git commit: `test: verify live CLI output matches PRD §7 specification`.

### 4.3 Final Code Quality Gate

- [x] Run `uv run ruff check .` across entire repo.
- [x] Fix every ruff violation found (zero tolerance policy).
- [x] Run `uv run ruff check .` again — confirm output is completely empty.
- [x] Run `uv run pytest --cov=src --cov-report=term-missing`.
- [x] Identify every module below 85% coverage from the report.
- [x] Write additional unit tests for each under-covered module.
- [x] Re-run `uv run pytest --cov=src --cov-fail-under=85` — confirm it passes.
- [x] Run `grep -rn "sk-ant" src/` — confirm 0 matches (no hardcoded Anthropic keys).
- [x] Run `grep -rn "api_key\s*=\s*['\"]" src/` — confirm 0 matches.
- [x] Run `grep -rn "ANTHROPIC_API_KEY\s*=\s*['\"]sk-" src/` — confirm 0 matches.
- [x] Audit every `.py` file in `src/` for hardcoded base URLs or IP addresses.
- [x] Check every source file: `for f in $(find src -name "*.py"); do c=$(wc -l < "$f"); [ "$c" -gt 150 ] && echo "$f: $c lines"; done`.
- [x] Split any file that exceeds 150 lines into appropriate sub-modules.
- [x] Re-run ruff and pytest after any splits — confirm both still pass.
- [x] Validate all three config JSON files: `python -m json.tool config/setup.json`, `rate_limits.json`, `pricing.json`.
- [x] Run `uv run python -c "from src.engine.debate_engine import DebateEngine"` — no import error.
- [x] Run `uv run python -c "from src.ui.debate_cli import run"` — no import error.
- [x] Confirm `logs/` is not tracked: `git ls-files logs/` returns empty.
- [x] Confirm `.env` is not tracked: `git ls-files .env` returns empty.
- [x] Git commit: `chore: code quality gate — 0 ruff violations, ≥85% coverage`.

### 4.4 README Completion

- [x] Write `## Overview` section with full system description in `README.md`.
- [x] Write `## Architecture` section referencing PLAN.md C4 diagrams.
- [x] Write `## Prerequisites` section: Python 3.11+, uv, API keys required.
- [x] Write `## Installation` section: step-by-step `uv sync` and `.env` setup.
- [x] Write `## Configuration` section describing all config files and key fields.
- [x] Write `## Usage` section with `uv run debate --topic "..."` example.
- [x] Write `## Dry Run` section showing `--dry-run` flag usage.
- [x] Write `## Debate Output` section describing each terminal output stage per PRD §7.
- [x] Write `## Running Tests` section: unit (`uv run pytest`) and integration (`uv run pytest -m slow`).
- [x] Write `## Cost Reporting` section explaining the cost table columns and budget cap.
- [x] Write `## Golden Rules` section: 150-line limit, ruff, 85% coverage, TDD.
- [x] Write `## Project Structure` section with full directory tree.
- [x] Write `## Agent Roles` section with three-agent table (Father/Pro Son/Con Son).
- [x] Write `## JSON Message Contract` section with example `DebateMessage` JSON.
- [x] Write `## Verdict Format` section with example `Verdict` JSON.
- [x] Write `## State Machine` section summarising the four lifecycle states.
- [x] Write `## Error Handling` section with condensed edge-case table from PRD §6.
- [x] Write `## Persuasiveness Rubric` section with the three scoring dimensions.
- [x] Write `## Extensibility` section explaining the `AgentSkill` plugin pattern.
- [x] Write `## License` section (MIT).
- [x] Proof-read README for accuracy against final implementation.
- [x] Git commit: `docs: complete README with architecture, usage, and examples`.

### 4.5 Sample Output & Acceptance Verification

- [x] Run full live debate on topic `"Remote work is better than office work"`.
- [x] Save terminal output to `examples/sample_output.txt`.
- [x] Copy final debate state JSON from `logs/` to `examples/sample_debate.json`.
- [x] Verify `examples/sample_debate.json` transcript array has ≥ 20 entries.
- [x] Verify `examples/sample_debate.json` verdict has `draw == false`.
- [x] Verify `examples/sample_debate.json` has non-null `cost_summary`.
- [x] Verify AC-01: transcript length ≥ 20 (10 per side).
- [x] Verify AC-02: `sources` field non-empty at least once every 3 turns per side.
- [x] Verify AC-03: run schema validator on every message in sample — 100% pass.
- [x] Verify AC-07: `uv run ruff check .` output is empty.
- [x] Verify AC-08: `uv run pytest --cov=src --cov-fail-under=85` passes.
- [x] Verify AC-09: `grep -rn "sk-ant\|api_key.*=" src/` returns 0 matches.
- [x] Verify AC-10: cost report table printed before exit in all sample runs.
- [x] Add `examples/` directory and files to git.
- [x] Git commit: `examples: add sample debate output and acceptance verification results`.

### 4.6 Release Tagging

- [x] Run full unit test suite: `uv run pytest` — confirm all green.
- [x] Run full integration suite: `uv run pytest -m slow` — confirm all green.
- [x] Run `uv run ruff check .` — confirm 0 violations (final check).
- [x] Run `uv run pytest --cov=src --cov-fail-under=85` — confirm passes (final check).
- [x] Review git log: confirm every commit follows `type: description` convention.
- [x] Confirm `docs/PRD.md` reflects all implemented features accurately.
- [x] Confirm `docs/PLAN.md` class diagram matches actual class hierarchy in `src/`.
- [x] Confirm all tasks in `docs/TODO.md` are checked off.
- [x] Create git tag: `git tag v1.0.0`.
- [x] Git commit: `release: v1.0.0 — AI Debate System complete`.

---

## Phase 5 — QA Fixes & Web GUI

### 5.0 Documentation Update

- [x] Update `docs/PRD.md`: add §2.6 Father Behavioral Rules (no draws, dodging, language, `current_lean`) and §14 Web GUI.
- [x] Update `docs/PLAN.md`: add §9 Phase 5 roadmap (QA fixes + Web GUI architecture).
- [x] Update `docs/TODO.md`: add Phase 5 checklist (this section).
- [x] Git commit: `docs: update PRD, PLAN, and TODO for Phase 5 QA and GUI`.

### 5.1 Topic Bug Fix

- [x] In `src/agents/pro_son_agent.py`: change `generate_argument(self, prompt)` signature to `generate_argument(self, prompt, topic: str = "")`.
- [x] Update `build_prompt` call inside `generate_argument` to use `topic` param when non-empty, else fall back to `prompt.content`.
- [x] In `src/agents/con_son_agent.py`: apply the same `topic: str = ""` parameter change.
- [x] In `src/engine/debate_engine.py._run_turn_loop`: pass `topic=self.state_manager.state.topic` to both `generate_argument` calls.
- [x] Add failing unit test in `tests/unit/test_pro_son_agent.py`: `test_generate_argument_uses_explicit_topic_when_provided`.
- [x] Add failing unit test in `tests/unit/test_con_son_agent.py`: `test_generate_argument_uses_explicit_topic_when_provided`.
- [x] Run `uv run pytest tests/unit/test_pro_son_agent.py tests/unit/test_con_son_agent.py` — confirm all pass.
- [x] Run `uv run ruff check src/agents/pro_son_agent.py src/agents/con_son_agent.py src/engine/debate_engine.py` — confirm 0 violations.
- [x] Confirm each edited file remains ≤ 150 lines.

### 5.2 Father Moderation & Scoring Updates

- [x] In `src/agents/father_agent.py`: update `_RUBRIC_TEMPLATE` to include:
  - Instruction to detect and note **argument dodging** (same-turn pivot or verbatim repeat).
  - Instruction to detect and note **disrespectful or inappropriate language**.
  - Instruction that the Father does **not** fact-check sources — agents challenge sources through argument.
  - `"current_lean": "pro_son | con_son"` field in the expected JSON response.
  - Remove redundant `"draw": false` line from the JSON template (schema enforces it).
- [x] Confirm `father_agent.py` remains ≤ 150 lines after changes.
- [x] Add failing unit test: `test_score_persuasiveness_result_contains_current_lean_key`.
- [x] Add failing unit test: `test_rubric_prompt_contains_dodging_instruction`.
- [x] Add failing unit test: `test_rubric_prompt_contains_language_enforcement_instruction`.
- [x] Add failing unit test: `test_rubric_prompt_does_not_instruct_fact_checking`.
- [x] Run `uv run pytest tests/unit/test_father_agent.py` — confirm all pass.
- [x] Run `uv run ruff check src/agents/father_agent.py` — confirm 0 violations.

### 5.3 Schema Verification (No Draws)

- [x] Open `src/schemas/verdict.json` — confirm `"draw": {"const": false}` is present.
- [x] Confirm `"winner": {"enum": ["pro_son", "con_son"]}` is present.
- [x] Confirm `"additionalProperties": false` is set.
- [x] Run existing `test_evaluate_returns_verdict_with_draw_false` — confirm still passes.
- [x] No schema file changes required unless a regression is found.

### 5.4 QA Gate

- [x] Run `uv run pytest` — confirm all unit and integration tests pass.
- [x] Run `uv run ruff check .` — confirm 0 violations.
- [x] Run `uv run pytest --cov=src --cov-fail-under=85` — confirm coverage gate holds.
- [x] Confirm no Python file in `src/` exceeds 150 lines.
- [x] Git commit: `fix: resolve topic bug and apply QA debate rules`.

### 5.5 Flask Web GUI

- [x] Add `flask` (≥ 3.0) to `[project.dependencies]` in `pyproject.toml`.
- [x] Run `uv sync` to install Flask.
- [x] Create `src/ui/app.py` — Flask application factory with `GET /` and `POST /api/debate`; `main()` entry point (84 lines).
- [x] Create `templates/index.html` — Bootstrap 5 + jQuery chat interface; topic form, colour-coded chat bubbles, verdict card, cost card.
- [x] Add `debate-web = "src.ui.app:main"` to `[project.scripts]` in `pyproject.toml`.
- [x] Run `uv sync` to register the new entry point.
- [x] Create `tests/unit/test_web_app.py` — 11 TDD tests covering all routes and edge cases via `app.test_client()`.
- [x] Write failing test: `test_index_route_returns_200`.
- [x] Write failing test: `test_api_debate_returns_400_when_topic_missing`.
- [x] Write failing test: `test_api_debate_returns_200_on_success`.
- [x] Write failing test: `test_api_debate_returns_500_on_engine_error`.
- [x] Implement routes; confirm all 237 tests pass.
- [x] Run `uv run ruff check src/ui/app.py` — confirm 0 violations.
- [x] Confirm `src/ui/app.py` ≤ 150 lines (84 lines).
- [x] Git commit: `feat: implement responsive Flask GUI with Bootstrap and jQuery`.

---

## Phase 5.1 — Post-v2.0.0 Hotfixes

> Applied after v2.0.0 to fix position-check failures observed in live debate runs.
> All five golden rules remain satisfied: ≤150 lines · 0 ruff · >85% coverage · no hardcoded values.

### 5.1.1 JSON Markdown Fix

- [x] Identify root cause: Claude responses wrapped in ` ```json ``` ` fences fail `json.loads()`.
- [x] Add `_extract_json(raw: str) -> str` to `src/agents/base_agent.py`.
- [x] Strip ` ```json ``` ` fences and extract `{…}` substring before parsing.
- [x] Route all `parse_response()` calls through `_extract_json`.
- [x] Verify `uv run pytest` still passes — confirm 0 regressions.

### 5.1.2 Live Cost Tracking Fix (`max_tokens=4096`)

- [x] Identify root cause: default `max_tokens` caused mid-sentence truncation.
- [x] Set `max_tokens=4096` in `Gatekeeper._make_api_call()`.
- [x] Confirm token counts now reflect full completions in `CostReporter`.
- [x] Verify `uv run pytest` still passes.
- [x] Git commit: `feat: increase max_tokens and display Father's rubric reasoning in UI`.

### 5.1.3 Father Reasoning UI Addition

- [x] Confirm `POST /api/debate` already returns `verdict.reasoning` in payload.
- [x] Update `templates/index.html`: render `reasoning` text inside verdict card.
- [x] Manual smoke test: reasoning paragraph visible below winner announcement.
- [x] Git commit included in `feat: increase max_tokens` commit above.

### 5.1.4 Chain-of-Thought Schema and "No Surrender" Stance Enforcement

- [x] Update `ProSonAgent.build_prompt()`: embed `{"opponent_analysis", "debate_strategy", "argument"}` JSON schema requirement.
- [x] Update `ConSonAgent.build_prompt()`: same CoT schema.
- [x] Add `NO SURRENDER` clause to both prompts: never concede, never neutral, counter directly.
- [x] Add `_extract_argument(raw: str) -> str` to both agents: parses CoT JSON, returns `"argument"` field; falls back to raw text on parse failure.
- [x] Update `generate_argument()` in both agents: call `_extract_argument(raw)` before `_enforce_position()`.
- [x] Confirm transcript/UI only shows `"argument"` field (hidden: `opponent_analysis`, `debate_strategy`).
- [x] Confirm each modified file ≤ 150 lines (`pro_son_agent.py`: 147, `con_son_agent.py`: 147).
- [x] Run `uv run ruff check .` — confirm 0 violations.
- [x] Run `uv run pytest` — confirm 227 tests pass, 97.73% coverage.
- [x] Git commit: `fix: implement chain-of-thought schema and strict stance prompts to prevent position failure`.

### 5.1.5 Documentation Sync

- [x] Update `docs/PRD.md`: add §15 Post-v2.0.0 Hotfixes (max_tokens, _extract_json, reasoning UI, CoT schema + No Surrender).
- [x] Update `docs/PLAN.md`: add §9.5 Phase 5.1 hotfix table and CoT flow diagram.
- [x] Update `docs/TODO.md`: add this Phase 5.1 checklist with all tasks checked off.
- [x] Git commit: `docs: synchronize PRD, PLAN, and TODO with post-v2.0.0 UX and reliability hotfixes`.

---

## Phase 5.2 — Final UI Scoreboard & Cost-Tracking Hotfixes

> Applied after v2.0.0 to restore the numerical rubric scores in the web UI
> and fix live Anthropic model price tracking via fuzzy-string matching.

### 5.2.1 Restore Numerical Scores in Verdict UI

- [x] Identify root cause: `templates/index.html` rendered only `reasoning` text; `scores` object present in API response but unused.
- [x] Update verdict card jQuery: extract `data.verdict.scores.pro_son` and `data.verdict.scores.con_son`.
- [x] Render scoreboard table rows: `Clarity: N/10 | Evidence: N/10 | Logic: N/10 → Total: N/30` for each agent.
- [x] Verify both scoreboard table and `reasoning` paragraph appear together in verdict card.
- [x] Manual smoke test: scores and reasoning visible after a live debate run.

### 5.2.2 Fuzzy-String Model Price Matching

- [x] Identify root cause: Anthropic API returns date-suffixed model IDs (e.g. `claude-haiku-4-5-20251001`) that miss `pricing.json` exact-key lookup.
- [x] Add fuzzy fallback path to `CostReporter.compute()`: longest-common-prefix scan over all pricing keys.
- [x] Apply 60% match-ratio threshold; flag as `"UNKNOWN PRICE"` and emit `[WARN]` when threshold not met.
- [x] Emit `[WARN]` log line when fuzzy path is used, showing live model ID and matched key.
- [x] Verify `uv run pytest` still passes — confirm 0 regressions.
- [x] Confirm cost card now shows real USD values (not $0.0000) in web UI.

### 5.2.3 Documentation Sync

- [x] Update `docs/PRD.md`: add §15.5 (numerical scores in UI) and §15.6 (fuzzy price lookup).
- [x] Update `docs/PLAN.md`: add §9.6 Phase 5.2 fix table and fuzzy-lookup algorithm.
- [x] Update `docs/TODO.md`: add this Phase 5.2 checklist with all tasks checked off.
- [x] Update `README.md`: polish setup/config instructions, clarify `ANTHROPIC_API_KEY`, add Screenshots section.
- [x] Git commit: `docs: update PRD, PLAN, TODO, and README for final UI scores, cost tracking, and screenshot placeholders`.

---

## Phase 5.3 — End-to-End Cost Tracking Wire-Up

> Three root causes identified and resolved together. All golden rules satisfied.
> See `docs/PRD.md §15.7–15.8` and `docs/PLAN.md §9.7` for full root-cause analysis.

### 5.3.1 `app.py` Configuration Merge Fix

- [x] Identify root cause: `create_app()` route passed only `load_setup()` to `DebateEngine`; `pricing.json` missing from config dict.
- [x] Fix: `cfg = {**_loader.load_setup(), "pricing": _loader.load_pricing()}` before `DebateEngine(cfg)`.
- [x] Verify cost card shows non-zero USD values in web UI after fix.
- [x] Confirm `src/ui/app.py` remains ≤ 150 lines.
- [x] Run `uv run ruff check src/ui/app.py` — confirm 0 violations.

### 5.3.2 `DebateEngine._sync_costs()` Orchestration Loop Fix

- [x] Identify root cause: `Gatekeeper.UsageStats` and `CostReporter._records` were disconnected; `compute()` always returned $0.
- [x] Implement `DebateEngine._sync_costs()`: clears `_records`, then calls `cost_reporter.record_usage()` for each agent from `gatekeeper.get_usage()`.
- [x] Wire `_sync_costs()` into `start()` (called once before final `compute()`) and `_check_budget()` (called each turn).
- [x] Confirm per-agent token counts appear in cost report after a live run.
- [x] Run `uv run pytest` — confirm 0 regressions.
- [x] Confirm `src/engine/debate_engine.py` remains ≤ 150 lines.

### 5.3.3 `CostReporter` Fuzzy Model-ID Matching

- [x] Identify root cause: Anthropic date-suffix model IDs (e.g. `claude-haiku-4-5-20251001`) fail strict `pricing.json` key lookup → silent $0.
- [x] Add `_find_rates(model: str) -> dict` to `CostReporter`: longest-common-prefix scan; 60% match-ratio threshold.
- [x] Emit `[WARN]` log when fuzzy path is taken; emit `"UNKNOWN PRICE"` warn when threshold not met.
- [x] Route all `compute()` rate lookups through `_find_rates()`.
- [x] Confirm `src/infrastructure/cost_reporter.py` remains ≤ 150 lines.
- [x] Run `uv run ruff check src/infrastructure/cost_reporter.py` — confirm 0 violations.
- [x] Run `uv run pytest` — confirm 0 regressions.

### 5.3.4 Documentation Sync

- [x] Update `docs/PRD.md`: add §15.7 (`app.py` config merge) and §15.8 (`_sync_costs()` orchestration fix).
- [x] Update `docs/PLAN.md`: add §9.7 Phase 5.3 end-to-end cost tracking data-flow table.
- [x] Update `docs/TODO.md`: add this Phase 5.3 checklist with all tasks checked off.
- [x] Update `README.md`: professional overhaul — introduction, quick start, all run options, screenshot placeholders.
- [x] Git commit: `docs: complete professional README overhaul and synchronize final cost-tracking hotfixes across documentation`.

---

### 5.6 Final Release

- [x] Run full test suite: `uv run pytest --cov=src --cov-fail-under=85` — confirm green.
- [x] Run `uv run ruff check .` — confirm 0 violations.
- [x] Update `README.md`: add Web GUI section describing `uv run debate-web` usage.
- [x] Create git tag: `git tag v2.0.0`.
- [x] Git commit: `release: v2.0.0 — Phase 5 QA fixes and Web GUI complete`.

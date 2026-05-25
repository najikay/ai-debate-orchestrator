"""Unit tests for ConfigLoader.

TDD order:
    __init__ → load_setup → load_rate_limits → load_pricing
    → _validate_schema_version → load_all
"""

import json

import pytest

from src.infrastructure.config_loader import ConfigLoader, ConfigVersionError

# ---------------------------------------------------------------------------
# Minimal valid fixture data
# ---------------------------------------------------------------------------

_VALID_SETUP: dict = {
    "schema_version": "1.0",
    "debate": {"min_turns_per_side": 10, "max_session_cost_usd": 2.0},
    "agents": {
        "father": {"model": "claude-sonnet-4-6"},
        "pro_son": {"model": "claude-haiku-4-5"},
        "con_son": {"model": "claude-haiku-4-5"},
    },
    "watchdog": {"timeout_seconds": 30, "max_retries": 1},
    "logging": {"log_dir": "logs/", "max_files": 20, "max_lines_per_file": 500},
    "enabled_skills": ["web_search"],
}

_VALID_RATE_LIMITS: dict = {
    "schema_version": "1.0",
    "models": {"claude-sonnet-4-6": {"rpm": 50, "tpm": 40000}},
    "web_search": {"rpm": 30},
}

_VALID_PRICING: dict = {
    "schema_version": "1.0",
    "models": {
        "claude-sonnet-4-6": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    },
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_config_dir(tmp_path: pytest.TempPathFactory) -> pytest.TempPathFactory:
    """Temp directory pre-populated with all three valid config JSON files."""
    (tmp_path / "setup.json").write_text(json.dumps(_VALID_SETUP))
    (tmp_path / "rate_limits.json").write_text(json.dumps(_VALID_RATE_LIMITS))
    (tmp_path / "pricing.json").write_text(json.dumps(_VALID_PRICING))
    return tmp_path


@pytest.fixture
def loader(tmp_config_dir: pytest.TempPathFactory) -> ConfigLoader:
    """ConfigLoader pointed at the pre-populated config dir."""
    return ConfigLoader(str(tmp_config_dir))


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_config_loader_init_sets_config_dir(tmp_config_dir: pytest.TempPathFactory) -> None:
    """config_dir attribute matches the directory passed to __init__."""
    from pathlib import Path

    result = ConfigLoader(str(tmp_config_dir))
    assert result.config_dir == Path(tmp_config_dir)


# ---------------------------------------------------------------------------
# load_setup
# ---------------------------------------------------------------------------


def test_load_setup_returns_dict(loader: ConfigLoader) -> None:
    """load_setup returns a dict for a valid setup.json."""
    result = loader.load_setup()
    assert isinstance(result, dict)
    assert result["schema_version"] == "1.0"


def test_load_setup_raises_file_not_found(tmp_path: pytest.TempPathFactory) -> None:
    """load_setup raises FileNotFoundError when setup.json is absent."""
    loader = ConfigLoader(str(tmp_path))  # empty dir
    with pytest.raises(FileNotFoundError):
        loader.load_setup()


def test_load_setup_raises_on_invalid_json(tmp_path: pytest.TempPathFactory) -> None:
    """load_setup raises json.JSONDecodeError when file contains bad JSON."""
    (tmp_path / "setup.json").write_text("{ not valid json }")
    loader = ConfigLoader(str(tmp_path))
    with pytest.raises(json.JSONDecodeError):
        loader.load_setup()


# ---------------------------------------------------------------------------
# load_rate_limits
# ---------------------------------------------------------------------------


def test_load_rate_limits_returns_dict(loader: ConfigLoader) -> None:
    """load_rate_limits returns a dict with expected keys."""
    result = loader.load_rate_limits()
    assert isinstance(result, dict)
    assert "models" in result


def test_load_rate_limits_raises_file_not_found(tmp_path: pytest.TempPathFactory) -> None:
    """load_rate_limits raises FileNotFoundError when the file is absent."""
    loader = ConfigLoader(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        loader.load_rate_limits()


# ---------------------------------------------------------------------------
# load_pricing
# ---------------------------------------------------------------------------


def test_load_pricing_returns_dict(loader: ConfigLoader) -> None:
    """load_pricing returns a dict with expected keys."""
    result = loader.load_pricing()
    assert isinstance(result, dict)
    assert "models" in result


def test_load_pricing_raises_file_not_found(tmp_path: pytest.TempPathFactory) -> None:
    """load_pricing raises FileNotFoundError when the file is absent."""
    loader = ConfigLoader(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        loader.load_pricing()


# ---------------------------------------------------------------------------
# _validate_schema_version
# ---------------------------------------------------------------------------


def test_validate_schema_version_passes_on_matching_version(loader: ConfigLoader) -> None:
    """No exception raised when schema_version matches expected."""
    loader._validate_schema_version({"schema_version": "1.0"}, "1.0")  # must not raise


def test_validate_schema_version_raises_config_version_error_on_mismatch(
    loader: ConfigLoader,
) -> None:
    """ConfigVersionError raised when schema_version does not match."""
    with pytest.raises(ConfigVersionError):
        loader._validate_schema_version({"schema_version": "2.0"}, "1.0")


def test_validate_schema_version_raises_when_field_is_missing(loader: ConfigLoader) -> None:
    """ConfigVersionError raised when schema_version key is absent."""
    with pytest.raises(ConfigVersionError):
        loader._validate_schema_version({}, "1.0")


# ---------------------------------------------------------------------------
# load_all
# ---------------------------------------------------------------------------


def test_load_all_populates_setup_rate_limits_and_pricing(loader: ConfigLoader) -> None:
    """load_all populates all three instance attributes."""
    loader.load_all()
    assert loader.setup["schema_version"] == "1.0"
    assert loader.rate_limits["schema_version"] == "1.0"
    assert loader.pricing["schema_version"] == "1.0"


def test_load_all_raises_config_version_error_on_bad_schema_version(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """load_all raises ConfigVersionError when setup.json has wrong schema_version."""
    bad_setup = {**_VALID_SETUP, "schema_version": "99.0"}
    (tmp_path / "setup.json").write_text(json.dumps(bad_setup))
    (tmp_path / "rate_limits.json").write_text(json.dumps(_VALID_RATE_LIMITS))
    (tmp_path / "pricing.json").write_text(json.dumps(_VALID_PRICING))
    loader = ConfigLoader(str(tmp_path))
    with pytest.raises(ConfigVersionError):
        loader.load_all()

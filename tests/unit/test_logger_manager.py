"""Unit tests for LoggerManager.

TDD order:
    __init__ → write (happy + format + bad level)
    → _get_current_file (same path + overflow)
    → _rotate (eviction + no-eviction)
"""

import time
from pathlib import Path

import pytest

from src.infrastructure.logger_manager import LoggerManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_log_dir(tmp_path: Path) -> Path:
    """Return a path inside tmp_path; LoggerManager will create it."""
    return tmp_path / "logs"


@pytest.fixture
def logger(tmp_log_dir: Path) -> LoggerManager:
    """LoggerManager with small limits so rotation is fast to trigger."""
    return LoggerManager(str(tmp_log_dir), max_files=5, max_lines=10)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_logger_manager_init_creates_log_dir(tmp_log_dir: Path) -> None:
    """The log directory is created on __init__ even if it did not exist."""
    assert not tmp_log_dir.exists()
    LoggerManager(str(tmp_log_dir), max_files=5, max_lines=10)
    assert tmp_log_dir.exists()
    assert tmp_log_dir.is_dir()


# ---------------------------------------------------------------------------
# write — happy path
# ---------------------------------------------------------------------------


def test_write_creates_log_file(logger: LoggerManager, tmp_log_dir: Path) -> None:
    """The first write creates exactly one .log file in the log directory."""
    logger.write("INFO", "test_component", "hello world")
    log_files = list(tmp_log_dir.glob("*.log"))
    assert len(log_files) == 1


def test_write_appends_multiple_lines(logger: LoggerManager, tmp_log_dir: Path) -> None:
    """Multiple writes accumulate lines in the same file (within the limit)."""
    logger.write("INFO", "cmp", "line 1")
    logger.write("DEBUG", "cmp", "line 2")
    log_file = next(tmp_log_dir.glob("*.log"))
    lines = log_file.read_text().splitlines()
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# write — format
# ---------------------------------------------------------------------------


def test_write_format_matches_spec(logger: LoggerManager, tmp_log_dir: Path) -> None:
    """Each log line matches: <ISO-timestamp> | LEVEL | COMPONENT | MESSAGE."""
    logger.write("WARNING", "mycomponent", "something happened")
    log_file = next(tmp_log_dir.glob("*.log"))
    line = log_file.read_text().strip()
    # The line must contain the three separators in order
    assert " | WARNING | mycomponent | something happened" in line
    # The timestamp prefix must look like an ISO datetime (starts with digit)
    assert line[0].isdigit()


def test_write_all_valid_levels_accepted(logger: LoggerManager) -> None:
    """DEBUG, INFO, WARNING, and ERROR are all accepted without raising."""
    for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        logger.write(level, "cmp", "msg")  # must not raise


# ---------------------------------------------------------------------------
# write — bad level
# ---------------------------------------------------------------------------


def test_write_rejects_unknown_level(logger: LoggerManager) -> None:
    """An unrecognised level string raises ValueError."""
    with pytest.raises(ValueError, match="Invalid log level"):
        logger.write("CRITICAL", "cmp", "msg")


def test_write_rejects_lowercase_level(logger: LoggerManager) -> None:
    """Level matching is case-sensitive; lowercase raises ValueError."""
    with pytest.raises(ValueError, match="Invalid log level"):
        logger.write("info", "cmp", "msg")


# ---------------------------------------------------------------------------
# _get_current_file
# ---------------------------------------------------------------------------


def test_get_current_file_returns_path_inside_log_dir(
    logger: LoggerManager, tmp_log_dir: Path
) -> None:
    """_get_current_file returns a Path whose parent is the log directory."""
    logger.write("INFO", "cmp", "seed")  # ensure a file exists
    path = logger._get_current_file()
    assert path.parent == tmp_log_dir


def test_get_current_file_returns_same_path_on_repeated_calls(
    logger: LoggerManager,
) -> None:
    """Repeated calls return the same path when line limit is not reached."""
    logger.write("INFO", "cmp", "seed")
    path1 = logger._get_current_file()
    path2 = logger._get_current_file()
    assert path1 == path2


def test_get_current_file_opens_new_file_after_line_limit(
    logger: LoggerManager, tmp_log_dir: Path
) -> None:
    """After max_lines writes, the next write goes to a new file."""
    for i in range(10):  # max_lines = 10
        logger.write("INFO", "cmp", f"line {i}")
    first_file = logger._current_file

    # This write must overflow into a second file
    logger.write("INFO", "cmp", "overflow")
    assert logger._current_file != first_file
    assert len(list(tmp_log_dir.glob("*.log"))) == 2


# ---------------------------------------------------------------------------
# _rotate
# ---------------------------------------------------------------------------


def test_rotate_deletes_oldest_file_when_max_files_exceeded(
    logger: LoggerManager, tmp_log_dir: Path
) -> None:
    """When a 6th file is opened (max_files=5), the oldest file is evicted."""
    # Fill 5 complete files (5 × 10 = 50 writes)
    for _ in range(5):
        for _ in range(10):
            logger.write("INFO", "cmp", "filling")
        time.sleep(0.002)  # guarantee distinct timestamps in filenames

    initial_files = sorted(tmp_log_dir.glob("*.log"))
    assert len(initial_files) == 5
    oldest = initial_files[0]

    # 51st write triggers creation of 6th file → _rotate must evict one
    logger.write("DEBUG", "cmp", "triggers rotation")
    remaining = set(tmp_log_dir.glob("*.log"))

    assert len(remaining) <= 5, "More than max_files files remain after rotation"
    assert oldest not in remaining, "Oldest file was not evicted"


def test_rotate_does_not_delete_when_below_max_files_limit(
    logger: LoggerManager, tmp_log_dir: Path
) -> None:
    """No file is evicted when creating the 5th file (max_files=5)."""
    # Fill 4 complete files (4 × 10 = 40 writes)
    for _ in range(4):
        for _ in range(10):
            logger.write("INFO", "cmp", "filling")
        time.sleep(0.002)

    count_before = len(list(tmp_log_dir.glob("*.log")))
    assert count_before == 4

    # 41st write opens the 5th file — no eviction should happen
    logger.write("INFO", "cmp", "one more")
    count_after = len(list(tmp_log_dir.glob("*.log")))

    assert count_after == count_before + 1, "A file was unexpectedly evicted"

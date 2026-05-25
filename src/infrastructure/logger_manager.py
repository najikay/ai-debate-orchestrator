"""LoggerManager — structured, FIFO-rotated file logging for the debate system.

Log format per line::

    <ISO-8601 UTC timestamp> | <LEVEL> | <COMPONENT> | <MESSAGE>

Rotation policy:
    - Each file holds at most *max_lines* entries.
    - At most *max_files* files are retained; the oldest is evicted when the
      limit is exceeded (FIFO).
"""

from datetime import datetime, timezone
from pathlib import Path

_VALID_LEVELS: frozenset[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})


class LoggerManager:
    """Manages structured, FIFO-rotated log files.

    Args:
        log_dir: Directory where ``.log`` files will be written.
            Created automatically if it does not exist.
        max_files: Maximum number of log files to retain.
            The oldest file is deleted when this limit is exceeded.
        max_lines: Maximum number of lines written to a single file
            before a new file is opened.

    Attributes:
        log_dir: Resolved :class:`~pathlib.Path` for the log directory.
        max_files: File-retention limit.
        max_lines: Per-file line limit.

    Example::

        mgr = LoggerManager("logs/", max_files=20, max_lines=500)
        mgr.write("INFO", "DebateEngine", "Debate started on topic: AI ethics")
    """

    def __init__(self, log_dir: str, max_files: int, max_lines: int) -> None:
        self.log_dir: Path = Path(log_dir)
        self.max_files: int = max_files
        self.max_lines: int = max_lines
        self._current_file: Path | None = None
        self._current_line_count: int = 0
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, level: str, component: str, message: str) -> None:
        """Append a formatted log entry to the current log file.

        Args:
            level: Severity label. Must be one of ``DEBUG``, ``INFO``,
                ``WARNING``, or ``ERROR``.
            component: Name of the subsystem emitting the entry
                (e.g. ``"FatherAgent"``).
            message: Human-readable log message.

        Raises:
            ValueError: If *level* is not a recognised severity label.
        """
        if level not in _VALID_LEVELS:
            raise ValueError(
                f"Invalid log level {level!r}. "
                f"Must be one of {sorted(_VALID_LEVELS)}."
            )
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        line = f"{timestamp} | {level} | {component} | {message}\n"
        target = self._get_current_file()
        with open(target, "a") as fh:
            fh.write(line)
        self._current_line_count += 1

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_current_file(self) -> Path:
        """Return the path that should receive the next log line.

        A new file is opened (and :meth:`_rotate` is called) whenever the
        current file has reached *max_lines* or no file has been opened yet.

        Returns:
            :class:`~pathlib.Path` of the active log file.
        """
        needs_new = (
            self._current_file is None
            or self._current_line_count >= self.max_lines
        )
        if needs_new:
            stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            self._current_file = self.log_dir / f"debate_{stamp}.log"
            self._current_line_count = 0
            self._rotate()
        return self._current_file  # type: ignore[return-value]

    def _rotate(self) -> None:
        """Evict the oldest log file when the file count meets *max_files*.

        Files are sorted lexicographically by name; because filenames embed a
        UTC timestamp this is equivalent to chronological order.  Eviction
        repeats until the count is strictly below *max_files* (one slot is
        reserved for the file about to be written).
        """
        existing = sorted(self.log_dir.glob("debate_*.log"))
        while len(existing) >= self.max_files:
            existing[0].unlink()
            existing = existing[1:]

"""ConfigLoader — loads and validates all JSON configuration files.

All configuration values are read from the ``config/`` directory at runtime.
No values are hardcoded in application source.
"""

import json
from pathlib import Path


class ConfigVersionError(Exception):
    """Raised when a config file's ``schema_version`` does not match expected."""


class ConfigLoader:
    """Loads ``setup.json``, ``rate_limits.json``, and ``pricing.json``.

    Args:
        config_dir: Path to the directory that contains the config JSON files.

    Attributes:
        config_dir: Resolved :class:`pathlib.Path` for the config directory.
        setup: Populated by :meth:`load_all`. Contains ``setup.json`` contents.
        rate_limits: Populated by :meth:`load_all`. Contains ``rate_limits.json``.
        pricing: Populated by :meth:`load_all`. Contains ``pricing.json``.

    Example::

        loader = ConfigLoader("config/")
        loader.load_all()
        model = loader.setup["agents"]["father"]["model"]
    """

    EXPECTED_SCHEMA_VERSION = "1.0"

    def __init__(self, config_dir: str) -> None:
        self.config_dir: Path = Path(config_dir)
        self.setup: dict = {}
        self.rate_limits: dict = {}
        self.pricing: dict = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_json(self, filename: str) -> dict:
        """Load and parse a single JSON file from *config_dir*.

        Args:
            filename: Name of the file to load (e.g. ``"setup.json"``).

        Returns:
            Parsed JSON content as a :class:`dict`.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        path = self.config_dir / filename
        try:
            with open(path) as fh:
                return json.load(fh)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file not found: {path}. "
                "Run 'make setup' or copy the file from the project template."
            ) from None

    def _validate_schema_version(self, data: dict, expected: str) -> None:
        """Assert that *data* carries the expected ``schema_version``.

        Args:
            data: Parsed config dict to inspect.
            expected: The version string that must be present.

        Raises:
            ConfigVersionError: If ``schema_version`` is missing or mismatched.
        """
        actual = data.get("schema_version")
        if actual != expected:
            raise ConfigVersionError(
                f"schema_version mismatch: expected {expected!r}, got {actual!r}. "
                "Update the config file or bump EXPECTED_SCHEMA_VERSION."
            )

    # ------------------------------------------------------------------
    # Public loaders
    # ------------------------------------------------------------------

    def load_setup(self) -> dict:
        """Load ``config/setup.json``.

        Returns:
            Parsed setup configuration dict.

        Raises:
            FileNotFoundError: If ``setup.json`` is missing.
            json.JSONDecodeError: If ``setup.json`` contains invalid JSON.
        """
        return self._load_json("setup.json")

    def load_rate_limits(self) -> dict:
        """Load ``config/rate_limits.json``.

        Returns:
            Parsed rate-limits configuration dict.

        Raises:
            FileNotFoundError: If ``rate_limits.json`` is missing.
            json.JSONDecodeError: If ``rate_limits.json`` contains invalid JSON.
        """
        return self._load_json("rate_limits.json")

    def load_pricing(self) -> dict:
        """Load ``config/pricing.json``.

        Returns:
            Parsed pricing configuration dict.

        Raises:
            FileNotFoundError: If ``pricing.json`` is missing.
            json.JSONDecodeError: If ``pricing.json`` contains invalid JSON.
        """
        return self._load_json("pricing.json")

    def load_all(self) -> None:
        """Load and validate all three config files.

        Populates :attr:`setup`, :attr:`rate_limits`, and :attr:`pricing`.

        Raises:
            FileNotFoundError: If any config file is missing.
            json.JSONDecodeError: If any config file contains invalid JSON.
            ConfigVersionError: If any file's ``schema_version`` is wrong.
        """
        self.setup = self.load_setup()
        self._validate_schema_version(self.setup, self.EXPECTED_SCHEMA_VERSION)

        self.rate_limits = self.load_rate_limits()
        self._validate_schema_version(self.rate_limits, self.EXPECTED_SCHEMA_VERSION)

        self.pricing = self.load_pricing()
        self._validate_schema_version(self.pricing, self.EXPECTED_SCHEMA_VERSION)

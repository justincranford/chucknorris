#!/usr/bin/env python3
"""Configuration module for Chuck Norris Quote Scraper.

This module handles loading configuration from files and environment.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration management for the scraper."""

    # Default configuration values
    DEFAULTS = {
        "sources_file": "scraper/sources.txt",
        "output_db": "scraper/quotes.db",
        "output_csv": "scraper/quotes.csv",
        "max_retries": 3,
        "retry_delay": 3,
        "request_timeout": 10,
        "max_workers": 4,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "verbose": False,
    }

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_file: Path to JSON config file (optional).
        """
        self._config: Dict[str, Any] = self.DEFAULTS.copy()

        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)

        self.load_from_env()

    def load_from_file(self, config_file: str) -> None:
        """Load configuration from JSON file.

        Args:
            config_file: Path to JSON config file.
        """
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                self._config.update(file_config)
                logging.debug(f"Loaded config from {config_file}")
        except Exception as e:  # pragma: no cover
            logging.warning(f"Failed to load config from {config_file}: {e}")

    def load_from_env(self) -> None:
        """Load configuration from environment variables.

        Environment variables should be prefixed with CN_ (Chuck Norris).
        """
        env_mappings: Dict[str, Any] = {
            "CN_SOURCES_FILE": "sources_file",
            "CN_OUTPUT_DB": "output_db",
            "CN_OUTPUT_CSV": "output_csv",
            "CN_MAX_RETRIES": ("max_retries", int),
            "CN_RETRY_DELAY": ("retry_delay", int),
            "CN_REQUEST_TIMEOUT": ("request_timeout", int),
            "CN_MAX_WORKERS": ("max_workers", int),
            "CN_USER_AGENT": "user_agent",
            "CN_VERBOSE": ("verbose", lambda x: x.lower() in ("true", "1", "yes")),
        }

        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                if isinstance(config_key, tuple):
                    key, converter = config_key
                    try:
                        self._config[key] = converter(value)  # type: ignore
                    except (ValueError, TypeError) as e:  # pragma: no cover
                        logging.warning(f"Invalid value for {env_var}: {e}")
                else:
                    self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary.

        Returns:
            Configuration dictionary.
        """
        return self._config.copy()


# Global config instance
_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """Get global configuration instance.

    Args:
        config_file: Path to config file (only used on first call).

    Returns:
        Config instance.
    """
    global _config
    if _config is None:
        _config = Config(config_file)
    return _config


def reset_config() -> None:
    """Reset global configuration (mainly for testing)."""
    global _config
    _config = None

"""Tests for the config module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from scraper.config import Config, get_config, reset_config


class TestConfig:
    """Tests for Config class."""

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.get("sources_file") == "scraper/sources.txt"
        assert config.get("output_db") == "scraper/quotes.db"
        assert config.get("max_retries") == 3
        assert config.get("max_workers") == 4

    def test_load_from_file(self):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"max_retries": 5, "max_workers": 8}, f)
            config_file = f.name

        try:
            config = Config(config_file)
            assert config.get("max_retries") == 5
            assert config.get("max_workers") == 8
        finally:
            os.unlink(config_file)

    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file uses defaults."""
        config = Config("nonexistent.json")
        assert config.get("max_retries") == 3

    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        os.environ["CN_MAX_RETRIES"] = "7"
        os.environ["CN_VERBOSE"] = "true"

        try:
            config = Config()
            assert config.get("max_retries") == 7
            assert config.get("verbose") is True
        finally:
            del os.environ["CN_MAX_RETRIES"]
            del os.environ["CN_VERBOSE"]

    def test_env_invalid_int(self):
        """Test invalid integer in environment variable."""
        os.environ["CN_MAX_RETRIES"] = "not-a-number"

        try:
            config = Config()
            # Should use default
            assert config.get("max_retries") == 3
        finally:
            del os.environ["CN_MAX_RETRIES"]

    def test_set_value(self):
        """Test setting configuration value."""
        config = Config()
        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"

    def test_get_with_default(self):
        """Test getting value with default."""
        config = Config()
        assert config.get("nonexistent_key", "default") == "default"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "sources_file" in config_dict

    def test_global_get_config(self):
        """Test global config instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test resetting global config."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_load_from_invalid_json_file(self):
        """Test loading from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("not valid json{")
            config_file = f.name

        try:
            config = Config(config_file)
            # Should use defaults on error
            assert config.get("max_retries") == 3
        finally:
            os.unlink(config_file)

    def test_env_boolean_variants(self):
        """Test various boolean representations in environment."""
        test_cases = [
            ("1", True),
            ("yes", True),
            ("TRUE", True),
            ("false", False),
            ("0", False),
            ("no", False),
        ]

        for value, expected in test_cases:
            os.environ["CN_VERBOSE"] = value
            try:
                config = Config()
                assert config.get("verbose") == expected
                reset_config()
            finally:
                if "CN_VERBOSE" in os.environ:
                    del os.environ["CN_VERBOSE"]

    def test_env_all_string_configs(self):
        """Test all string-based environment variables."""
        os.environ["CN_SOURCES_FILE"] = "custom/sources.txt"
        os.environ["CN_OUTPUT_DB"] = "custom/db.db"
        os.environ["CN_OUTPUT_CSV"] = "custom/csv.csv"
        os.environ["CN_USER_AGENT"] = "Custom Agent"

        try:
            config = Config()
            assert config.get("sources_file") == "custom/sources.txt"
            assert config.get("output_db") == "custom/db.db"
            assert config.get("output_csv") == "custom/csv.csv"
            assert config.get("user_agent") == "Custom Agent"
        finally:
            for key in ["CN_SOURCES_FILE", "CN_OUTPUT_DB", "CN_OUTPUT_CSV", "CN_USER_AGENT"]:
                if key in os.environ:
                    del os.environ[key]

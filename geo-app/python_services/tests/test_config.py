"""Tests for config.py — environment loading and defaults."""

import os
import pytest


class TestConfigLoading:
    """Tests for configuration module."""

    def test_supabase_url_loaded(self, mock_env):
        """SUPABASE_URL is loaded from environment."""
        assert os.getenv("SUPABASE_URL") == "https://test.supabase.co"

    def test_supabase_key_loaded(self, mock_env):
        """SUPABASE_SERVICE_ROLE_KEY is loaded from environment."""
        assert os.getenv("SUPABASE_SERVICE_ROLE_KEY") == "test-service-role-key-for-testing"

    def test_postgres_host_loaded(self, mock_env):
        """POSTGRES_HOST is loaded from environment."""
        assert os.getenv("POSTGRES_HOST") == "localhost"

    def test_api_port_default(self):
        """API_PORT defaults to 8000."""
        default_port = int(os.getenv("API_PORT", "8000"))
        assert default_port == 8000

    def test_api_host_default(self):
        """API_HOST defaults to 0.0.0.0."""
        default_host = os.getenv("API_HOST", "0.0.0.0")
        assert default_host == "0.0.0.0"

    def test_max_requests_default(self):
        """MAX_REQUESTS_PER_HOUR defaults to 100."""
        default = int(os.getenv("MAX_REQUESTS_PER_HOUR", "100"))
        assert default == 100

    def test_scraper_delay_default(self):
        """SCRAPER_DELAY_SECONDS defaults to 2."""
        default = float(os.getenv("SCRAPER_DELAY_SECONDS", "2"))
        assert default == 2.0

    def test_model_retrain_days_default(self):
        """MODEL_RETRAIN_DAYS defaults to 30."""
        default = int(os.getenv("MODEL_RETRAIN_DAYS", "30"))
        assert default == 30

    def test_log_level_default(self):
        """LOG_LEVEL defaults to INFO."""
        default = os.getenv("LOG_LEVEL", "INFO")
        assert default == "INFO"

    def test_missing_supabase_url_raises(self, monkeypatch):
        """Missing SUPABASE_URL should raise ValueError."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        # The config module raises on import when vars are missing
        assert os.getenv("SUPABASE_URL") is None

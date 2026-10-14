import logging
import os
import tempfile
from pathlib import Path
import pytest

from ziplime.utils.bundle_utils import (
    get_asset_data_source,
    get_bundle_service,
    get_data_source,
    get_exchange,
    get_fundamental_data_provider,
    get_market_data_source,
)
from ziplime.utils.logging_utils import configure_logging


def test_get_bundle_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = get_bundle_service(bundle_storage_path=tmpdir)
        assert service is not None


def test_get_asset_and_market_data_source():
    # "yahoo" is a registered provider
    src = get_asset_data_source("yahoo")
    assert src is not None

    mkt = get_market_data_source("yahoo")
    assert mkt is not None

    alias = get_data_source("yahoo")
    assert alias is not None


def test_get_data_source_lime_trader_sdk_missing_env(monkeypatch):
    monkeypatch.delenv("LIME_SDK_CREDENTIALS_FILE", raising=False)
    with pytest.raises(ValueError, match="Missing LIME_SDK_CREDENTIALS_FILE"):
        get_data_source("lime-trader-sdk")


def test_get_fundamental_data_provider():
    with pytest.raises(Exception, match="Unsupported fundamental data provider"):
        get_fundamental_data_provider("unsupported")


def test_get_fundamental_data_provider_limex_hub(monkeypatch):
    monkeypatch.delenv("LIMEX_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Missing LIMEX_API_KEY"):
        get_fundamental_data_provider("limex-hub")

    monkeypatch.setenv("LIMEX_API_KEY", "dummy_key")
    provider = get_fundamental_data_provider("limex-hub")
    assert provider is not None


def test_get_exchange():
    with pytest.raises(Exception, match="Unsupported live market data provider"):
        get_exchange("unsupported")


def test_get_exchange_lime_trader_sdk(monkeypatch):
    monkeypatch.delenv("LIME_SDK_CREDENTIALS_FILE", raising=False)
    with pytest.raises(ValueError, match="Missing LIME_SDK_CREDENTIALS_FILE"):
        get_exchange("lime-trader-sdk")


def test_configure_logging():
    # Console only
    configure_logging(level=logging.DEBUG)

    # With file
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        configure_logging(level=logging.INFO, file_name=str(log_file))
        assert log_file.exists()

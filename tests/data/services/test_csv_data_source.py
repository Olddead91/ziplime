import datetime
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import polars as pl
import pytest

from ziplime.constants.data_type import DataType
from ziplime.data.services.csv_data_source import CSVDataSource
from ziplime.utils.calendar_utils import get_calendar


@pytest.fixture
def sample_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    content = (
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-02 16:00:00,100.0,105.0,95.0,102.0,1000\n"
        "2024-01-03 16:00:00,102.0,108.0,101.0,107.0,1500\n"
    )
    csv_path.write_text(content)
    return str(csv_path)


@pytest.mark.asyncio
async def test_csv_data_source_load(sample_csv, monkeypatch):
    calendar = get_calendar("XNYS")
    asset_service = MagicMock()

    # Mock _process_data to avoid full pipeline / asset resolution
    async def mock_process_data(data, **kwargs):
        return data.with_columns(pl.lit(1).alias("sid"))

    monkeypatch.setattr("ziplime.data.services.csv_data_source._process_data", mock_process_data)

    mapping = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    source = CSVDataSource(
        name="test_csv",
        csv_file_name=sample_csv,
        column_mapping=mapping,
        frequency=datetime.timedelta(days=1),
        date_column_name="Date",
        date_format="%Y-%m-%d %H:%M:%S",
        data_frequency_use_window_end=False,
        symbols=["AAPL"],
        asset_service=asset_service,
        trading_calendar=calendar,
        data_type=DataType.MARKET_DATA,
    )

    df = await source.load_data_in_memory()
    assert source.data is not None
    assert "price" in df.columns
    assert "close" in df.columns
    assert len(df) == 2

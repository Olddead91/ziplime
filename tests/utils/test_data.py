from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest

from ziplime.utils.data import get_fundamental_data


def test_get_fundamental_data_unsupported_frequency():
    bar_data = MagicMock()
    context = MagicMock()
    with pytest.raises(Exception, match="Currently only frequency of 1 quarter is supported"):
        get_fundamental_data(bar_data, context, "AAPL", "pe_ratio", 4, "1d")


def test_get_fundamental_data_quarterly():
    bar_data = MagicMock()
    bar_data.current_session = pd.Timestamp("2024-03-31")

    context = MagicMock()
    bundle = MagicMock()
    context.fundamental_data_bundle = bundle

    bundle.first_trading_day = pd.Timestamp("2023-01-01")
    # Date range from start_date to end_date
    # 4 bars * 92 days = 368 days before 2024-03-31 -> 2023-03-29
    dr = pd.date_range("2023-03-29", "2024-03-31", freq="D")
    raw_array = np.full((len(dr), 1), 15.0)
    bundle.load_raw_arrays_full_range.return_value = [raw_array]

    res = get_fundamental_data(
        bar_data=bar_data,
        context=context,
        assets="AAPL",
        fields="pe_ratio",
        bar_count=4,
        frequency="1q",
        fillna=0.0,
    )

    assert isinstance(res, pd.Series)
    assert not res.empty


def test_get_fundamental_data_start_before_first_date():
    bar_data = MagicMock()
    bar_data.current_session = pd.Timestamp("2024-03-31")

    context = MagicMock()
    bundle = MagicMock()
    context.fundamental_data_bundle = bundle

    # First trading day is after the calculated start_date
    bundle.first_trading_day = pd.Timestamp("2023-08-01")
    dr = pd.date_range("2023-08-01", "2024-03-31", freq="D")
    raw_array = np.full((len(dr), 1), 20.0)
    bundle.load_raw_arrays_full_range.return_value = [raw_array]

    res = get_fundamental_data(
        bar_data=bar_data,
        context=context,
        assets="AAPL",
        fields="pe_ratio",
        bar_count=4,
        frequency="1q",
    )

    assert isinstance(res, pd.Series)

import numpy as np
import pandas as pd
import pytest

from ziplime.utils.pandas_utils import (
    _sort_set_none_first,
    _union_all,
    categorical_df_concat,
    empty_dataframe,
    explode,
    ignore_pandas_nan_categorical_warning,
    nearest_unequal_elements,
    timedelta_to_integral_seconds,
)


def test_explode():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, index=["r1", "r2"])
    idx, cols, vals = explode(df)
    assert list(idx) == ["r1", "r2"]
    assert list(cols) == ["a", "b"]
    np.testing.assert_array_equal(vals, np.array([[1, 3], [2, 4]]))


def test_nearest_unequal_elements():
    dts = pd.date_range("2024-01-02", periods=4, freq="D")

    # Before first
    assert nearest_unequal_elements(dts, pd.Timestamp("2024-01-01")) == (None, dts[0])

    # After last
    assert nearest_unequal_elements(dts, pd.Timestamp("2024-01-10")) == (dts[-1], None)

    # Exactly matching an internal element
    assert nearest_unequal_elements(dts, pd.Timestamp("2024-01-03")) == (dts[0], dts[2])

    # Between elements
    assert nearest_unequal_elements(dts, pd.Timestamp("2024-01-03 12:00:00")) == (dts[1], dts[2])

    # Empty
    empty_dts = pd.DatetimeIndex([])
    assert nearest_unequal_elements(empty_dts, pd.Timestamp("2024-01-01")) == (None, None)

    # Validations
    non_unique = pd.DatetimeIndex(["2024-01-01", "2024-01-01"])
    with pytest.raises(ValueError, match="dts must be unique"):
        nearest_unequal_elements(non_unique, pd.Timestamp("2024-01-01"))

    non_monotonic = pd.DatetimeIndex(["2024-01-02", "2024-01-01"])
    with pytest.raises(ValueError, match="dts must be sorted"):
        nearest_unequal_elements(non_monotonic, pd.Timestamp("2024-01-01"))


def test_timedelta_to_integral_seconds():
    delta = pd.Timedelta(minutes=5, seconds=12)
    assert timedelta_to_integral_seconds(delta) == 312


def test_ignore_pandas_nan_categorical_warning():
    with ignore_pandas_nan_categorical_warning():
        s = pd.Series(["a", "b", None], dtype="category")
        assert len(s) == 3


def test_categorical_df_concat():
    df1 = pd.DataFrame({"cat": pd.Categorical(["a", "b"]), "val": [1, 2]})
    df2 = pd.DataFrame({"cat": pd.Categorical(["b", "c"]), "val": [3, 4]})

    res = categorical_df_concat([df1, df2], inplace=False)
    assert len(res) == 4
    assert list(res["cat"]) == ["a", "b", "b", "c"]
    assert set(res["cat"].cat.categories) == {"a", "b", "c"}

    # Inplace mode
    res_inplace = categorical_df_concat([df1, df2], inplace=True)
    assert len(res_inplace) == 4

    # Mismatched columns raises
    df3 = pd.DataFrame({"different": [1, 2]})
    with pytest.raises(ValueError, match="Input DataFrames must have the same columns"):
        categorical_df_concat([df1, df3])


def test_sort_set_none_first_and_union_all():
    assert _union_all([[1, 2], [2, 3]]) == {1, 2, 3}
    assert _sort_set_none_first({3, 1, 2}) == [1, 2, 3]
    assert _sort_set_none_first({3, None, 1}) == [None, 1, 3]


def test_empty_dataframe():
    df = empty_dataframe(("a", "int64"), ("b", "float64"))
    assert df.empty
    assert list(df.columns) == ["a", "b"]
    assert df.dtypes["a"] == np.int64
    assert df.dtypes["b"] == np.float64

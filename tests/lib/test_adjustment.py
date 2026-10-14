import numpy as np
import pandas as pd
import pytest

from ziplime.lib.adjustment import (
    AdjustmentKind,
    BooleanOverwrite,
    Datetime64Overwrite,
    Float641DArrayOverwrite,
    Float64Add,
    Float64Multiply,
    Float64Overwrite,
    Int64Overwrite,
    ObjectOverwrite,
    choose_adjustment_type,
    datetime_to_int,
    get_adjustment_locs,
    make_adjustment_from_indices,
    make_adjustment_from_labels,
)


def test_float64_adjustments():
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])

    # Multiply
    adj_mul = Float64Multiply(0, 0, 0, 1, 2.0)
    adj_mul.mutate(arr)
    np.testing.assert_array_equal(arr, [[2.0, 4.0], [3.0, 4.0]])

    # Add
    adj_add = Float64Add(1, 1, 0, 1, 10.0)
    adj_add.mutate(arr)
    np.testing.assert_array_equal(arr, [[2.0, 4.0], [13.0, 14.0]])

    # Overwrite
    adj_ovw = Float64Overwrite(0, 1, 0, 0, 0.0)
    adj_ovw.mutate(arr)
    np.testing.assert_array_equal(arr, [[0.0, 4.0], [0.0, 14.0]])


def test_float64_1d_array_overwrite():
    arr = np.arange(9, dtype=float).reshape(3, 3)
    adj = Float641DArrayOverwrite(
        first_row=0,
        last_row=2,
        first_col=1,
        last_col=1,
        values=np.array([100.0, 200.0, 300.0]),
    )
    adj.mutate(arr)
    expected = np.array([[0.0, 100.0, 2.0], [3.0, 200.0, 5.0], [6.0, 300.0, 8.0]])
    np.testing.assert_array_equal(arr, expected)

    with pytest.raises(ValueError, match="Mismatch: got 2 values"):
        Float641DArrayOverwrite(0, 2, 0, 0, np.array([1.0, 2.0]))


def test_other_overwrites():
    # Int64
    arr_int = np.zeros((2, 2), dtype=np.int64)
    Int64Overwrite(0, 1, 0, 1, 42).mutate(arr_int)
    np.testing.assert_array_equal(arr_int, [[42, 42], [42, 42]])

    # Boolean
    arr_bool = np.zeros((2, 2), dtype=np.uint8)
    BooleanOverwrite(0, 0, 0, 1, True).mutate(arr_bool)
    np.testing.assert_array_equal(arr_bool, [[1, 1], [0, 0]])

    # Object (works on LabelArray)
    from ziplime.lib.labelarray import LabelArray

    arr_la = LabelArray(np.array([["a", "b"], ["c", "d"]], dtype=object), missing_value="missing")
    ObjectOverwrite(1, 1, 1, 1, "a").mutate(arr_la)
    assert arr_la[1, 1] == "a"


def test_datetime_to_int_and_overwrite():
    ts = pd.Timestamp("2024-01-01")
    val_int = datetime_to_int(ts)
    assert val_int == ts.value

    dt64 = np.datetime64("2024-01-01", "ns")
    assert datetime_to_int(dt64) == ts.value

    with pytest.raises(TypeError, match="Expected datetime64"):
        datetime_to_int(12345)

    with pytest.raises(TypeError, match="Expected datetime64\\[ns\\]"):
        datetime_to_int(np.datetime64("2024-01-01", "D"))

    arr_dt = np.zeros((2, 2), dtype="datetime64[ns]").view("int64")
    Datetime64Overwrite(0, 0, 0, 0, ts).mutate(arr_dt)
    assert arr_dt[0, 0] == ts.value


def test_choose_adjustment_type_and_factories():
    assert choose_adjustment_type(AdjustmentKind.MULTIPLY, 1.5) is Float64Multiply
    assert choose_adjustment_type(AdjustmentKind.ADD, 1.5) is Float64Add
    assert choose_adjustment_type(AdjustmentKind.OVERWRITE, 1.5) is Float64Overwrite
    assert choose_adjustment_type(AdjustmentKind.OVERWRITE, 10) is Int64Overwrite
    assert choose_adjustment_type(AdjustmentKind.OVERWRITE, True) is BooleanOverwrite
    assert choose_adjustment_type(AdjustmentKind.OVERWRITE, "foo") is ObjectOverwrite

    with pytest.raises(TypeError, match="ADD and MULTIPLY adjustments are only supported"):
        choose_adjustment_type(AdjustmentKind.MULTIPLY, "foo")

    with pytest.raises(TypeError, match="Don't know how to make overwrite adjustments"):
        choose_adjustment_type(AdjustmentKind.OVERWRITE, [1, 2, 3])

    adj = make_adjustment_from_indices(0, 1, 0, 1, AdjustmentKind.ADD, 5.0)
    assert isinstance(adj, Float64Add)


def test_labels_and_adjustment_locs():
    dates = pd.date_range("2024-01-01", "2024-01-10")
    assets = pd.Index([10, 20, 30])

    locs = get_adjustment_locs(
        dates,
        assets,
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-05"),
        20,
    )
    assert locs == (2, 4, 1)

    # Start date as NaT or None
    locs_nat = get_adjustment_locs(
        dates,
        assets,
        pd.NaT,
        pd.Timestamp("2024-01-05"),
        10,
    )
    assert locs_nat == (0, 4, 0)

    adj = make_adjustment_from_labels(
        dates,
        assets,
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-05"),
        20,
        AdjustmentKind.OVERWRITE,
        99.0,
    )
    assert isinstance(adj, Float64Overwrite)
    assert adj.first_row == 2
    assert adj.last_row == 4
    assert adj.first_col == 1
    assert adj.value == 99.0

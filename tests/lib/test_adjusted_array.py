import numpy as np
import pytest

from ziplime.errors import WindowLengthNotPositive, WindowLengthTooLong
from ziplime.lib.adjusted_array import (
    AdjustedArray,
    can_represent_dtype,
    ensure_adjusted_array,
    ensure_ndarray,
    is_categorical,
)
from ziplime.lib.adjustment import Float64Multiply
from ziplime.lib.labelarray import LabelArray
from ziplime.lib.windowtemplate import AdjustedArrayWindow, Exhausted


def test_can_represent_and_is_categorical():
    assert can_represent_dtype(np.dtype("float64"))
    assert can_represent_dtype(np.dtype("int64"))
    assert can_represent_dtype(np.dtype("bool"))
    assert can_represent_dtype(np.dtype("datetime64[ns]"))
    assert can_represent_dtype(np.dtype(object))
    assert is_categorical(np.dtype(object))
    assert is_categorical(np.dtype("S5"))
    assert not is_categorical(np.dtype("float64"))


def test_ensure_helpers():
    raw = np.array([[1.0, 2.0], [3.0, 4.0]])
    adj_arr = ensure_adjusted_array(raw, missing_value=np.nan)
    assert isinstance(adj_arr, AdjustedArray)
    assert ensure_adjusted_array(adj_arr, missing_value=np.nan) is adj_arr

    with pytest.raises(TypeError):
        ensure_adjusted_array([1, 2, 3], missing_value=np.nan)

    nd = ensure_ndarray(adj_arr)
    assert isinstance(nd, np.ndarray)
    assert ensure_ndarray(raw) is raw

    with pytest.raises(TypeError):
        ensure_ndarray("not-an-array")


def test_adjusted_array_traversal_and_adjustments():
    data = np.arange(12, dtype=float).reshape(6, 2)
    # Adjustment: at row 3, multiply first 2 rows by 2.0
    adj = Float64Multiply(first_row=0, last_row=1, first_col=0, last_col=1, value=2.0)
    adjustments = {3: [adj]}

    adj_arr = AdjustedArray(data=data, adjustments=adjustments, missing_value=np.nan)
    assert adj_arr.dtype == np.float64
    assert adj_arr.data.shape == (6, 2)

    # Traverse window of length 3
    window_iter = adj_arr.traverse(window_length=3, offset=0)
    assert isinstance(window_iter, AdjustedArrayWindow)

    # Window 0 (anchor 2: rows 0..2)
    w0 = next(window_iter)
    assert w0.shape == (3, 2)
    np.testing.assert_array_equal(w0, data[0:3])

    # Window 1 (anchor 3: rows 1..3, adjustment at 3 has triggered)
    w1 = next(window_iter)
    assert w1.shape == (3, 2)
    # Row 1 was multiplied by 2.0
    np.testing.assert_array_equal(w1[0], data[1] * 2.0)


def test_adjusted_array_window_seek_and_repr():
    data = np.arange(10, dtype=float).reshape(5, 2)
    adj_arr = AdjustedArray(data=data, adjustments={}, missing_value=np.nan)

    window_iter = adj_arr.traverse(window_length=2)
    repr_str = repr(window_iter)
    assert "AdjustedArrayWindow" in repr_str

    # seek to next target anchor
    w = window_iter.seek(2)
    assert w.shape == (2, 2)

    with pytest.raises(Exception, match="Can not access data after window has passed"):
        window_iter.seek(1)


def test_adjusted_array_invalid_window_params():
    data = np.arange(10, dtype=float).reshape(5, 2)
    adj_arr = AdjustedArray(data=data, adjustments={}, missing_value=np.nan)

    with pytest.raises(WindowLengthNotPositive):
        adj_arr.traverse(window_length=0)

    with pytest.raises(WindowLengthTooLong):
        adj_arr.traverse(window_length=10)


def test_adjusted_array_copy():
    data = np.arange(10, dtype=float).reshape(5, 2)
    adj_arr = AdjustedArray(data=data, adjustments={}, missing_value=np.nan)

    copied = adj_arr.copy()
    assert copied is not adj_arr
    np.testing.assert_array_equal(copied.data, adj_arr.data)


def test_adjusted_array_labelarray():
    raw = np.array([["a", "b"], ["c", "d"], ["e", "f"]], dtype=object)
    la = LabelArray(raw, missing_value="missing")
    adj_arr = AdjustedArray(data=la, adjustments={}, missing_value="missing")

    assert isinstance(adj_arr.data, LabelArray)
    window_iter = adj_arr.traverse(window_length=2)
    w = next(window_iter)
    assert w.shape == (2, 2)

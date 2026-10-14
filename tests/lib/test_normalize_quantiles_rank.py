import numpy as np
import pytest

from ziplime.lib.normalize import naive_grouped_rowwise_apply
from ziplime.lib.quantiles import quantiles
from ziplime.lib.rank import (
    grouped_masked_is_maximal,
    masked_rankdata_2d,
    rankdata_1d_descending,
    rankdata_2d_ordinal,
)


def test_naive_grouped_rowwise_apply():
    data = np.array([[1.0, 2.0, 3.0], [2.0, 3.0, 4.0], [5.0, 6.0, 7.0]])
    labels = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 2]])

    result = naive_grouped_rowwise_apply(data, labels, lambda row: row - row.min())
    expected = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 2.0], [0.0, 0.0, 0.0]])
    np.testing.assert_array_equal(result, expected)


def test_quantiles():
    data = np.array([[10.0, 20.0, 30.0, 40.0], [40.0, 30.0, 20.0, 10.0]])
    q = quantiles(data, 2)
    assert q.shape == (2, 4)
    np.testing.assert_array_equal(q[0], [0, 0, 1, 1])
    np.testing.assert_array_equal(q[1], [1, 1, 0, 0])


def test_rankdata_1d_descending():
    arr = np.array([10.0, 30.0, 20.0])
    res = rankdata_1d_descending(arr, method="ordinal")
    np.testing.assert_array_equal(res, [3.0, 1.0, 2.0])


def test_rankdata_2d_ordinal():
    arr = np.array([[10.0, 30.0, 20.0], [5.0, 1.0, 8.0]])
    res = rankdata_2d_ordinal(arr)
    expected = np.array([[1.0, 3.0, 2.0], [2.0, 1.0, 3.0]])
    np.testing.assert_array_equal(res, expected)


def test_masked_rankdata_2d():
    data = np.array([[10.0, 30.0, 20.0], [5.0, 1.0, 8.0]])
    mask = np.array([[True, True, False], [True, True, True]])

    # Ascending ordinal
    res_asc = masked_rankdata_2d(data, mask, missing_value=np.nan, method="ordinal", ascending=True)
    assert np.isnan(res_asc[0, 2])
    assert res_asc[0, 0] == 1.0
    assert res_asc[0, 1] == 2.0

    # Descending average
    res_desc = masked_rankdata_2d(data, mask, missing_value=np.nan, method="average", ascending=False)
    assert res_desc[1, 2] == 1.0  # 8.0 is max, so rank 1 descending
    assert res_desc[1, 0] == 2.0  # 5.0
    assert res_desc[1, 1] == 3.0  # 1.0

    with pytest.raises(TypeError, match="Can't compute rankdata on array of dtype"):
        masked_rankdata_2d(data.astype(np.complex128), mask, missing_value=0, method="ordinal", ascending=True)


def test_grouped_masked_is_maximal():
    data = np.array([[10, 20, 15, 5], [30, 40, 25, 50]])
    groupby = np.array([[1, 1, 2, 2], [1, 1, 2, 2]])
    mask = np.array([[True, True, True, True], [True, False, True, True]], dtype=np.uint8)

    max_mask = grouped_masked_is_maximal(data, groupby, mask)
    # Row 0: group 1 values [10, 20] -> max is col 1 (20); group 2 values [15, 5] -> max is col 2 (15)
    np.testing.assert_array_equal(max_mask[0], [False, True, True, False])
    # Row 1: group 1 values [30 (valid), 40 (masked)] -> max is col 0 (30); group 2 values [25, 50] -> max is col 3 (50)
    np.testing.assert_array_equal(max_mask[1], [True, False, False, True])

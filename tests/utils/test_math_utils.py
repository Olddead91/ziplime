import math
import numpy as np
import pytest

from ziplime.utils.math_utils import (
    nanargmax,
    nanargmin,
    nanmax,
    nanmean,
    nanmedian,
    nanmin,
    nanstd,
    nansum,
    number_of_decimal_places,
    round_if_near_integer,
    tolerant_equals,
)


def test_tolerant_equals():
    assert tolerant_equals(1.0, 1.0)
    assert tolerant_equals(1.0, 1.0 + 1e-8)
    assert not tolerant_equals(1.0, 1.01)

    # equal_nan
    assert tolerant_equals(float("nan"), float("nan"), equal_nan=True)
    assert not tolerant_equals(float("nan"), float("nan"), equal_nan=False)
    assert not tolerant_equals(float("nan"), 1.0, equal_nan=True)


def test_round_if_near_integer():
    assert round_if_near_integer(3.00001, epsilon=1e-4) == 3
    assert round_if_near_integer(2.99999, epsilon=1e-4) == 3
    assert round_if_near_integer(3.05, epsilon=1e-4) == 3.05


def test_number_of_decimal_places():
    assert number_of_decimal_places(1) == 0
    assert number_of_decimal_places(3.14) == 2
    assert number_of_decimal_places("3.140") == 3
    assert number_of_decimal_places(100) == 0


def test_nan_aggregations():
    arr = np.array([1.0, np.nan, 3.0, 5.0])
    assert nanmean(arr) == 3.0
    assert nansum(arr) == 9.0
    assert nanmin(arr) == 1.0
    assert nanmax(arr) == 5.0
    assert nanmedian(arr) == 3.0
    assert nanargmin(arr) == 0
    assert nanargmax(arr) == 3
    assert math.isclose(nanstd(arr), np.std([1.0, 3.0, 5.0]))

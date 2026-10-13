import re
import numpy as np
import pandas as pd
import pytest

from ziplime.lib.labelarray import (
    CategoryMismatch,
    LabelArray,
    MissingValueMismatch,
    labelarray_where,
)


def test_labelarray_construction_and_basic_attributes():
    raw = np.array(["apple", "banana", "apple", "cherry", None], dtype=object)
    la = LabelArray(raw, missing_value=None)

    assert la.missing_value is None
    assert la.has_label("apple")
    assert la.has_label("banana")
    assert not la.has_label("orange")
    assert la.missing_value_code == 0
    assert la.shape == (5,)

    # Slicing keeps categories
    sliced = la[:3]
    assert isinstance(sliced, LabelArray)
    assert sliced.categories is la.categories
    assert list(sliced.as_string_array()) == ["apple", "banana", "apple"]


def test_labelarray_from_categorical():
    cat = pd.Categorical(["a", "b", "a", "c"])
    la = LabelArray.from_categorical(cat, missing_value=None)
    assert list(la.as_string_array()) == ["a", "b", "a", "c"]


def test_labelarray_indexing_and_setitem():
    raw = np.array([["a", "b"], ["c", "d"]], dtype=object)
    la = LabelArray(raw, missing_value="missing")

    assert la[0, 0] == "a"
    assert la[1, 1] == "d"

    # Setting scalar
    la[0, 0] = "b"
    assert la[0, 0] == "b"

    with pytest.raises(ValueError, match="not in LabelArray categories"):
        la[0, 0] = "unknown_val"

    la.set_scalar((1, 1), "c")
    assert la[1, 1] == "c"

    with pytest.raises(ValueError, match="not in LabelArray categories"):
        la.set_scalar((1, 1), "unknown_val")


def test_labelarray_conversions():
    raw = np.array(["cat", "dog", "bird"], dtype=object)
    la = LabelArray(raw, missing_value="missing")

    # as_int_array
    int_arr = la.as_int_array()
    assert isinstance(int_arr, np.ndarray)

    # as_categorical
    cat = la.as_categorical()
    assert isinstance(cat, pd.Categorical)

    # 2D as_categorical fails
    la_2d = LabelArray(raw.reshape(1, 3), missing_value="missing")
    with pytest.raises(ValueError, match="Can't convert a 2D array"):
        la_2d.as_categorical()

    # as_categorical_frame
    frame = la_2d.as_categorical_frame(index=[0], columns=["c1", "c2", "c3"])
    assert frame.shape == (1, 3)

    # astype
    assert list(la.astype(object)) == ["cat", "dog", "bird"]
    assert la.astype(np.dtype("S5")).dtype.kind == "S"
    with pytest.raises(TypeError, match="can only be converted"):
        la.astype(int)


def test_labelarray_missing_and_equality():
    raw1 = np.array(["a", "b", None], dtype=object)
    raw2 = np.array(["a", "c", None], dtype=object)
    la1 = LabelArray(raw1, missing_value=None, categories=[None, "a", "b", "c"])
    la2 = LabelArray(raw2, missing_value=None, categories=[None, "a", "b", "c"])

    # is_missing / not_missing
    np.testing.assert_array_equal(la1.is_missing(), [False, False, True])
    np.testing.assert_array_equal(la1.not_missing(), [True, True, False])

    # == with another LabelArray
    eq_res = (la1 == la2)
    # At index 2, both are missing, so equality should be False (NaN semantics)
    np.testing.assert_array_equal(eq_res, [True, False, False])

    # == with scalar
    np.testing.assert_array_equal(la1 == "a", [True, False, False])

    # != with scalar
    np.testing.assert_array_equal(la1 != "a", [False, True, False])

    # Mismatched missing values
    la_diff_mv = LabelArray(raw1, missing_value="missing")
    with pytest.raises(MissingValueMismatch):
        _ = la1 == la_diff_mv

    # Mismatched categories
    la_diff_cat = LabelArray(raw1, missing_value=None, categories=[None, "a", "b", "other"])
    with pytest.raises(CategoryMismatch):
        _ = la1 == la_diff_cat


def test_labelarray_string_methods():
    raw = np.array(["prefix_foo_suffix", "foo_bar", "prefix_bar", None], dtype=object)
    la = LabelArray(raw, missing_value=None)

    np.testing.assert_array_equal(la.startswith("prefix"), [True, False, True, False])
    np.testing.assert_array_equal(la.endswith("suffix"), [True, False, False, False])
    np.testing.assert_array_equal(la.has_substring("bar"), [False, True, True, False])
    np.testing.assert_array_equal(la.matches(re.compile(r"^prefix.*")), [True, False, True, False])
    np.testing.assert_array_equal(la.element_of({"foo_bar", "other"}), [False, True, False, False])


def test_labelarray_map():
    raw = np.array(["low", "high", "low", None], dtype=object)
    la = LabelArray(raw, missing_value=None)

    mapped = la.map(lambda s: s.upper())
    assert list(mapped.as_string_array()) == ["LOW", "HIGH", "LOW", None]


def test_labelarray_where():
    c = np.array([True, False, True])
    la1 = LabelArray(np.array(["a", "b", "c"], dtype=object), missing_value="missing")
    la2 = LabelArray(np.array(["x", "y", "z"], dtype=object), missing_value="missing")

    res = labelarray_where(c, la1, la2)
    assert list(res.as_string_array()) == ["a", "y", "c"]

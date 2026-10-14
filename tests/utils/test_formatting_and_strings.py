from ziplime.utils.formatting import bulleted_list as fmt_bulleted_list, plural, s
from ziplime.utils.sqlite_utils import group_into_chunks
from ziplime.utils.string_formatting import bulleted_list as str_bulleted_list
from ziplime.utils.string_utils import camel_case_to_snake_case


def test_camel_case_to_snake_case():
    assert camel_case_to_snake_case("HelloWorld") == "hello_world"
    assert camel_case_to_snake_case("camelCase") == "camel_case"
    assert camel_case_to_snake_case("already_snake") == "already_snake"
    assert camel_case_to_snake_case("A") == "a"
    assert camel_case_to_snake_case("") == ""


def test_string_formatting_bulleted_list():
    items = ["apple", "banana", "cherry"]
    result = str_bulleted_list(items, indent=4)
    expected = "    - apple\n    - banana\n    - cherry"
    assert result == expected

    # With max_count truncating items
    long_list = ["one", "two", "three", "four", "five"]
    truncated = str_bulleted_list(long_list, max_count=3, indent=2)
    assert truncated == "  - one\n  - two\n  - ...\n  - five"


def test_formatting_s_and_plural():
    assert s("apple", [1]) == "apple"
    assert s("apple", [1, 2]) == "apples"
    assert s("apple", []) == "apples"
    assert s("fox", [1, 2], suffix="es") == "foxes"

    assert plural("share", "shares", [1]) == "share"
    assert plural("share", "shares", [1, 2]) == "shares"
    assert plural("share", "shares", []) == "shares"


def test_formatting_bulleted_list():
    items = ["item1", "item2"]
    res = fmt_bulleted_list(items, indent=2, bullet_type="*")
    assert res == "  * item1\n  * item2"


def test_sqlite_utils_group_into_chunks():
    items = list(range(10))
    chunks = group_into_chunks(items, chunk_size=3)
    assert chunks == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    assert group_into_chunks([], chunk_size=5) == []
    assert group_into_chunks([1, 2], chunk_size=5) == [[1, 2]]

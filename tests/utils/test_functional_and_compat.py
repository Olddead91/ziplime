from ziplime.utils.compat import (
    ExitStack,
    consistent_round,
    contextmanager,
    escape_html,
    mappingproxy,
    unicode,
    wraps,
)
from ziplime.utils.functional import (
    apply,
    instance,
    invert,
    keysorted,
    set_attribute,
    with_doc,
    with_name,
)


def test_functional_apply_and_instance():
    def add(a, b):
        return a + b

    assert apply(add, 2, 3) == 5

    @instance
    class MySingleton:
        def __init__(self):
            self.x = 42

    assert MySingleton.x == 42


def test_functional_set_attribute_and_decorators():
    @with_name("custom_name")
    @with_doc("custom docstring")
    def func():
        return 1

    assert func.__name__ == "custom_name"
    assert func.__doc__ == "custom docstring"
    assert func() == 1

    @set_attribute("tag", "val")
    def tagged():
        pass

    assert tagged.tag == "val"


def test_functional_invert_and_keysorted():
    d = {"a": 1, "b": 2, "c": 1}
    assert invert(d) == {1: {"a", "c"}, 2: {"b"}}

    assert keysorted({"c": 1, "a": 2, "b": 3}) == [("a", 2), ("b", 3), ("c", 1)]


def test_compat_consistent_round():
    assert consistent_round(2.5) == 3
    assert consistent_round(2.4) == 2
    assert consistent_round(3.0) == 3
    assert consistent_round(3.7) == 4


def test_compat_reexports():
    assert callable(contextmanager)
    assert ExitStack is not None
    assert escape_html("<script>") == "&lt;script&gt;"
    mp = mappingproxy({"a": 1})
    assert mp["a"] == 1
    assert unicode is str
    assert callable(wraps)

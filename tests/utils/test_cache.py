import datetime
import pytest

from ziplime.utils.cache import CachedObject, Expired, ExpiringCache


def test_cached_object_lifecycle():
    now = datetime.datetime(2024, 1, 1, 12, 0)
    expires = datetime.datetime(2024, 1, 1, 13, 0)

    obj = CachedObject("value1", expires)
    assert obj.unwrap(now) == "value1"
    assert obj.unwrap(expires) == "value1"

    after = datetime.datetime(2024, 1, 1, 13, 1)
    with pytest.raises(Expired):
        obj.unwrap(after)

    assert obj._unsafe_get_value() == "value1"


def test_cached_object_always_expired():
    obj = CachedObject.expired()
    with pytest.raises(Expired):
        obj.unwrap(datetime.datetime(2024, 1, 1))


def test_expiring_cache_lifecycle_and_cleanup():
    cleaned_up = []

    def cleanup(val):
        cleaned_up.append(val)

    cache = ExpiringCache(cleanup=cleanup)
    expires = datetime.datetime(2024, 1, 1, 13, 0)

    cache.set("k1", "v1", expires)

    # Valid read before expiry
    assert cache.get("k1", datetime.datetime(2024, 1, 1, 12, 0)) == "v1"

    # Expired read
    with pytest.raises(KeyError):
        cache.get("k1", datetime.datetime(2024, 1, 1, 13, 1))

    assert cleaned_up == ["v1"]

    # Key is now deleted
    with pytest.raises(KeyError):
        cache.get("k1", datetime.datetime(2024, 1, 1, 12, 0))


def test_expiring_cache_missing_key():
    custom_dict = {}
    cache = ExpiringCache(cache=custom_dict)
    with pytest.raises(KeyError):
        cache.get("nonexistent", datetime.datetime(2024, 1, 1))

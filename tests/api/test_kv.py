import struct

import pytest

from consul import ConsulException


class TestConsul:
    def test_kv(self, consul_obj):
        c, _consul_version = consul_obj
        _index, data = c.kv.get("foo")
        assert data is None
        assert c.kv.put("foo", "bar") is True
        _index, data = c.kv.get("foo")
        assert data["Value"] == b"bar"

    def test_kv_wait(self, consul_obj):
        c, _consul_version = consul_obj
        assert c.kv.put("foo", "bar") is True
        index, _data = c.kv.get("foo")
        check, _data = c.kv.get("foo", index=index, wait="20ms")
        assert index == check

    def test_kv_encoding(self, consul_obj):
        c, _consul_version = consul_obj

        # test binary
        c.kv.put("foo", struct.pack("i", 1000))
        _index, data = c.kv.get("foo")
        assert struct.unpack("i", data["Value"]) == (1000,)

        # test unicode
        c.kv.put("foo", "bar")
        _index, data = c.kv.get("foo")
        assert data["Value"] == b"bar"

        # test empty-string comes back as `None`
        c.kv.put("foo", "")
        _index, data = c.kv.get("foo")
        assert data["Value"] is None

        # test None
        c.kv.put("foo", None)
        _index, data = c.kv.get("foo")
        assert data["Value"] is None

        # check unencoded values raises assert
        pytest.raises(AssertionError, c.kv.put, "foo", {1: 2})

    def test_kv_put_cas(self, consul_obj):
        c, _consul_version = consul_obj
        assert c.kv.put("foo", "bar", cas=50) is False
        assert c.kv.put("foo", "bar", cas=0) is True
        _index, data = c.kv.get("foo")

        assert c.kv.put("foo", "bar2", cas=data["ModifyIndex"] - 1) is False
        assert c.kv.put("foo", "bar2", cas=data["ModifyIndex"]) is True
        _index, data = c.kv.get("foo")
        assert data["Value"] == b"bar2"

    def test_kv_put_flags(self, consul_obj):
        c, _consul_version = consul_obj
        c.kv.put("foo", "bar")
        _index, data = c.kv.get("foo")
        assert data["Flags"] == 0

        assert c.kv.put("foo", "bar", flags=50) is True
        _index, data = c.kv.get("foo")
        assert data["Flags"] == 50

    def test_kv_recurse(self, consul_obj):
        c, _consul_version = consul_obj
        _index, data = c.kv.get("foo/", recurse=True)
        assert data is None

        c.kv.put("foo/", None)
        _index, data = c.kv.get("foo/", recurse=True)
        assert len(data) == 1

        c.kv.put("foo/bar1", "1")
        c.kv.put("foo/bar2", "2")
        c.kv.put("foo/bar3", "3")
        _index, data = c.kv.get("foo/", recurse=True)
        assert [x["Key"] for x in data] == ["foo/", "foo/bar1", "foo/bar2", "foo/bar3"]
        assert [x["Value"] for x in data] == [None, b"1", b"2", b"3"]

    def test_kv_delete(self, consul_obj):
        c, _consul_version = consul_obj
        c.kv.put("foo1", "1")
        c.kv.put("foo2", "2")
        c.kv.put("foo3", "3")
        _index, data = c.kv.get("foo", recurse=True)
        assert [x["Key"] for x in data] == ["foo1", "foo2", "foo3"]

        assert c.kv.delete("foo2") is True
        _index, data = c.kv.get("foo", recurse=True)
        assert [x["Key"] for x in data] == ["foo1", "foo3"]
        assert c.kv.delete("foo", recurse=True) is True
        _index, data = c.kv.get("foo", recurse=True)
        assert data is None

    def test_kv_delete_cas(self, consul_obj):
        c, _consul_version = consul_obj

        c.kv.put("foo", "bar")
        index, data = c.kv.get("foo")

        assert c.kv.delete("foo", cas=data["ModifyIndex"] - 1) is False
        assert c.kv.get("foo") == (index, data)

        assert c.kv.delete("foo", cas=data["ModifyIndex"]) is True
        index, data = c.kv.get("foo")
        assert data is None

    def test_kv_acquire_release(self, consul_obj):
        c, _consul_version = consul_obj

        pytest.raises(ConsulException, c.kv.put, "foo", "bar", acquire="foo")

        s1 = c.session.create()
        s2 = c.session.create()

        assert c.kv.put("foo", "1", acquire=s1) is True
        assert c.kv.put("foo", "2", acquire=s2) is False
        assert c.kv.put("foo", "1", acquire=s1) is True
        assert c.kv.put("foo", "1", release="foo") is False
        assert c.kv.put("foo", "2", release=s2) is False
        assert c.kv.put("foo", "2", release=s1) is True

        c.session.destroy(s1)
        c.session.destroy(s2)

    def test_kv_keys_only(self, consul_obj):
        c, _consul_version = consul_obj

        assert c.kv.put("bar", "4") is True
        assert c.kv.put("base/foo", "1") is True
        assert c.kv.put("base/base/foo", "5") is True

        _index, data = c.kv.get("base/", keys=True, separator="/")
        assert data == ["base/base/", "base/foo"]

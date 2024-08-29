import pytest

import consul


class TestSession:
    def test_session(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # session.create
        pytest.raises(consul.ConsulException, c.session.create, node="n2")
        pytest.raises(consul.ConsulException, c.session.create, dc="dc2")
        session_id = c.session.create("my-session")

        # session.list
        pytest.raises(consul.ConsulException, c.session.list, dc="dc2")
        _, sessions = c.session.list()
        assert [x["Name"] for x in sessions] == ["my-session"]

        # session.info
        pytest.raises(consul.ConsulException, c.session.info, session_id, dc="dc2")
        _index, session = c.session.info("1" * 36)
        assert session is None
        _index, session = c.session.info(session_id)
        assert session["Name"] == "my-session"

        # session.node
        node = session["Node"]
        pytest.raises(consul.ConsulException, c.session.node, node, dc="dc2")
        _, sessions = c.session.node(node)
        assert [x["Name"] for x in sessions] == ["my-session"]

        # session.destroy
        pytest.raises(consul.ConsulException, c.session.destroy, session_id, dc="dc2")
        assert c.session.destroy(session_id) is True
        _, sessions = c.session.list()
        assert sessions == []

    def test_session_delete_ttl_renew(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        s = c.session.create(behavior="delete", ttl=20)

        # attempt to renew an unknown session
        pytest.raises(consul.NotFound, c.session.renew, "1" * 36)

        session = c.session.renew(s)
        assert session["Behavior"] == "delete"
        assert session["TTL"] == "20s"

        # trying out the behavior
        assert c.kv.put("foo", "1", acquire=s) is True
        _index, data = c.kv.get("foo")
        assert data["Value"] == b"1"

        c.session.destroy(s)
        _index, data = c.kv.get("foo")
        assert data is None

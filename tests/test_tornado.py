import base64
import struct
import time

import pytest
from tornado import gen, ioloop
from tornado.ioloop import IOLoop

import consul
import consul.tornado

Check = consul.Check


@pytest.fixture(autouse=True)
def ensure_tornado_ioloop():
    assert isinstance(IOLoop.current(), IOLoop), "Not using Tornado's IOLoop!"


@pytest.fixture
def consul_obj(consul_port):
    c = consul.tornado.Consul(port=consul_port)
    yield c
    loop = IOLoop.current()
    loop.run_sync(c.close)


@pytest.fixture
def consul_acl_obj(acl_consul):
    c = consul.tornado.Consul(port=acl_consul.port, token=acl_consul.token)
    yield c
    loop = IOLoop.current()
    loop.run_sync(c.close)


class TestConsul:
    async def test_kv(self, consul_obj):
        c = consul_obj
        _index, data = await c.kv.get("foo")
        assert data is None
        response = await c.kv.put("foo", "bar")
        assert response is True
        _index, data = await c.kv.get("foo")
        assert data["Value"] == b"bar"

    async def test_kv_binary(self, consul_obj):
        c = consul_obj
        await c.kv.put("foo", struct.pack("i", 1000))
        _index, data = await c.kv.get("foo")
        assert struct.unpack("i", data["Value"]) == (1000,)

    def test_kv_missing(self, consul_obj):
        c = consul_obj

        @gen.coroutine
        def main():
            yield c.kv.put("index", "bump")
            index, data = yield c.kv.get("foo")
            assert data is None
            index, data = yield c.kv.get("foo", index=index)
            assert data["Value"] == b"bar"
            loop.stop()

        @gen.coroutine
        def put():
            yield c.kv.put("foo", "bar")

        loop = ioloop.IOLoop.current()
        loop.add_timeout(time.time() + (2.0 / 100), put)
        loop.run_sync(main)

    async def test_kv_put_flags(self, consul_obj):
        c = consul_obj
        yield c.kv.put("foo", "bar")
        _index, data = yield c.kv.get("foo")
        assert data["Flags"] == 0

        response = yield c.kv.put("foo", "bar", flags=50)
        assert response is True
        _index, data = yield c.kv.get("foo")
        assert data["Flags"] == 50

    async def test_kv_delete(self, consul_obj):
        c = consul_obj
        await c.kv.put("foo1", "1")
        await c.kv.put("foo2", "2")
        await c.kv.put("foo3", "3")
        _index, data = await c.kv.get("foo", recurse=True)
        assert [x["Key"] for x in data] == ["foo1", "foo2", "foo3"]

        response = await c.kv.delete("foo2")
        assert response is True
        _index, data = await c.kv.get("foo", recurse=True)
        assert [x["Key"] for x in data] == ["foo1", "foo3"]
        response = await c.kv.delete("foo", recurse=True)
        assert response is True
        _index, data = await c.kv.get("foo", recurse=True)
        assert data is None

    def test_kv_subscribe(self, consul_obj):
        c = consul_obj

        @gen.coroutine
        def get():
            index, data = yield c.kv.get("foo")
            assert data is None
            index, data = yield c.kv.get("foo", index=index)
            assert data["Value"] == b"bar"
            loop.stop()

        @gen.coroutine
        def put():
            response = yield c.kv.put("foo", "bar")
            assert response is True

        loop = ioloop.IOLoop.current()
        loop.add_timeout(time.time() + (1.0 / 100), put)
        loop.run_sync(get)

    async def test_kv_encoding(self, consul_obj):
        c = consul_obj

        # test binary
        response = await c.kv.put("foo", struct.pack("i", 1000))
        assert response is True
        _index, data = await c.kv.get("foo")
        assert struct.unpack("i", data["Value"]) == (1000,)

        # test unicode
        response = await c.kv.put("foo", "bar")
        assert response is True
        _index, data = await c.kv.get("foo")
        assert data["Value"] == b"bar"

        # test empty-string comes back as `None`
        response = await c.kv.put("foo", "")
        assert response is True
        _index, data = await c.kv.get("foo")
        assert data["Value"] is None

        # test None
        response = await c.kv.put("foo", None)
        assert response is True
        _index, data = await c.kv.get("foo")
        assert data["Value"] is None

        # check unencoded values raises assert
        with pytest.raises(AssertionError):
            await c.kv.put("foo", {1: 2})

    async def test_transaction(self, consul_obj):
        c = consul_obj
        value = base64.b64encode(b"1").decode("utf8")
        d = {"KV": {"Verb": "set", "Key": "asdf", "Value": value}}
        r = await c.txn.put([d])
        assert r["Errors"] is None

        d = {"KV": {"Verb": "get", "Key": "asdf"}}
        r = await c.txn.put([d])
        assert r["Results"][0]["KV"]["Value"] == value

    async def test_agent_services(self, consul_obj):
        c = consul_obj
        services = await c.agent.services()
        assert services == {}
        response = await c.agent.service.register("foo")
        assert response is True
        services = await c.agent.services()
        assert services == {
            "foo": {
                "Port": 0,
                "ID": "foo",
                "CreateIndex": 0,
                "ModifyIndex": 0,
                "EnableTagOverride": False,
                "Service": "foo",
                "Tags": [],
                "Meta": {},
                "Address": "",
            },
        }
        response = await c.agent.service.deregister("foo")
        assert response is True
        services = await c.agent.services()
        assert services == {}

    def test_catalog(self, consul_obj):
        c = consul_obj

        @gen.coroutine
        def nodes():
            index, nodes = yield c.catalog.nodes()
            assert len(nodes) == 1
            current = nodes[0]

            index, nodes = yield c.catalog.nodes(index=index)
            nodes.remove(current)
            assert [x["Node"] for x in nodes] == ["n1"]

            index, nodes = yield c.catalog.nodes(index=index)
            nodes.remove(current)
            assert [x["Node"] for x in nodes] == []
            loop.stop()

        @gen.coroutine
        def register():
            response = yield c.catalog.register("n1", "10.1.10.11")
            assert response is True
            yield gen.sleep(50 / 1000.0)
            response = yield c.catalog.deregister("n1")
            assert response is True

        loop = ioloop.IOLoop.current()
        loop.add_timeout(time.time() + (1.0 / 100), register)
        loop.run_sync(nodes)

    async def test_health_service(self, consul_obj):
        c = consul_obj
        # check there are no nodes for the service 'foo'
        _index, nodes = await c.health.service("foo")
        assert nodes == []

        # register two nodes, one with a long ttl, the other shorter
        await c.agent.service.register("foo", service_id="foo:1", check=Check.ttl("10s"))
        await c.agent.service.register("foo", service_id="foo:2", check=Check.ttl("100ms"))

        await gen.sleep(30 / 1000.0)

        # check the nodes show for the /health/service endpoint
        _index, nodes = await c.health.service("foo")
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # but that they aren't passing their health check
        _index, nodes = await c.health.service("foo", passing=True)
        assert nodes == []

        # ping the two node's health check
        await c.agent.check.ttl_pass("service:foo:1")
        await c.agent.check.ttl_pass("service:foo:2")

        await gen.sleep(50 / 1000.0)

        # both nodes are now available
        _index, nodes = await c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # wait until the short ttl node fails
        await gen.sleep(120 / 1000.0)

        # only one node available
        _index, nodes = await c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1"]

        # ping the failed node's health check
        await c.agent.check.ttl_pass("service:foo:2")

        await gen.sleep(30 / 1000.0)

        # check both nodes are available
        _index, nodes = await c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # deregister the nodes
        await c.agent.service.deregister("foo:1")
        await c.agent.service.deregister("foo:2")

        await gen.sleep(30 / 1000.0)

        _index, nodes = await c.health.service("foo")
        assert nodes == []

    def test_health_service_subscribe(self, consul_obj):
        c = consul_obj

        class Config:
            nodes = []

        config = Config()

        @gen.coroutine
        def monitor():
            yield c.agent.service.register("foo", service_id="foo:1", check=Check.ttl("40ms"))
            index = None
            while True:
                index, nodes = yield c.health.service("foo", index=index, passing=True)
                config.nodes = [node["Service"]["ID"] for node in nodes]

        @gen.coroutine
        def keepalive():
            # give the monitor a chance to register the service
            yield gen.sleep(50 / 1000.0)
            assert config.nodes == []

            # ping the service's health check
            yield c.agent.check.ttl_pass("service:foo:1")
            yield gen.sleep(30 / 1000.0)
            assert config.nodes == ["foo:1"]

            # the service should fail
            yield gen.sleep(60 / 1000.0)
            assert config.nodes == []

            yield c.agent.service.deregister("foo:1")
            loop.stop()

        loop = ioloop.IOLoop.current()
        loop.add_callback(monitor)
        loop.run_sync(keepalive)

    @pytest.mark.tornado
    async def test_session(self, consul_obj):
        c = consul_obj

        async def monitor():
            index, services = await c.session.list()
            assert services == []
            await gen.sleep(20 / 1000.0)

            index, services = await c.session.list(index=index)
            assert len(services)

            index, services = await c.session.list(index=index)
            assert services == []
            loop.stop()

        async def register():
            session_id = await c.session.create()
            await gen.sleep(50 / 1000.0)
            response = await c.session.destroy(session_id)
            assert response is True

        loop = ioloop.IOLoop.current()
        loop.add_timeout(time.time() + (1.0 / 100), register)
        await monitor()

    async def test_acl(self, consul_acl_obj):
        c = consul_acl_obj

        rules = """
            key "" {
                policy = "read"
            }
            key "private/" {
                policy = "deny"
            }
        """
        token = await c.acl.create(rules=rules)

        with pytest.raises(consul.ACLPermissionDenied):
            await c.acl.list(token=token)

        destroyed = await c.acl.destroy(token)
        assert destroyed is True

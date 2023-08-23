import asyncio
import base64
import struct

import pytest

import consul
import consul.aio

Check = consul.Check


@pytest.fixture()
def loop(request):
    asyncio.set_event_loop(None)
    loop = asyncio.new_event_loop()

    def fin():
        loop.close()

    request.addfinalizer(fin)
    return loop


class TestAsyncioConsul:
    def test_kv(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
            print(c)
            index, data = await c.kv.get("foo")

            print(index, data)
            assert data is None
            response = await c.kv.put("foo", "bar")
            assert response is True
            index, data = await c.kv.get("foo")
            assert data["Value"] == b"bar"
            await c.close()

        loop.run_until_complete(main())

    def test_consul_ctor(self, loop, consul_port):
        # same as previous but with global event loop
        async def main():
            c = consul.aio.Consul(port=consul_port)
            assert c._loop is loop  # pylint: disable=protected-access
            await c.kv.put("foo", struct.pack("i", 1000))
            _index, data = await c.kv.get("foo")
            assert struct.unpack("i", data["Value"]) == (1000,)
            await c.close()

        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())

    def test_kv_binary(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
            await c.kv.put("foo", struct.pack("i", 1000))
            _index, data = await c.kv.get("foo")
            assert struct.unpack("i", data["Value"]) == (1000,)
            await c.close()

        loop.run_until_complete(main())

    def test_kv_missing(self, loop, consul_port):
        c = consul.aio.Consul(port=consul_port, loop=loop)

        async def main():
            fut = asyncio.ensure_future(put(), loop=loop)
            await c.kv.put("index", "bump")
            index, data = await c.kv.get("foo")
            assert data is None
            index, data = await c.kv.get("foo", index=index)
            assert data["Value"] == b"bar"
            await fut
            await c.close()

        async def put():
            await asyncio.sleep(2.0 / 100)
            await c.kv.put("foo", "bar")

        loop.run_until_complete(main())

    def test_kv_put_flags(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
            await c.kv.put("foo", "bar")
            _index, data = await c.kv.get("foo")
            assert data["Flags"] == 0

            response = await c.kv.put("foo", "bar", flags=50)
            assert response is True
            _index, data = await c.kv.get("foo")
            assert data["Flags"] == 50
            await c.close()

        loop.run_until_complete(main())

    def test_kv_delete(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
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
            await c.close()

        loop.run_until_complete(main())

    def test_kv_subscribe(self, loop, consul_port):
        c = consul.aio.Consul(port=consul_port, loop=loop)

        async def get():
            fut = asyncio.ensure_future(put(), loop=loop)
            index, data = await c.kv.get("foo")
            assert data is None
            index, data = await c.kv.get("foo", index=index)
            assert data["Value"] == b"bar"
            await fut
            await c.close()

        async def put():
            await asyncio.sleep(1.0 / 100)
            response = await c.kv.put("foo", "bar")
            assert response is True

        loop.run_until_complete(get())

    def test_transaction(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
            value = base64.b64encode(b"1").decode("utf8")
            d = {"KV": {"Verb": "set", "Key": "asdf", "Value": value}}
            r = await c.txn.put([d])
            assert r["Errors"] is None

            d = {"KV": {"Verb": "get", "Key": "asdf"}}
            r = await c.txn.put([d])
            assert r["Results"][0]["KV"]["Value"] == value
            await c.close()

        loop.run_until_complete(main())

    def test_agent_services(self, loop, consul_port):
        async def main():
            c = consul.aio.Consul(port=consul_port, loop=loop)
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
            await c.close()

        loop.run_until_complete(main())

    def test_catalog(self, loop, consul_port):
        c = consul.aio.Consul(port=consul_port, loop=loop)

        async def nodes():
            fut = asyncio.ensure_future(register(), loop=loop)
            index, nodes = await c.catalog.nodes()
            assert len(nodes) == 1
            current = nodes[0]

            index, nodes = await c.catalog.nodes(index=index)
            nodes.remove(current)
            assert [x["Node"] for x in nodes] == ["n1"]

            index, nodes = await c.catalog.nodes(index=index)
            nodes.remove(current)
            assert [x["Node"] for x in nodes] == []
            await fut
            await c.close()

        async def register():
            await asyncio.sleep(1.0 / 100)
            response = await c.catalog.register("n1", "10.1.10.11")
            assert response is True
            await asyncio.sleep(50 / 1000.0)
            response = await c.catalog.deregister("n1")
            assert response is True

        loop.run_until_complete(nodes())

    def test_session(self, loop, consul_port):
        c = consul.aio.Consul(port=consul_port, loop=loop)

        async def monitor():
            fut = asyncio.ensure_future(register(), loop=loop)
            index, services = await c.session.list()
            assert services == []
            await asyncio.sleep(20 / 1000.0)

            index, services = await c.session.list(index=index)
            assert len(services)

            index, services = await c.session.list(index=index)
            assert services == []
            await fut
            await c.close()

        async def register():
            await asyncio.sleep(1.0 / 100)
            session_id = await c.session.create()
            await asyncio.sleep(50 / 1000.0)
            response = await c.session.destroy(session_id)
            assert response is True

        loop.run_until_complete(monitor())

    def test_acl(self, loop, acl_consul):
        async def main():
            c = consul.aio.Consul(port=acl_consul.port, token=acl_consul.token, loop=loop)

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
            await c.close()

        loop.run_until_complete(main())

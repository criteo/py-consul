class TestCatalog:
    pass
    # def test_catalog(self, consul_obj):
    #     c, _consul_version = consul_obj
    #
    #     # grab the node our server created, so we can ignore it
    #     _, nodes = c.catalog.nodes()
    #     assert len(nodes) == 1
    #     current = nodes[0]
    #
    #     # test catalog.datacenters
    #     assert c.catalog.datacenters() == ["dc1"]
    #
    #     # test catalog.register
    #     pytest.raises(consul.ConsulException, c.catalog.register, "foo", "10.1.10.11", dc="dc2")
    #
    #     assert c.catalog.register("n1", "10.1.10.11", service={"service": "s1"}, check={"name": "c1"}) is True
    #     assert c.catalog.register("n1", "10.1.10.11", service={"service": "s2"}) is True
    #     assert c.catalog.register("n2", "10.1.10.12", service={"service": "s1", "tags": ["master"]}) is True
    #
    #     # test catalog.nodes
    #     pytest.raises(consul.ConsulException, c.catalog.nodes, dc="dc2")
    #     _, nodes = c.catalog.nodes()
    #     nodes.remove(current)
    #     assert [x["Node"] for x in nodes] == ["n1", "n2"]
    #
    #     # test catalog.services
    #     pytest.raises(consul.ConsulException, c.catalog.services, dc="dc2")
    #     _, services = c.catalog.services()
    #     assert services == {"s1": ["master"], "s2": [], "consul": []}
    #
    #     # test catalog.node
    #     pytest.raises(consul.ConsulException, c.catalog.node, "n1", dc="dc2")
    #     _, node = c.catalog.node("n1")
    #     assert set(node["Services"].keys()) == {"s1", "s2"}
    #     _, node = c.catalog.node("n3")
    #     assert node is None
    #
    #     # test catalog.service
    #     pytest.raises(consul.ConsulException, c.catalog.service, "s1", dc="dc2")
    #     _, nodes = c.catalog.service("s1")
    #     assert {x["Node"] for x in nodes} == {"n1", "n2"}
    #     _, nodes = c.catalog.service("s1", tag="master")
    #     assert {x["Node"] for x in nodes} == {"n2"}
    #
    #     # test catalog.deregister
    #     pytest.raises(consul.ConsulException, c.catalog.deregister, "n2", dc="dc2")
    #     assert c.catalog.deregister("n1", check_id="c1") is True
    #     assert c.catalog.deregister("n2", service_id="s1") is True
    #     # check the nodes weren't removed
    #     _, nodes = c.catalog.nodes()
    #     nodes.remove(current)
    #     assert [x["Node"] for x in nodes] == ["n1", "n2"]
    #     # check n2's s1 service was removed though
    #     _, nodes = c.catalog.service("s1")
    #     assert {x["Node"] for x in nodes} == {"n1"}
    #
    #     # cleanup
    #     assert c.catalog.deregister("n1") is True
    #     assert c.catalog.deregister("n2") is True
    #     _, nodes = c.catalog.nodes()
    #     nodes.remove(current)
    #     assert [x["Node"] for x in nodes] == []

import time

import pytest

import consul


class TestCatalog:
    def test_catalog(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # grab the node our server created, so we can ignore it
        _, nodes = c.catalog.nodes()
        assert len(nodes) == 1
        current = nodes[0]

        # test catalog.datacenters
        assert c.catalog.datacenters() == ["dc1"]

        # test catalog.register
        pytest.raises(consul.ConsulException, c.catalog.register, "foo", "10.1.10.11", dc="dc2")

        assert c.catalog.register("n1", "10.1.10.11", service={"service": "s1"}, check={"name": "c1"}) is True
        assert c.catalog.register("n1", "10.1.10.11", service={"service": "s2"}) is True
        assert c.catalog.register("n2", "10.1.10.12", service={"service": "s1", "tags": ["master"]}) is True

        # test catalog.nodes
        pytest.raises(consul.ConsulException, c.catalog.nodes, dc="dc2")
        _, nodes = c.catalog.nodes()
        nodes.remove(current)
        assert [x["Node"] for x in nodes] == ["n1", "n2"]

        # test catalog.services
        pytest.raises(consul.ConsulException, c.catalog.services, dc="dc2")
        _, services = c.catalog.services()
        assert services == {"s1": ["master"], "s2": [], "consul": []}

        # test catalog.node
        pytest.raises(consul.ConsulException, c.catalog.node, "n1", dc="dc2")
        _, node = c.catalog.node("n1")
        assert set(node["Services"].keys()) == {"s1", "s2"}
        _, node = c.catalog.node("n3")
        assert node is None

        # test catalog.service
        pytest.raises(consul.ConsulException, c.catalog.service, "s1", dc="dc2")
        _, nodes = c.catalog.service("s1")
        assert {x["Node"] for x in nodes} == {"n1", "n2"}
        _, nodes = c.catalog.service("s1", tag="master")
        assert {x["Node"] for x in nodes} == {"n2"}

        # test catalog.deregister
        pytest.raises(consul.ConsulException, c.catalog.deregister, "n2", dc="dc2")
        assert c.catalog.deregister("n1", check_id="c1") is True
        assert c.catalog.deregister("n2", service_id="s1") is True
        # check the nodes weren't removed
        _, nodes = c.catalog.nodes()
        nodes.remove(current)
        assert [x["Node"] for x in nodes] == ["n1", "n2"]
        # check n2's s1 service was removed though
        _, nodes = c.catalog.service("s1")
        assert {x["Node"] for x in nodes} == {"n1"}

        # cleanup
        assert c.catalog.deregister("n1") is True
        assert c.catalog.deregister("n2") is True
        _, nodes = c.catalog.nodes()
        nodes.remove(current)
        assert [x["Node"] for x in nodes] == []

    def test_catalog_register_skip_node_update_and_tagged_addresses(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        tagged_addresses = {"lan": "10.1.10.11", "wan": "10.1.10.21"}
        assert (
            c.catalog.register(
                "n-tagged",
                "10.1.10.11",
                service={"service": "s-tagged"},
                tagged_addresses=tagged_addresses,
            )
            is True
        )

        _, node = c.catalog.node("n-tagged")
        assert node["Node"]["TaggedAddresses"]["lan"] == "10.1.10.11"
        assert node["Node"]["TaggedAddresses"]["wan"] == "10.1.10.21"

        # SkipNodeUpdate=True should not error and the node's address stays
        # untouched (registering with the same address so this is a no-op
        # check, but exercises the wire format of the flag).
        assert (
            c.catalog.register(
                "n-tagged",
                "10.1.10.11",
                service={"service": "s-tagged"},
                skip_node_update=True,
            )
            is True
        )

        _, node = c.catalog.node("n-tagged")
        assert node["Node"]["Address"] == "10.1.10.11"

        assert c.catalog.deregister("n-tagged") is True

    def test_catalog_filter(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert c.catalog.register("n-filter-1", "10.1.10.31", service={"service": "web", "tags": ["prod"]}) is True
        assert c.catalog.register("n-filter-2", "10.1.10.32", service={"service": "web", "tags": ["staging"]}) is True

        # catalog.nodes filter
        _, nodes = c.catalog.nodes(filter_expr='Node == "n-filter-1"')
        assert [x["Node"] for x in nodes] == ["n-filter-1"]

        # catalog.services filter
        _, services = c.catalog.services(filter_expr='"prod" in ServiceTags')
        assert services == {"web": ["prod"]}

        # catalog.node filter -- the filter expression is evaluated against
        # each entry of the "Services" map, not the top-level document.
        _, node = c.catalog.node("n-filter-1", filter_expr='Service == "web"')
        assert node is not None
        assert "web" in node["Services"]
        _, node = c.catalog.node("n-filter-1", filter_expr='Service == "does-not-exist"')
        assert node["Services"] == {}

        # catalog.service filter
        _, nodes = c.catalog.service("web", filter_expr='"prod" in ServiceTags')
        assert {x["Node"] for x in nodes} == {"n-filter-1"}

        # catalog.connect filter (connect-capable nodes for a plain service
        # is empty, but the filter param must still be accepted and produce
        # a well-formed, successful request)
        _, nodes = c.catalog.connect("web", filter_expr='"prod" in ServiceTags')
        assert nodes == []

        # malformed bexpr should raise a clear ConsulException from Consul
        pytest.raises(consul.ConsulException, c.catalog.nodes, filter_expr="not a valid expression((")

        assert c.catalog.deregister("n-filter-1") is True
        assert c.catalog.deregister("n-filter-2") is True

    def test_catalog_service_merge_central_config(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert c.catalog.register("n-mcc", "10.1.10.41", service={"service": "web-mcc", "port": 8080}) is True

        _, nodes = c.catalog.service("web-mcc", merge_central_config=True)
        assert {x["Node"] for x in nodes} == {"n-mcc"}
        assert nodes[0]["ServicePort"] == 8080

        _, nodes = c.catalog.connect("web-mcc", merge_central_config=True)
        assert nodes == []

        assert c.catalog.deregister("n-mcc") is True

    def test_catalog_service_peer_unknown(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # querying with a peer name that doesn't exist returns no results
        # rather than erroring, this simply verifies the query param is
        # wired through correctly end-to-end.
        _, nodes = c.catalog.service("web", peer="unknown-peer")
        assert nodes == []

        _, nodes = c.catalog.connect("web", peer="unknown-peer")
        assert nodes == []

    def test_catalog_gateway_services(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # no gateway registered yet: empty list of services
        services = c.catalog.gateway_services("ingress-gateway-1")
        assert services == []

        assert (
            c.catalog.register(
                "n-gw",
                "10.1.10.51",
                service={"service": "ingress-gateway-1", "kind": "ingress-gateway"},
            )
            is True
        )
        assert c.catalog.register("n-gw", "10.1.10.51", service={"service": "web-gw", "port": 8080}) is True

        c.config.set(
            "ingress-gateway",
            "ingress-gateway-1",
            {
                "Listeners": [
                    {
                        "Port": 8080,
                        "Protocol": "tcp",
                        "Services": [{"Name": "web-gw"}],
                    }
                ]
            },
        )

        time.sleep(0.5)

        services = c.catalog.gateway_services("ingress-gateway-1")
        assert [entry["Service"]["Name"] for entry in services] == ["web-gw"]
        assert services[0]["GatewayKind"] == "ingress-gateway"

        assert c.catalog.deregister("n-gw", service_id="ingress-gateway-1") is True
        assert c.catalog.deregister("n-gw", service_id="web-gw") is True

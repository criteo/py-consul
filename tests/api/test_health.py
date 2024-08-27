import time

import consul.check

Check = consul.check.Check


class TestHealth:
    def test_health_service(self, consul_obj):
        c, _consul_version = consul_obj

        # check there are no nodes for the service 'foo'
        _index, nodes = c.health.service("foo")
        assert nodes == []

        # register two nodes, one with a long ttl, the other shorter
        c.agent.service.register("foo", service_id="foo:1", check=Check.ttl("10s"), tags=["tag:foo:1"])
        c.agent.service.register("foo", service_id="foo:2", check=Check.ttl("1s"))

        time.sleep(0.2)

        # check the nodes show for the /health/service endpoint
        _index, nodes = c.health.service("foo")
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # but that they aren't passing their health check
        _index, nodes = c.health.service("foo", passing=True)
        assert nodes == []

        # ping the two node's health check
        c.agent.check.ttl_pass("service:foo:1")
        c.agent.check.ttl_pass("service:foo:2")

        time.sleep(0.2)

        # both nodes are now available
        _index, nodes = c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # wait until the short ttl node fails
        time.sleep(3)

        # only one node available
        _index, nodes = c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1"]

        # ping the failed node's health check
        c.agent.check.ttl_pass("service:foo:2")

        time.sleep(0.2)

        # check both nodes are available
        _index, nodes = c.health.service("foo", passing=True)
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1", "foo:2"]

        # check that tag works
        _index, nodes = c.health.service("foo", tag="tag:foo:1")
        assert [node["Service"]["ID"] for node in nodes] == ["foo:1"]

        # deregister the nodes
        c.agent.service.deregister("foo:1")
        c.agent.service.deregister("foo:2")

        time.sleep(0.2)

        _index, nodes = c.health.service("foo")
        assert nodes == []

    def test_health_state(self, consul_obj):
        c, _consul_version = consul_obj

        # The empty string is for the Serf Health Status check, which has an
        # empty ServiceID
        _index, nodes = c.health.state("any")
        assert [node["ServiceID"] for node in nodes] == [""]

        # register two nodes, one with a long ttl, the other shorter
        c.agent.service.register("foo", service_id="foo:1", check=Check.ttl("10s"))
        c.agent.service.register("foo", service_id="foo:2", check=Check.ttl("1s"))

        time.sleep(0.2)

        # check the nodes show for the /health/state/any endpoint
        _index, nodes = c.health.state("any")
        assert {node["ServiceID"] for node in nodes} == {"", "foo:1", "foo:2"}

        # but that they aren't passing their health check
        _index, nodes = c.health.state("passing")
        assert [node["ServiceID"] for node in nodes] != "foo"

        # ping the two node's health check
        c.agent.check.ttl_pass("service:foo:1")
        c.agent.check.ttl_pass("service:foo:2")

        time.sleep(0.2)

        # both nodes are now available
        _index, nodes = c.health.state("passing")
        assert {node["ServiceID"] for node in nodes} == {"", "foo:1", "foo:2"}

        # wait until the short ttl node fails
        time.sleep(3)

        # only one node available
        _index, nodes = c.health.state("passing")
        assert {node["ServiceID"] for node in nodes} == {"", "foo:1"}

        # ping the failed node's health check
        c.agent.check.ttl_pass("service:foo:2")

        time.sleep(0.2)

        # check both nodes are available
        _index, nodes = c.health.state("passing")
        assert {node["ServiceID"] for node in nodes} == {"", "foo:1", "foo:2"}

        # deregister the nodes
        c.agent.service.deregister("foo:1")
        c.agent.service.deregister("foo:2")

        time.sleep(0.2)

        _index, nodes = c.health.state("any")
        assert [node["ServiceID"] for node in nodes] == [""]

    def test_health_node(self, consul_obj):
        c, _consul_version = consul_obj
        # grab local node name
        node = c.agent.self()["Config"]["NodeName"]
        _index, checks = c.health.node(node)
        assert node in [check["Node"] for check in checks]

    def test_health_checks(self, consul_obj):
        c, _consul_version = consul_obj

        c.agent.service.register("foobar", service_id="foobar", check=Check.ttl("10s"))

        time.sleep(40 / 1000.00)

        _index, checks = c.health.checks("foobar")

        assert [check["ServiceID"] for check in checks] == ["foobar"]
        assert [check["CheckID"] for check in checks] == ["service:foobar"]

        c.agent.service.deregister("foobar")

        time.sleep(40 / 1000.0)

        _index, checks = c.health.checks("foobar")
        assert len(checks) == 0

import time

import pytest

import consul.check
from tests.utils import should_skip

Check = consul.check.Check


class TestAgent:
    def test_agent_checks(self, consul_port) -> None:
        consul_port, _consul_version = consul_port
        c = consul.Consul(port=consul_port)

        def verify_and_dereg_check(check_id) -> None:
            assert set(c.agent.checks().keys()) == {check_id}
            assert c.agent.check.deregister(check_id) is True
            assert set(c.agent.checks().keys()) == set()

        def verify_check_status(check_id, status, notes=None) -> None:
            checks = c.agent.checks()
            assert checks[check_id]["Status"] == status
            if notes:
                assert checks[check_id]["Output"] == notes

        # test setting notes on a check
        c.agent.check.register("check", Check.ttl("1s"), notes="foo")
        assert c.agent.checks()["check"]["Notes"] == "foo"
        c.agent.check.deregister("check")

        assert set(c.agent.checks().keys()) == set()
        assert c.agent.check.register("script_check", Check.script("/bin/true", 10)) is True
        verify_and_dereg_check("script_check")

        assert c.agent.check.register("check name", Check.script("/bin/true", 10, "10m"), check_id="check_id") is True
        verify_and_dereg_check("check_id")

        # 1s is the minimal interval for HTTP checks
        http_addr = "http://localhost:8500"
        assert c.agent.check.register("http_check", Check.http(http_addr, "1s")) is True
        time.sleep(1.5)
        verify_check_status("http_check", "passing")
        verify_and_dereg_check("http_check")

        assert c.agent.check.register("http_timeout_check", Check.http(http_addr, "100ms", timeout="2s")) is True
        verify_and_dereg_check("http_timeout_check")

        assert c.agent.check.register("ttl_check", Check.ttl("100ms")) is True

        assert c.agent.check.ttl_warn("ttl_check") is True
        verify_check_status("ttl_check", "warning")
        assert c.agent.check.ttl_warn("ttl_check", notes="its not quite right") is True
        verify_check_status("ttl_check", "warning", "its not quite right")

        assert c.agent.check.ttl_fail("ttl_check") is True
        verify_check_status("ttl_check", "critical")
        assert c.agent.check.ttl_fail("ttl_check", notes="something went boink!") is True
        verify_check_status("ttl_check", "critical", notes="something went boink!")

        assert c.agent.check.ttl_pass("ttl_check") is True
        verify_check_status("ttl_check", "passing")
        assert c.agent.check.ttl_pass("ttl_check", notes="all hunky dory!") is True
        verify_check_status("ttl_check", "passing", notes="all hunky dory!")
        # wait for ttl to expire
        time.sleep(120 / 1000.0)
        verify_check_status("ttl_check", "critical")
        verify_and_dereg_check("ttl_check")

    def test_service_multi_check(self, consul_port) -> None:
        consul_port, _consul_version = consul_port
        c = consul.Consul(port=consul_port)
        http_addr = "http://127.0.0.1:8500"
        c.agent.service.register(
            "foo1",
            check=Check.http(http_addr, "1s"),
            extra_checks=[
                Check.http(http_addr, "2s"),
                Check.http(http_addr, "3s"),
            ],
        )

        time.sleep(200 / 1000.0)

        _index, nodes = c.health.service("foo1")
        assert {check["ServiceID"] for node in nodes for check in node["Checks"]} == {"foo1", ""}

        assert {check["CheckID"] for node in nodes for check in node["Checks"]} == {
            "service:foo1:1",
            "service:foo1:2",
            "service:foo1:3",
            "serfHealth",
        }
        time.sleep(3.5)

        _index, checks = c.health.checks(service="foo1")
        assert [check["CheckID"] for check in checks] == ["service:foo1:1", "service:foo1:2", "service:foo1:3"]
        assert [check["Status"] for check in checks] == ["passing", "passing", "passing"]

    def test_service_dereg_issue_156(self, consul_port) -> None:
        consul_port, _consul_version = consul_port
        # https://github.com/cablehead/python-consul/issues/156
        service_name = "app#127.0.0.1#3000"
        c = consul.Consul(port=consul_port)
        c.agent.service.register(service_name)

        time.sleep(80 / 1000.0)

        _index, nodes = c.health.service(service_name)
        assert [node["Service"]["ID"] for node in nodes] == [service_name]

        # Clean up tasks
        assert c.agent.service.deregister(service_name) is True

        time.sleep(40 / 1000.0)

        _index, nodes = c.health.service(service_name)
        assert [node["Service"]["ID"] for node in nodes] == []

    def test_agent_checks_service_id(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        c.agent.service.register("foo1")

        time.sleep(40 / 1000.0)

        _index, nodes = c.health.service("foo1")
        assert [node["Service"]["ID"] for node in nodes] == ["foo1"]

        c.agent.check.register("foo", Check.ttl("100ms"), service_id="foo1")
        c.agent.check.register("foo2", Check.ttl("100ms"), service_id="foo1")

        time.sleep(40 / 1000.0)

        _index, nodes = c.health.service("foo1")
        assert {check["ServiceID"] for node in nodes for check in node["Checks"]} == {"foo1", ""}
        assert {check["CheckID"] for node in nodes for check in node["Checks"]} == {"foo", "foo2", "serfHealth"}

        # Clean up tasks
        assert c.agent.check.deregister("foo") is True
        assert c.agent.check.deregister("foo2") is True

        time.sleep(40 / 1000.0)

        assert c.agent.service.deregister("foo1") is True

        time.sleep(40 / 1000.0)

    def test_agent_register_check_no_service_id(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        _index, nodes = c.health.service("foo1")
        assert nodes == []

        if should_skip(_consul_version, ">", "1.11.0"):
            with pytest.raises(consul.std.base.ConsulException):
                c.agent.check.register("foo", Check.ttl("100ms"), service_id="foo1")
        else:
            assert not c.agent.check.register("foo", Check.ttl("100ms"), service_id="foo1")

        time.sleep(40 / 1000.0)

        assert c.agent.checks() == {}

        # Cleanup tasks
        c.agent.check.deregister("foo")

        time.sleep(40 / 1000.0)

    def test_agent_register_enable_tag_override(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        _index, nodes = c.health.service("foo1")
        assert nodes == []

        c.agent.service.register("foo", enable_tag_override=True)

        assert c.agent.services()["foo"]["EnableTagOverride"]
        # Cleanup tasks
        c.agent.check.deregister("foo")

    def test_agent_service_maintenance(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        c.agent.service.register("foo", check=Check.ttl("100ms"))

        time.sleep(40 / 1000.0)

        c.agent.service.maintenance("foo", "true", "test")

        time.sleep(40 / 1000.0)

        checks_pre = c.agent.checks()
        assert "_service_maintenance:foo" in checks_pre
        assert checks_pre["_service_maintenance:foo"]["Notes"] == "test"

        c.agent.service.maintenance("foo", "false")

        time.sleep(40 / 1000.0)

        checks_post = c.agent.checks()
        assert "_service_maintenance:foo" not in checks_post

        # Cleanup
        c.agent.service.deregister("foo")

        time.sleep(40 / 1000.0)

    def test_agent_node_maintenance(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        c.agent.maintenance("true", "test")

        time.sleep(40 / 1000.0)

        checks_pre = c.agent.checks()
        assert "_node_maintenance" in checks_pre
        assert checks_pre["_node_maintenance"]["Notes"] == "test"

        c.agent.maintenance("false")

        time.sleep(40 / 1000.0)

        checks_post = c.agent.checks()
        assert "_node_maintenance" not in checks_post

    def test_agent_members(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        members = c.agent.members()
        for x in members:
            assert x["Status"] == 1
            assert x["Name"] is not None
            assert x["Tags"] is not None
        assert c.agent.self()["Member"] in members

        wan_members = c.agent.members(wan=True)
        for x in wan_members:
            assert "dc1" in x["Name"]

    def test_agent_self(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert set(c.agent.self().keys()) == {"Member", "xDS", "Stats", "Config", "Coord", "DebugConfig", "Meta"}

    def test_agent_services(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        assert c.agent.service.register("foo") is True
        assert set(c.agent.services().keys()) == {"foo"}
        assert c.agent.service.deregister("foo") is True
        assert set(c.agent.services().keys()) == set()

        # test address param
        assert c.agent.service.register("foo", address="10.10.10.1") is True
        assert [v["Address"] for k, v in c.agent.services().items() if k == "foo"][0] == "10.10.10.1"
        assert c.agent.service.deregister("foo") is True

    def test_agent_service_tagged_addresses(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        tagged_addresses = {
            "lan": {"address": "10.10.10.1", "port": 8080},
            "wan": {"address": "192.168.1.1", "port": 80},
        }
        expected_tagged_addresses = {
            "lan": {"Address": "10.10.10.1", "Port": 8080},
            "wan": {"Address": "192.168.1.1", "Port": 80},
        }

        assert c.agent.service.register("foo_tagged", tagged_addresses=tagged_addresses) is True

        services = c.agent.services()
        assert "foo_tagged" in services
        assert services["foo_tagged"]["TaggedAddresses"] == expected_tagged_addresses

        assert c.agent.service.deregister("foo_tagged") is True

    def test_agent_service_connect(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        connect: dict[str, dict] = {"sidecar_service": {}}

        assert c.agent.service.register("foo_connect", connect=connect) is True

        services = c.agent.services()
        assert "foo_connect" in services

        # When using sidecar_service, Consul registers a separate service.
        assert "foo_connect-sidecar-proxy" in services

        assert c.agent.service.deregister("foo_connect") is True

class TestDiscoveryChain:
    def test_discovery_chain_get(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        c.agent.service.register("web")

        try:
            chain = c.discovery_chain.get("web")
            assert chain["Chain"]["ServiceName"] == "web"

            overridden = c.discovery_chain.get("web", override_protocol="http")
            assert overridden["Chain"]["ServiceName"] == "web"
        finally:
            c.agent.service.deregister("web")

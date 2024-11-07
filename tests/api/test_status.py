class TestStatus:
    def test_status_leader(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        agent_self = c.agent.self()
        leader = c.status.leader()
        addr_port = agent_self["Stats"]["consul"]["leader_addr"]

        assert leader == addr_port, f"Leader value was {leader}, expected value was {addr_port}"

    def test_status_peers(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        agent_self = c.agent.self()

        addr_port = agent_self["Stats"]["consul"]["leader_addr"]
        peers = c.status.peers()

        assert addr_port in peers, f"Expected value '{addr_port}' in peer list but it was not present"

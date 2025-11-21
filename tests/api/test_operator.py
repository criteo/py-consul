class TestOperator:
    def test_operator(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        config = c.operator.raft_config()

        assert config["Index"] == 0
        leader = False
        voter = False
        for server in config["Servers"]:
            if server["Leader"]:
                leader = True
            if server["Voter"]:
                voter = True
        assert leader
        assert voter

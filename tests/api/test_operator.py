from packaging import version


class TestOperator:
    def test_operator(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        config = c.operator.raft_config()

        expected_index = 1
        if version.parse(_consul_version) >= version.parse("1.13.8"):
            expected_index = 0

        assert config["Index"] == expected_index
        leader = False
        voter = False
        for server in config["Servers"]:
            if server["Leader"]:
                leader = True
            if server["Voter"]:
                voter = True
        assert leader
        assert voter

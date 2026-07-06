import time

import pytest

import consul


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

    def test_raft_remove_peer_not_found(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # Removing a peer that isn't part of the Raft configuration is a
        # server-side error (Consul returns a 500), not a boolean failure --
        # verified against a live single-node dev cluster. We deliberately
        # avoid removing the sole real peer here, since that would break the
        # single-node cluster the rest of the tests run against.
        with pytest.raises(consul.ConsulException):
            c.operator.raft_remove_peer(address="10.255.255.1:8300")

        with pytest.raises(consul.ConsulException):
            c.operator.raft_remove_peer(peer_id="00000000-0000-0000-0000-000000000099")

    def test_raft_transfer_leader_no_other_peers(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # On a single-node dev cluster there is no other peer to transfer
        # leadership to, so Consul errors out instead of transferring.
        with pytest.raises(consul.ConsulException):
            c.operator.raft_transfer_leader()

        with pytest.raises(consul.ConsulException):
            c.operator.raft_transfer_leader(peer_id="00000000-0000-0000-0000-000000000099")

    def test_autopilot_configuration(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        config = c.operator.autopilot_configuration()
        assert config["CleanupDeadServers"] is True
        assert "ModifyIndex" in config

        # A cas that doesn't match the current ModifyIndex is a no-op that
        # returns False rather than raising or applying the change.
        assert (
            c.operator.update_autopilot_configuration(cleanup_dead_servers=False, cas=config["ModifyIndex"] + 1000)
            is False
        )
        assert c.operator.autopilot_configuration()["CleanupDeadServers"] is True

        # Without cas (or with the correct cas) the update is unconditional.
        assert c.operator.update_autopilot_configuration(cleanup_dead_servers=False) is True
        updated = c.operator.autopilot_configuration()
        assert updated["CleanupDeadServers"] is False

        assert c.operator.update_autopilot_configuration(cleanup_dead_servers=True, cas=updated["ModifyIndex"]) is True
        assert c.operator.autopilot_configuration()["CleanupDeadServers"] is True

    def test_autopilot_health(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # A healthy single-node dev cluster returns HTTP 200 with Healthy=True;
        # this must not raise even though the callback also has to handle the
        # HTTP 429 "unhealthy" case without raising. Immediately after
        # startup Consul can briefly report itself as unhealthy (HTTP 429)
        # while the raft leader election settles -- verified live -- so
        # retry a few times rather than asserting on the very first call.
        health = c.operator.autopilot_health()
        for _ in range(20):
            if health["Healthy"]:
                break
            time.sleep(0.5)
            health = c.operator.autopilot_health()

        assert health["Healthy"] is True
        assert len(health["Servers"]) == 1
        assert health["Servers"][0]["Leader"] is True
        assert health["Servers"][0]["Healthy"] is True

    def test_keyring_without_encryption_errors(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # The test fixtures start Consul without gossip encryption enabled,
        # so the keyring is empty and every keyring operation is a real,
        # observed server-side error (HTTP 500) rather than a boolean result.
        with pytest.raises(consul.ConsulException):
            c.operator.keyring_list()

        with pytest.raises(consul.ConsulException):
            c.operator.keyring_install(key="8CooQRX1+VK7MsQQK6lx2LhumpSfQzUjE63HdAu2hgA=")

        with pytest.raises(consul.ConsulException):
            c.operator.keyring_use(key="8CooQRX1+VK7MsQQK6lx2LhumpSfQzUjE63HdAu2hgA=")

        with pytest.raises(consul.ConsulException):
            c.operator.keyring_remove(key="8CooQRX1+VK7MsQQK6lx2LhumpSfQzUjE63HdAu2hgA=")

    def test_usage(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        usage = c.operator.usage()
        assert "dc1" in usage["Usage"]
        assert usage["Usage"]["dc1"]["Nodes"] >= 1
        assert usage["KnownLeader"] is True

        global_usage = c.operator.usage(global_=True, stale=True)
        assert "dc1" in global_usage["Usage"]

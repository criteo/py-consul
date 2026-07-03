import pytest

import consul


class TestSnapshot:
    def test_snapshot_save_and_restore(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        c.kv.put("snapshot-test-key", "before-snapshot", token=master_token)

        snapshot = c.snapshot.save(token=master_token)
        assert isinstance(snapshot, bytes)
        assert snapshot[:2] == b"\x1f\x8b"  # gzip magic number

        c.kv.put("snapshot-test-key", "after-snapshot", token=master_token)

        assert c.snapshot.restore(snapshot, token=master_token) is True

        _index, value = c.kv.get("snapshot-test-key", token=master_token)
        assert value["Value"] == b"before-snapshot"

    def test_snapshot_requires_management_token(self, acl_consul) -> None:
        c, _master_token, _consul_version = acl_consul

        pytest.raises(consul.ACLPermissionDenied, c.snapshot.save, token="anonymous")

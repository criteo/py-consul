import pytest

import consul
from tests.utils import find_recursive


class TestConsulAcl:
    def test_acl_permission_denied(self, acl_consul):
        c, _master_token, _consul_version = acl_consul

        # No token
        pytest.raises(consul.ACLPermissionDenied, c.acl.list)
        pytest.raises(consul.ACLPermissionDenied, c.acl.create)
        pytest.raises(consul.ACLPermissionDenied, c.acl.update, accessor_id="00000000-0000-0000-0000-000000000002")
        pytest.raises(consul.ACLPermissionDenied, c.acl.clone, accessor_id="00000000-0000-0000-0000-000000000002")
        pytest.raises(consul.ACLPermissionDenied, c.acl.read, accessor_id="00000000-0000-0000-0000-000000000002")
        pytest.raises(consul.ACLPermissionDenied, c.acl.delete, accessor_id="00000000-0000-0000-0000-000000000002")

        # Token without the right permission (acl:write or acl:read)
        pytest.raises(consul.ACLPermissionDenied, c.acl.list, token="anonymous")
        pytest.raises(consul.ACLPermissionDenied, c.acl.create, token="anonymous")
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.update,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.clone,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.read,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.delete,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )

    def test_acl_list(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        # Make sure both master and anonymous tokens are created
        acls = c.acl.list(token=master_token)

        master_token_repr = {
            "Description": "Initial Management Token",
            "Policies": [{"ID": "00000000-0000-0000-0000-000000000001", "Name": "global-management"}],
            "SecretID": master_token,
        }
        anonymous_token_repr = {
            "AccessorID": "00000000-0000-0000-0000-000000000002",
            "SecretID": "anonymous",
        }
        assert find_recursive(acls, master_token_repr)
        assert find_recursive(acls, anonymous_token_repr)

    def test_acl_read(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.read, accessor_id="unknown", token=master_token)

        anonymous_token_repr = {
            "AccessorID": "00000000-0000-0000-0000-000000000002",
            "SecretID": "anonymous",
        }
        acl = c.acl.read(accessor_id="00000000-0000-0000-0000-000000000002", token=master_token)
        assert find_recursive(acl, anonymous_token_repr)

    def test_acl_create(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        c.acl.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        c.acl.create(secret_id="DEADBEEF-0000-0000-0000-000000000000", token=master_token)
        c.acl.create(
            secret_id="00000000-A5A5-0000-0000-000000000000",
            accessor_id="00000000-0000-A5A5-0000-000000000000",
            description="some token!",
            token=master_token,
        )

        assert c.acl.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert c.acl.read(accessor_id="00000000-0000-A5A5-0000-000000000000", token=master_token)

        expected = [
            {
                "AccessorID": "00000000-DEAD-BEEF-0000-000000000000",
                "Description": "",
            },
            {
                "SecretID": "DEADBEEF-0000-0000-0000-000000000000",
                "Description": "",
            },
            {
                "AccessorID": "00000000-0000-A5A5-0000-000000000000",
                "SecretID": "00000000-A5A5-0000-0000-000000000000",
                "Description": "some token!",
            },
        ]
        acl = c.acl.list(token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_clone(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        assert len(c.acl.list(token=master_token)) == 2

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.clone, accessor_id="unknown", token=master_token)

        c.acl.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        c.acl.clone(accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="cloned", token=master_token)
        assert len(c.acl.list(token=master_token)) == 4

        expected = [
            {
                "AccessorID": "00000000-DEAD-BEEF-0000-000000000000",
            },
            {
                "Description": "cloned",
            },
        ]
        acl = c.acl.list(token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_update(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.update, accessor_id="unknown", token=master_token)

        assert len(c.acl.list(token=master_token)) == 2
        c.acl.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="original", token=master_token)
        assert len(c.acl.list(token=master_token)) == 3
        c.acl.update(accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="updated", token=master_token)
        assert len(c.acl.list(token=master_token)) == 3

        expected = {
            "AccessorID": "00000000-DEAD-BEEF-0000-000000000000",
            "Description": "updated",
        }
        acl = c.acl.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_delete(self, acl_consul):
        c, master_token, _consul_version = acl_consul

        assert len(c.acl.list(token=master_token)) == 2
        c.acl.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert len(c.acl.list(token=master_token)) == 3
        assert c.acl.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)

        # Delete and ensure it doesn't exist anymore
        c.acl.delete(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert len(c.acl.list(token=master_token)) == 2
        pytest.raises(
            consul.ConsulException, c.acl.read, accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token
        )

    #
    # def test_acl_implicit_token_use(self, acl_consul):
    #     # configure client to use the master token by default
    #     port, _token, _consul_version = acl_consul
    #     c = consul.Consul(port=port)
    #     master_token = acl_consul.token
    #
    #     if should_skip(_consul_version, "<", "1.11.0"):
    #         clean_consul(port)
    #         pytest.skip("Endpoint /v1/acl/list for the legacy ACL system was removed in Consul 1.11.")
    #
    #
    #     acls = c.acl.list()
    #     assert {x["ID"] for x in acls} == {"anonymous", master_token}
    #
    #     assert c.acl.info("foo") is None
    #     compare = [c.acl.info(master_token), c.acl.info("anonymous")]
    #     compare.sort(key=operator.itemgetter("ID"))
    #     assert acls == compare
    #
    #     rules = """
    #         key "" {
    #             policy = "read"
    #         }
    #         key "private/" {
    #             policy = "deny"
    #         }
    #     """
    #     token = c.acl.create(rules=rules)
    #     assert c.acl.info(token)["Rules"] == rules
    #
    #     token2 = c.acl.clone(token)
    #     assert c.acl.info(token2)["Rules"] == rules
    #
    #     assert c.acl.update(token2, name="Foo") == token2
    #     assert c.acl.info(token2)["Name"] == "Foo"
    #
    #     assert c.acl.destroy(token2) is True
    #     assert c.acl.info(token2) is None
    #
    #     c.kv.put("foo", "bar")
    #     c.kv.put("private/foo", "bar")
    #
    #     c_limited = consul.Consul(port=acl_consul.port, token=token)
    #     assert c_limited.kv.get("foo")[1]["Value"] == b"bar"
    #     pytest.raises(consul.ACLPermissionDenied, c_limited.kv.put, "foo", "bar2")
    #     pytest.raises(consul.ACLPermissionDenied, c_limited.kv.delete, "foo")
    #
    #     assert c.kv.get("private/foo")[1]["Value"] == b"bar"
    #     pytest.raises(consul.ACLPermissionDenied, c_limited.kv.get, "private/foo")
    #     pytest.raises(consul.ACLPermissionDenied, c_limited.kv.put, "private/foo", "bar2")
    #     pytest.raises(consul.ACLPermissionDenied, c_limited.kv.delete, "private/foo")
    #
    #     # check we can override the client's default token
    #     pytest.raises(consul.ACLPermissionDenied, c.kv.get, "private/foo", token=token)
    #     pytest.raises(consul.ACLPermissionDenied, c.kv.put, "private/foo", "bar2", token=token)
    #     pytest.raises(consul.ACLPermissionDenied, c.kv.delete, "private/foo", token=token)
    #
    #     # clean up
    #     c.acl.destroy(token)
    #     acls = c.acl.list()
    #     assert {x["ID"] for x in acls} == {"anonymous", master_token}

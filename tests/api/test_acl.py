import pytest

import consul
from tests.utils import find_recursive

# Static RSA public key used to configure an offline "jwt" ACL auth method in tests,
# so auth-method/binding-rule CRUD can be tested without a real OIDC/Kubernetes backend.
JWT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0VPUoKqJMko3Snie9UX1
AgDQcE0W13BdhFJn9ngzjq/ce2WJiIzww/sY1NVwVUkymdGYsFhoEorvGBwsOgWI
FEOlpKgTWOjn+nXVYCH7AnyVdYkCfgDPItdv666ankphcv55QJOY16om2uSWV3iy
IoScXHFVJtBhlwho33wH+AZLmaV2LSEYqQdqHhGKT6JO20QRGYQzxfXkGSbEUtNm
f2Tgbr4nZPL/fKqhuY+rsU7LGVYKGf5Ddrm5+AjotDturj4GAc+R49MfsPXN9pZG
BXOAq+NWy3W3IPz1DQ2wU1MYPm3X94FG7Og8b2qZ/5+oB/2RXwYTtW5vvOgZ6mSK
KwIDAQAB
-----END PUBLIC KEY-----"""


class TestConsulAcl:
    def test_acl_token_permission_denied(self, acl_consul) -> None:
        c, _master_token, _consul_version = acl_consul

        # No token
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.list)
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.create)
        pytest.raises(
            consul.ACLPermissionDenied, c.acl.token.update, accessor_id="00000000-0000-0000-0000-000000000002"
        )
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.clone, accessor_id="00000000-0000-0000-0000-000000000002")
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.read, accessor_id="00000000-0000-0000-0000-000000000002")
        pytest.raises(
            consul.ACLPermissionDenied, c.acl.token.delete, accessor_id="00000000-0000-0000-0000-000000000002"
        )

        # Token without the right permission (acl:write or acl:read)
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.list, token="anonymous")
        pytest.raises(consul.ACLPermissionDenied, c.acl.token.create, token="anonymous")
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.token.update,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.token.clone,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.token.read,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )
        pytest.raises(
            consul.ACLPermissionDenied,
            c.acl.token.delete,
            accessor_id="00000000-0000-0000-0000-000000000002",
            token="anonymous",
        )

    def test_acl_token_list(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # Make sure both master and anonymous tokens are created
        acls = c.acl.token.list(token=master_token)

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

    def test_acl_token_read(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.token.read, accessor_id="unknown", token=master_token)

        anonymous_token_repr = {
            "AccessorID": "00000000-0000-0000-0000-000000000002",
            "SecretID": "anonymous",
        }
        acl = c.acl.token.read(accessor_id="00000000-0000-0000-0000-000000000002", token=master_token)
        assert find_recursive(acl, anonymous_token_repr)

    def test_acl_token_create(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        c.acl.token.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        c.acl.token.create(secret_id="DEADBEEF-0000-0000-0000-000000000000", token=master_token)
        c.acl.token.create(
            secret_id="00000000-A5A5-0000-0000-000000000000",
            accessor_id="00000000-0000-A5A5-0000-000000000000",
            description="some token!",
            token=master_token,
        )

        assert c.acl.token.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert c.acl.token.read(accessor_id="00000000-0000-A5A5-0000-000000000000", token=master_token)

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
        acl = c.acl.token.list(token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_token_clone(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        assert len(c.acl.token.list(token=master_token)) == 2

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.token.clone, accessor_id="unknown", token=master_token)

        c.acl.token.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        c.acl.token.clone(accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="cloned", token=master_token)
        assert len(c.acl.token.list(token=master_token)) == 4

        expected = [
            {
                "AccessorID": "00000000-DEAD-BEEF-0000-000000000000",
            },
            {
                "Description": "cloned",
            },
        ]
        acl = c.acl.token.list(token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_token_update(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.token.update, accessor_id="unknown", token=master_token)

        assert len(c.acl.token.list(token=master_token)) == 2
        c.acl.token.create(
            accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="original", token=master_token
        )
        assert len(c.acl.token.list(token=master_token)) == 3
        c.acl.token.update(
            accessor_id="00000000-DEAD-BEEF-0000-000000000000", description="updated", token=master_token
        )
        assert len(c.acl.token.list(token=master_token)) == 3

        expected = {
            "AccessorID": "00000000-DEAD-BEEF-0000-000000000000",
            "Description": "updated",
        }
        acl = c.acl.token.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert find_recursive(acl, expected)

    def test_acl_token_delete(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        assert len(c.acl.token.list(token=master_token)) == 2
        c.acl.token.create(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert len(c.acl.token.list(token=master_token)) == 3
        assert c.acl.token.read(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)

        # Delete and ensure it doesn't exist anymore
        c.acl.token.delete(accessor_id="00000000-DEAD-BEEF-0000-000000000000", token=master_token)
        assert len(c.acl.token.list(token=master_token)) == 2
        pytest.raises(
            consul.ConsulException,
            c.acl.token.read,
            accessor_id="00000000-DEAD-BEEF-0000-000000000000",
            token=master_token,
        )

    def test_acl_policy_list(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # Make sure both master and anonymous tokens are created
        policies = c.acl.policy.list(token=master_token)
        assert find_recursive(policies, {"ID": "00000000-0000-0000-0000-000000000001", "Name": "global-management"})

    def test_acl_policy_read(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # Unknown token
        pytest.raises(consul.ConsulException, c.acl.policy.read, uuid="unknown", token=master_token)

        policy = c.acl.policy.read(uuid="00000000-0000-0000-0000-000000000001", token=master_token)
        assert find_recursive(policy, {"ID": "00000000-0000-0000-0000-000000000001", "Name": "global-management"})

    def test_acl_token_create_templated(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        policy_name = "builtin/service"
        templated_policies = [{policy_name: {"Name": "my-service"}}]

        token_info = c.acl.token.create(
            description="templated token", templated_policies=templated_policies, token=master_token
        )

        expected = {"TemplatedPolicies": [{"TemplateName": policy_name, "TemplateVariables": {"name": "my-service"}}]}

        # Check immediate response
        assert find_recursive(token_info, expected)

        # Check read
        token_read = c.acl.token.read(accessor_id=token_info["AccessorID"], token=master_token)
        assert find_recursive(token_read, expected)

    def test_acl_role_crud(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        role = c.acl.role.create(
            name="test-role",
            description="a test role",
            service_identities=[{"ServiceName": "web"}],
            node_identities=[{"NodeName": "node-1", "Datacenter": "dc1"}],
            token=master_token,
        )
        assert role["Name"] == "test-role"
        assert find_recursive(role, {"ServiceIdentities": [{"ServiceName": "web"}]})
        role_id = role["ID"]

        assert c.acl.role.read(role_id=role_id, token=master_token)["Name"] == "test-role"
        assert c.acl.role.read_by_name(name="test-role", token=master_token)["ID"] == role_id
        assert find_recursive(c.acl.role.list(token=master_token), {"ID": role_id})

        updated = c.acl.role.update(role_id=role_id, name="test-role", description="updated", token=master_token)
        assert updated["Description"] == "updated"

        assert c.acl.role.delete(role_id=role_id, token=master_token) is True
        assert c.acl.role.read(role_id=role_id, token=master_token) is None

    def test_acl_role_permission_denied(self, acl_consul) -> None:
        c, _master_token, _consul_version = acl_consul

        pytest.raises(consul.ACLPermissionDenied, c.acl.role.list)
        pytest.raises(consul.ACLPermissionDenied, c.acl.role.create, name="denied-role")

    def test_acl_auth_method_crud(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        method = c.acl.auth_method.create(
            name="test-jwt",
            method_type="jwt",
            description="a test auth method",
            config={"JWTValidationPubKeys": [JWT_PUBLIC_KEY], "BoundIssuer": "test-issuer"},
            token=master_token,
        )
        assert method["Name"] == "test-jwt"
        assert method["Type"] == "jwt"

        read = c.acl.auth_method.read(name="test-jwt", token=master_token)
        assert read["Config"]["BoundIssuer"] == "test-issuer"

        assert find_recursive(c.acl.auth_method.list(token=master_token), {"Name": "test-jwt"})

        updated = c.acl.auth_method.update(
            name="test-jwt",
            method_type="jwt",
            description="updated",
            config={"JWTValidationPubKeys": [JWT_PUBLIC_KEY], "BoundIssuer": "test-issuer"},
            token=master_token,
        )
        assert updated["Description"] == "updated"

        assert c.acl.auth_method.delete(name="test-jwt", token=master_token) is True
        assert c.acl.auth_method.read(name="test-jwt", token=master_token) is None

    #
    # def test_acl_token_implicit_token_use(self, acl_consul):
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

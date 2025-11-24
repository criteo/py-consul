class TestConsulAclTemplatedPolicy:
    def test_acl_templated_policy_preview(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        policy_name = "builtin/service"
        template_variables = {"Name": "my-service"}

        # Preview
        result = c.acl.templated_policy.preview(
            name=policy_name, template_variables=template_variables, token=master_token
        )

        assert result["ID"] is not None
        assert result["Name"].startswith("synthetic-policy-")
        assert 'service "my-service"' in result["Rules"]

    def test_acl_templated_policy_read(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        policy_name = "builtin/service"

        # Read
        result = c.acl.templated_policy.read(name=policy_name, token=master_token)

        assert result["TemplateName"] == policy_name
        assert "Template" in result

    def test_acl_templated_policy_list(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        # List
        result = c.acl.templated_policy.list(token=master_token)

        assert len(result) > 0
        assert result["builtin/service"]["TemplateName"] == "builtin/service"

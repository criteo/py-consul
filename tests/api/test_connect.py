from tests.utils import find_recursive


class TestConsulConnectIntentions:
    def test_intentions_crud(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        created = c.connect.intentions.upsert(
            source="web", destination="db", action="allow", description="allow web to db", token=master_token
        )
        assert created is True

        intention = c.connect.intentions.read(source="web", destination="db", token=master_token)
        assert intention["SourceName"] == "web"
        assert intention["DestinationName"] == "db"
        assert intention["Action"] == "allow"

        assert find_recursive(
            c.connect.intentions.list(token=master_token), {"SourceName": "web", "DestinationName": "db"}
        )

        assert c.connect.intentions.check(source="web", destination="db", token=master_token) is True

        matched = c.connect.intentions.match(by="destination", name="db", token=master_token)
        assert find_recursive(matched["db"], {"SourceName": "web"})

        assert c.connect.intentions.delete(source="web", destination="db", token=master_token) is True
        assert c.connect.intentions.read(source="web", destination="db", token=master_token) is None

    def test_intentions_deny_check(self, acl_consul) -> None:
        c, master_token, _consul_version = acl_consul

        c.connect.intentions.upsert(source="web", destination="db", action="deny", token=master_token)
        assert c.connect.intentions.check(source="web", destination="db", token=master_token) is False

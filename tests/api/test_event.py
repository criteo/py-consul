class TestEvent:
    def test_event(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert c.event.fire("fooname", "foobody")
        _index, events = c.event.list()
        assert [x["Name"] == "fooname" for x in events]
        assert [x["Payload"] == "foobody" for x in events]

    def test_event_targeted(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert c.event.fire("fooname", "foobody")
        _index, events = c.event.list(name="othername")
        assert events == []

        _index, events = c.event.list(name="fooname")
        assert [x["Name"] == "fooname" for x in events]
        assert [x["Payload"] == "foobody" for x in events]

    def test_event_fire_dc(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # the dev agent runs in dc1, so firing with the matching dc
        # should behave exactly like not specifying it at all
        assert c.event.fire("fooname", "foobody", dc="dc1")
        _index, events = c.event.list(name="fooname")
        assert [x["Name"] == "fooname" for x in events]
        assert [x["Payload"] == "foobody" for x in events]

    def test_event_list_node_service_tag_filters(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        node = c.agent.self()["Config"]["NodeName"]

        assert c.event.fire("fooname", "foobody")

        # node/service/tag are accepted as regex filter query params by the
        # /v1/event/list endpoint (see
        # https://developer.hashicorp.com/consul/api-docs/event). On a
        # single dev-mode agent Consul does not actually exclude the event
        # from the response based on these filters (they filter which
        # agents *store* the event via gossip at fire time, not what a
        # given agent returns from its local buffer), so we can only
        # confirm here that passing them doesn't error and that matching
        # events are still returned.
        _index, events = c.event.list(name="fooname", node=node)
        assert [x["Name"] == "fooname" for x in events]

        _index, events = c.event.list(name="fooname", service="fooservice")
        assert [x["Name"] == "fooname" for x in events]

        _index, events = c.event.list(name="fooname", tag="footag")
        assert [x["Name"] == "fooname" for x in events]

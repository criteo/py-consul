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

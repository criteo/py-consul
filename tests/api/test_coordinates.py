class TestCoordinates:
    def test_coordinate(self, consul_obj):
        c, _consul_version = consul_obj
        c.coordinate.nodes()
        c.coordinate.datacenters()
        assert set(c.coordinate.datacenters()[0].keys()) == {"Datacenter", "Coordinates", "AreaID"}

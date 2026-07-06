import time


class TestCoordinates:
    def test_coordinate(self, consul_obj) -> None:
        c, _consul_version = consul_obj
        c.coordinate.nodes()
        c.coordinate.datacenters()
        assert set(c.coordinate.datacenters()[0].keys()) == {"Datacenter", "Coordinates", "AreaID"}

    def test_coordinate_update(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        # find our own node name via the datacenters endpoint, which is
        # populated as soon as the agent joins the WAN gossip pool
        datacenters = c.coordinate.datacenters()
        assert datacenters
        node = datacenters[0]["Coordinates"][0]["Node"]

        coord = {"Adjustment": 0, "Error": 1.5, "Height": 0, "Vec": [0, 0, 0, 0, 0, 0, 0, 0]}

        # writing a coordinate update is somewhat artificial in a
        # single-node dev-mode cluster (real updates normally come from the
        # serf gossip / RTT estimation loop), but it lets us exercise the
        # request/response contract of the endpoint.
        assert c.coordinate.update(node, coord) is True

        # coordinate.node/:node can 404 until the update has propagated
        # through the catalog, so poll for a bit rather than sleeping a
        # fixed, possibly-too-short amount of time.
        result = None
        for _ in range(20):
            _index, result = c.coordinate.node(node)
            if result:
                break
            time.sleep(0.5)

        assert result is not None
        entry = result[0]
        assert entry["Node"] == node
        assert entry["Coord"]["Error"] == coord["Error"]
        assert entry["Coord"]["Vec"] == coord["Vec"]

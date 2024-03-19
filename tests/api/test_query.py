class testQuery:
    def test_query(self, consul_obj):
        c, _consul_version = consul_obj

        # check that query list is empty
        queries = c.query.list()
        assert queries == []

        # create a new named query
        query_service = "foo"
        query_name = "fooquery"
        query = c.query.create(query_service, query_name)

        # assert response contains query ID
        assert "ID" in query
        assert query["ID"] is not None
        assert str(query["ID"]) != ""

        # retrieve query using id and name
        queries = c.query.get(query["ID"])
        assert queries != []
        assert len(queries) == 1
        assert queries[0]["Name"] == query_name
        assert queries[0]["ID"] == query["ID"]

        # explain query
        assert c.query.explain(query_name)["Query"]

        # delete query
        assert c.query.delete(query["ID"])

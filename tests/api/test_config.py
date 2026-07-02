class TestConfig:
    def test_config_entry_crud(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        assert c.config.set(kind="service-defaults", name="test-svc", config_entry={"Protocol": "http"}) is True

        entry = c.config.get(kind="service-defaults", name="test-svc")
        assert entry["Kind"] == "service-defaults"
        assert entry["Name"] == "test-svc"
        assert entry["Protocol"] == "http"

        entries = c.config.list(kind="service-defaults")
        assert any(e["Name"] == "test-svc" for e in entries)

        assert c.config.set(kind="service-defaults", name="test-svc", config_entry={"Protocol": "grpc"}) is True
        updated = c.config.get(kind="service-defaults", name="test-svc")
        assert updated["Protocol"] == "grpc"

        assert c.config.delete(kind="service-defaults", name="test-svc") is True
        assert c.config.get(kind="service-defaults", name="test-svc") is None

    def test_config_entry_cas(self, consul_obj) -> None:
        c, _consul_version = consul_obj

        c.config.set(kind="service-defaults", name="cas-svc", config_entry={"Protocol": "http"})
        modify_index = c.config.get(kind="service-defaults", name="cas-svc")["ModifyIndex"]

        # A stale cas value must not apply
        stale_cas = int(modify_index) + 999999
        assert (
            c.config.set(kind="service-defaults", name="cas-svc", config_entry={"Protocol": "grpc"}, cas=stale_cas)
            is False
        )
        assert c.config.get(kind="service-defaults", name="cas-svc")["Protocol"] == "http"

        # The correct cas value applies
        assert (
            c.config.set(
                kind="service-defaults", name="cas-svc", config_entry={"Protocol": "grpc"}, cas=int(modify_index)
            )
            is True
        )
        assert c.config.get(kind="service-defaults", name="cas-svc")["Protocol"] == "grpc"

        # Deleting with a stale cas must not apply
        modify_index = c.config.get(kind="service-defaults", name="cas-svc")["ModifyIndex"]
        assert c.config.delete(kind="service-defaults", name="cas-svc", cas=int(modify_index) + 999999) is False
        assert c.config.get(kind="service-defaults", name="cas-svc") is not None

        # Deleting with the correct cas applies
        assert c.config.delete(kind="service-defaults", name="cas-svc", cas=int(modify_index)) is True
        assert c.config.get(kind="service-defaults", name="cas-svc") is None

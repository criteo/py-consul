import collections

import pytest

from consul import Consul

ACLConsul = collections.namedtuple("ACLConsul", ["instance", "token", "version"])


@pytest.fixture
def acl_consul(acl_consul_instance):
    instance, token = acl_consul_instance
    return ACLConsul(Consul(port=instance.port), token, instance.version)


@pytest.fixture
def consul_obj(consul_port):
    consul_port, consul_version = consul_port
    c = Consul(port=consul_port)
    return c, consul_version

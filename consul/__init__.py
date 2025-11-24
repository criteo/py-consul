__version__ = "1.7.1"

from consul.check import Check
from consul.exceptions import ACLDisabled, ACLPermissionDenied, ConsulException, NotFound, Timeout
from consul.std import Consul

from importlib.metadata import PackageNotFoundError, version

from consul.check import Check
from consul.exceptions import ACLDisabled, ACLPermissionDenied, ConsulException, NotFound, Timeout
from consul.std import Consul

# The version comes from the git tag, through setuptools-scm.
try:
    __version__ = version("py-consul")
except PackageNotFoundError:
    __version__ = "unknown"

import collections
import json
import os
import socket
import time
import uuid

import docker
import pytest
import requests
from requests import RequestException

CONSUL_VERSIONS = ["1.16.1", "1.17.3"]

ConsulInstance = collections.namedtuple("ConsulInstance", ["container", "port", "version"])

# Create a logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def get_free_ports(num, host=None):
    if not host:
        host = "127.0.0.1"
    sockets = []
    ret = []
    for _ in range(num):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, 0))
        ret.append(s.getsockname()[1])
        sockets.append(s)
    for s in sockets:
        s.close()
    return ret


@pytest.fixture(scope="session", autouse=True)
def _unset_consul_token():
    if "CONSUL_HTTP_TOKEN" in os.environ:
        del os.environ["CONSUL_HTTP_TOKEN"]


def start_consul_container(version, acl_master_token=None):
    """
    Starts a Consul container. If acl_master_token is None, ACL will be disabled
    for this server, otherwise it will be enabled and the master token will be
    set to the supplied token.

    Returns: a tuple of the container object and the HTTP port the instance is listening on
    """
    client = docker.from_env()
    allocated_ports = get_free_ports(5)
    ports = {
        "http": allocated_ports[0],
        "server": allocated_ports[1],
        "grpc": allocated_ports[2],
        "serf_lan": allocated_ports[3],
        "serf_wan": allocated_ports[4],
    }

    base_config = {
        "ports": {
            "https": -1,
            "dns": -1,
            "grpc_tls": -1,
        },
        "performance": {"raft_multiplier": 1},
        "enable_script_checks": True,
    }
    docker_config = {
        "ports": {
            8500: ports["http"],
            8300: ports["server"],
            8502: ports["grpc"],
            8301: ports["serf_lan"],
            8302: ports["serf_wan"],
        },
        "environment": {"CONSUL_LOCAL_CONFIG": json.dumps(base_config)},
        "detach": True,
        "name": f"consul_test_{uuid.uuid4().hex[:8]}",  # Add a unique name
    }

    # Extend the base config with required ACL fields if needed
    if acl_master_token:
        acl_config = {
            "primary_datacenter": "dc1",
            "acl": {"enabled": True, "tokens": {"initial_management": acl_master_token}},
        }
        merged_config = {**base_config, **acl_config}
        docker_config["environment"]["CONSUL_LOCAL_CONFIG"] = json.dumps(merged_config)

    def start_consul_container_with_retry(client, command, version, docker_config, max_retries=3, retry_delay=2):  # pylint: disable=inconsistent-return-statements
        """
        Start a Consul container with retries as a few initial attempts sometimes fail.
        """
        for attempt in range(max_retries):
            try:
                container = client.containers.run(f"hashicorp/consul:{version}", command=command, **docker_config)
                return container
            except docker.errors.APIError:
                # Cleanup that stray container as it might cause a naming conflict
                try:
                    container = client.containers.get(docker_config["name"])
                    container.remove(force=True)
                except docker.errors.NotFound:
                    pass
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)

    container = start_consul_container_with_retry(
        client, command="agent -dev -client=0.0.0.0 -log-level trace", version=version, docker_config=docker_config
    )

    # Wait for Consul to be ready
    base_uri = f"http://127.0.0.1:{ports['http']}/v1/"
    start_time = time.time()
    global_timeout = 10

    while True:
        if time.time() - start_time > global_timeout:
            container.stop()
            container.remove()
            raise TimeoutError("Global timeout reached")
        time.sleep(0.1)
        try:
            response = requests.get(base_uri + "status/leader", timeout=2)
            if response.status_code == 200 and response.json():
                break
        except RequestException:
            continue

    # Additional check to ensure Consul is fully ready
    for _ in range(10):
        try:
            requests.put(base_uri + "agent/service/register", json={"name": "test-service"}, timeout=2)
            response = requests.get(base_uri + "health/service/test-service", timeout=2)
            if response.status_code == 200 and response.json():
                requests.put(base_uri + "agent/service/deregister/test-service", timeout=2)
                return container, ports["http"]
        except RequestException:
            time.sleep(0.5)

    container.stop()
    container.remove()
    raise Exception("Failed to verify Consul startup")  # pylint: disable=broad-exception-raised


def get_consul_version(port):
    base_uri = f"http://127.0.0.1:{port}/v1/"
    response = requests.get(base_uri + "agent/self", timeout=10)
    return response.json()["Config"]["Version"].strip()


def setup_and_teardown_consul(request, version, acl_master_token=None):
    # Start the container, yield, get container logs, store them in logs/<test_name>.log, stop the container
    container, port = start_consul_container(version=version, acl_master_token=acl_master_token)
    version = get_consul_version(port)
    instance = ConsulInstance(container, port, version)

    yield instance if acl_master_token is None else (instance, acl_master_token)

    logs = container.logs().decode("utf-8")
    log_file = os.path.join(LOGS_DIR, f"{request.node.name}.log")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(logs)

    container.stop()
    container.remove()


@pytest.fixture(params=CONSUL_VERSIONS)
def consul_instance(request):
    yield from setup_and_teardown_consul(request, version=request.param)


@pytest.fixture(params=CONSUL_VERSIONS)
def acl_consul_instance(request):
    acl_master_token = uuid.uuid4().hex
    yield from setup_and_teardown_consul(request, version=request.param, acl_master_token=acl_master_token)


@pytest.fixture
def consul_port(consul_instance):
    return consul_instance.port, consul_instance.version

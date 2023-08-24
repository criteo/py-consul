import collections
import json
import os
import platform
import shlex
import socket
import subprocess
import tempfile
import time
import uuid

import aiohttp
import py
import pytest
import requests
from packaging import version

collect_ignore = []

CONSUL_BINARIES = {
    "1.1.0": "consul",
    "1.13.8": "consul-1.13.8",
    "1.15.4": "consul-1.15.4",
    "1.16.1": "consul-1.16.1",
}


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


def start_consul_instance(binary_name, acl_master_token=None):
    """
    starts a consul instance. if acl_master_token is None, acl will be disabled
    for this server, otherwise it will be enabled and the master token will be
    set to the supplied token

    returns: a tuple of the instances process object and the http port the
             instance is listening on
    """
    ports = dict(zip(["http", "serf_lan", "serf_wan", "server", "dns"], get_free_ports(4) + [-1]))

    config = {"ports": ports, "performance": {"raft_multiplier": 1}, "enable_script_checks": True}
    if acl_master_token:
        config["acl_datacenter"] = "dc1"
        config["acl_master_token"] = acl_master_token

    tmpdir = py.path.local(tempfile.mkdtemp())
    tmpdir.join("config.json").write(json.dumps(config))
    tmpdir.chdir()

    (system, _node, _release, _version, _machine, _processor) = platform.uname()
    ext = "osx" if system == "Darwin" else "linux64"
    binary = os.path.join(os.path.dirname(__file__), f"{binary_name}.{ext}")
    command = "{bin} agent -dev -bind=127.0.0.1 -config-dir=."
    command = command.format(bin=binary).strip()
    command = shlex.split(command)

    with open("/dev/null", "w") as devnull:  # pylint: disable=unspecified-encoding
        p = subprocess.Popen(command, stdout=devnull, stderr=devnull)  # pylint: disable=consider-using-with

    # wait for consul instance to bootstrap
    base_uri = f"http://127.0.0.1:{ports['http']}/v1/"

    while True:
        time.sleep(0.1)
        try:
            response = requests.get(base_uri + "status/leader", timeout=10)
        except requests.ConnectionError:
            continue
        print(response.text)
        if response.text.strip() != '""':
            break

    requests.put(base_uri + "agent/service/register", data='{"name": "foo"}', timeout=10)

    while True:
        response = requests.get(base_uri + "health/service/foo", timeout=10)
        if response.text.strip() != "[]":
            break
        time.sleep(0.1)

    requests.put(base_uri + "agent/service/deregister/foo", timeout=10)
    # phew
    time.sleep(2)
    return p, ports["http"]


def clean_consul(port):
    # remove all data from the instance, to have a clean start
    base_uri = f"http://127.0.0.1:{port}/v1/"
    requests.delete(base_uri + "kv/", params={"recurse": 1}, timeout=10)
    services = requests.get(base_uri + "agent/services", timeout=10).json().keys()
    for s in services:
        requests.put(base_uri + f"agent/service/deregister/{s}", timeout=10)


async def async_clean_consul(port):
    base_uri = f"http://127.0.0.1:{port}/v1/"
    async with aiohttp.ClientSession() as session:
        # Delete all key-value pairs
        await session.delete(base_uri + "kv/", params={"recurse": 1})

        # Deregister all services
        async with session.get(base_uri + "agent/services") as response:
            services = await response.json()
            for s in services:
                await session.put(base_uri + f"agent/service/deregister/{s}")


def get_consul_version(port):
    base_uri = f"http://127.0.0.1:{port}/v1/"
    response = requests.get(base_uri + "agent/self", timeout=10)
    return response.json()["Config"]["Version"].strip()


@pytest.fixture(scope="module", params=CONSUL_BINARIES.keys())
def consul_instance(request):
    p, port = start_consul_instance(binary_name=CONSUL_BINARIES[request.param])
    version = get_consul_version(port)
    yield port, version
    p.terminate()


@pytest.fixture(scope="module", params=CONSUL_BINARIES.keys())
def acl_consul_instance(request):
    acl_master_token = uuid.uuid4().hex
    p, port = start_consul_instance(binary_name=CONSUL_BINARIES[request.param], acl_master_token=acl_master_token)
    version = get_consul_version(port)
    yield port, acl_master_token, version
    p.terminate()


@pytest.fixture()
def consul_port(consul_instance):
    port, version = consul_instance
    yield port, version
    clean_consul(port)


@pytest.fixture()
def acl_consul(acl_consul_instance):
    ACLConsul = collections.namedtuple("ACLConsul", ["port", "token", "version"])
    port, token, version = acl_consul_instance
    yield ACLConsul(port, token, version)
    clean_consul(port)


def should_skip(version_str, comparator, ref_version_str):
    v = version.parse(version_str)
    ref_version = version.parse(ref_version_str)

    if comparator == "<" and v >= ref_version:
        return f"Requires version {comparator} {ref_version_str}"
    if comparator == ">" and v <= ref_version:
        return f"Requires version {comparator} {ref_version_str}"
    # You can add other comparators if needed
    return None

from __future__ import annotations

import logging
import warnings
from typing import Any, Optional

log = logging.getLogger(__name__)


class Check:
    """
    There are three different kinds of checks: script, http and ttl
    """

    @classmethod
    def script(cls, args, interval, deregister=None) -> dict[str, Any]:
        """
        Run the script *args* every *interval* (e.g. "10s") to peform health
        check
        """
        if isinstance(args, (str, bytes)):
            warnings.warn("Check.script should take a list of args", DeprecationWarning)
            args = ["sh", "-c", args]
        ret = {"args": args, "interval": interval}
        if deregister:
            ret["DeregisterCriticalServiceAfter"] = deregister
        return ret

    @classmethod
    def http(cls, url, interval, timeout=None, deregister=None, header=None) -> dict[str, Any]:
        """
        Peform a HTTP GET against *url* every *interval* (e.g. "10s") to peform
        health check with an optional *timeout* and optional *deregister* after
        which a failing service will be automatically deregistered. Optional
        parameter *header* specifies headers sent in HTTP request. *header*
        paramater is in form of map of lists of strings,
        e.g. {"x-foo": ["bar", "baz"]}.
        """
        ret = {"http": url, "interval": interval}
        if timeout:
            ret["timeout"] = timeout
        if deregister:
            ret["DeregisterCriticalServiceAfter"] = deregister
        if header:
            ret["header"] = header
        return ret

    @classmethod
    def tcp(cls, host: str, port: int, interval, timeout=None, deregister=None) -> dict[str, Any]:
        """
        Attempt to establish a tcp connection to the specified *host* and
        *port* at a specified *interval* with optional *timeout* and optional
        *deregister* after which a failing service will be automatically
        deregistered.
        """
        ret = {"tcp": f"{host:s}:{port:d}", "interval": interval}
        if timeout:
            ret["timeout"] = timeout
        if deregister:
            ret["DeregisterCriticalServiceAfter"] = deregister
        return ret

    @classmethod
    def ttl(cls, ttl: str) -> dict[str, Any]:
        """
        Set check to be marked as critical after *ttl* (e.g. "10s") unless the
        check is periodically marked as passing.
        """
        return {"ttl": ttl}

    @classmethod
    def docker(cls, container_id, shell, script, interval, deregister=None) -> dict[str, Any]:
        """
        Invoke *script* packaged within a running docker container with
        *container_id* at a specified *interval* on the configured
        *shell* using the Docker Exec API.  Optional *register* after which a
        failing service will be automatically deregistered.
        """
        ret = {"docker_container_id": container_id, "shell": shell, "script": script, "interval": interval}
        if deregister:
            ret["DeregisterCriticalServiceAfter"] = deregister
        return ret

    @classmethod
    def _compat(
        cls, script=None, interval=None, ttl: Optional[int] = None, http=None, timeout=None, deregister=None
    ) -> dict[str, Any]:
        if not script and not http and not ttl:
            return {}

        log.warning("DEPRECATED: use consul.Check.script/http/ttl to specify check")

        ret: dict[str, Any] = {"check": {}}

        if script:
            assert interval
            assert not ttl
            assert not http
            ret["check"] = {"script": script, "interval": interval}
        if ttl:
            assert not interval or script
            assert not http
            ret["check"] = {"ttl": ttl}
        if http:
            assert interval
            assert not script
            assert not ttl
            ret["check"] = {"http": http, "interval": interval}
        if timeout:
            assert http
            ret["check"]["timeout"] = timeout

        if deregister:
            ret["check"]["DeregisterCriticalServiceAfter"] = deregister

        return ret

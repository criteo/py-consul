# Consul API Endpoint Implementation Status

This document tracks the implementation status of Consul API endpoints in the Python wrapper.
**Note:** Enterprise parameters (e.g., `namespace`, `partition`) are intentionally excluded from this analysis.

## Legend
- ✅ **Fully Handled**: All standard parameters are implemented.
- ⚠️ **Partially Handled**: Endpoint exists but is missing some standard parameters.
- ❌ **Not Handled**: Endpoint or method is completely missing.

---

## 1. Key/Value Store (`/v1/kv`)
File: `consul/api/kv.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/kv/:key` | `KV.get` | ✅ | - |
| `PUT /v1/kv/:key` | `KV.put` | ✅ | - |
| `DELETE /v1/kv/:key` | `KV.delete` | ✅ | - |

## 2. Agent (`/v1/agent`)
File: `consul/api/agent.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/agent/self` | `Agent.self` | ✅ | - |
| `GET /v1/agent/services` | `Agent.services` | ⚠️ | `filter` |
| `GET /v1/agent/service/:service_id` | `Agent.service_definition` | ✅ | - |
| `GET /v1/agent/checks` | `Agent.checks` | ⚠️ | `filter` |
| `GET /v1/agent/members` | `Agent.members` | ✅ | (`segment` is Ent) |
| `PUT /v1/agent/maintenance` | `Agent.maintenance` | ✅ | - |
| `PUT /v1/agent/join/:address` | `Agent.join` | ✅ | - |
| `PUT /v1/agent/leave` | `Agent.leave` | ✅ | - |
| `PUT /v1/agent/force-leave/:node` | `Agent.force_leave` | ⚠️ | `prune` (added v1.13) |
| `PUT /v1/agent/reload` | `Agent.reload` | ✅ | - |
| `GET /v1/agent/metrics` | `Agent.metrics` | ✅ | - |
| `GET /v1/agent/monitor` | `Agent.monitor` | ⚠️ | Not true streaming — single blocking read, see docstring |
| `PUT /v1/agent/token/default` | `Agent.Token.set_default` | ✅ | - |
| `PUT /v1/agent/token/agent` | `Agent.Token.set_agent` | ✅ | - |
| `PUT /v1/agent/token/agent_recovery` | `Agent.Token.set_agent_recovery` | ✅ | - |
| `PUT /v1/agent/token/replication` | `Agent.Token.set_replication` | ✅ | - |
| `PUT /v1/agent/token/config_file_service_registration` | `Agent.Token.set_config_file_service_registration` | ✅ | - |

### Agent Services
| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/agent/service/register` | `Agent.Service.register` | ⚠️ | Body: `Kind`, `Proxy`, `SocketPath`, `Locality` |
| `PUT /v1/agent/service/deregister/:id` | `Agent.Service.deregister` | ✅ | - |
| `PUT /v1/agent/service/maintenance/:id` | `Agent.Service.maintenance` | ✅ | - |

### Agent Checks
| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/agent/check/register` | `Agent.Check.register` | ✅ | `check` arg accepts dict, allowing all params |
| `PUT /v1/agent/check/deregister/:id` | `Agent.Check.deregister` | ✅ | - |
| `PUT /v1/agent/check/pass/:id` | `Agent.Check.ttl_pass` | ✅ | - |
| `PUT /v1/agent/check/fail/:id` | `Agent.Check.ttl_fail` | ✅ | - |
| `PUT /v1/agent/check/warn/:id` | `Agent.Check.ttl_warn` | ✅ | - |

### Agent Connect
| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `POST /v1/agent/connect/authorize` | `Agent.Connect.authorize` | ✅ | - |
| `GET /v1/agent/connect/ca/roots` | `Agent.Connect.CA.roots` | ✅ | - |
| `GET /v1/agent/connect/ca/leaf/:service` | `Agent.Connect.CA.leaf` | ✅ | - |

## 3. Catalog (`/v1/catalog`)
File: `consul/api/catalog.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/catalog/register` | `Catalog.register` | ✅ | - |
| `PUT /v1/catalog/deregister` | `Catalog.deregister` | ✅ | - |
| `GET /v1/catalog/datacenters` | `Catalog.datacenters` | ✅ | - |
| `GET /v1/catalog/nodes` | `Catalog.nodes` | ✅ | - |
| `GET /v1/catalog/services` | `Catalog.services` | ✅ | - |
| `GET /v1/catalog/service/:service` | `Catalog.service` | ✅ | - |
| `GET /v1/catalog/connect/:service` | `Catalog.connect` | ✅ | - |
| `GET /v1/catalog/node/:node` | `Catalog.node` | ✅ | - |
| `GET /v1/catalog/gateway-services/:gateway` | `Catalog.gateway_services` | ✅ | - |

## 4. Health (`/v1/health`)
File: `consul/api/health.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/health/node/:node` | `Health.node` | ✅ | - |
| `GET /v1/health/checks/:service` | `Health.checks` | ✅ | - |
| `GET /v1/health/service/:service` | `Health.service` | ✅ | - |
| `GET /v1/health/connect/:service` | `Health.connect` | ✅ | - |
| `GET /v1/health/state/:state` | `Health.state` | ✅ | - |
| `GET /v1/health/ingress/:service` | `Health.ingress` | ✅ | - |

## 5. Session (`/v1/session`)
File: `consul/api/session.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/session/create` | `Session.create` | ✅ | - |
| `PUT /v1/session/destroy/:uuid` | `Session.destroy` | ✅ | - |
| `PUT /v1/session/renew/:uuid` | `Session.renew` | ✅ | - |
| `GET /v1/session/list` | `Session.list` | ✅ | - |
| `GET /v1/session/node/:node` | `Session.node` | ✅ | - |
| `GET /v1/session/info/:uuid` | `Session.info` | ✅ | - |

## 6. ACL (`/v1/acl`)
File: `consul/api/acl/*.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/acl/bootstrap` | `ACL.bootstrap` | ✅ | - |
| `POST /v1/acl/login` | `ACL.login` | ✅ | - |
| `POST /v1/acl/logout` | `ACL.logout` | ✅ | - |
| `GET /v1/acl/tokens` | `Token.list` | ⚠️ | `policy`, `role`, `authmethod`, `secondary` (filters) |
| `PUT /v1/acl/token` | `Token.create` | ⚠️ | `ServiceIdentities`, `NodeIdentities`, `ExpirationTime`, `ExpirationTTL`, `Local` |
| `GET /v1/acl/token/:accessor` | `Token.read` | ✅ | - |
| `PUT /v1/acl/token/:accessor` | `Token.update` | ⚠️ | `ServiceIdentities`, `NodeIdentities`, `ExpirationTime`, `ExpirationTTL`, `Local` |
| `DELETE /v1/acl/token/:accessor` | `Token.delete` | ✅ | - |
| `PUT /v1/acl/token/:accessor/clone` | `Token.clone` | ✅ | - |
| `GET /v1/acl/token/self` | `Token.read_self` | ✅ | - |
| `GET /v1/acl/policies` | `Policy.list` | ✅ | - |
| `PUT /v1/acl/policy` | `Policy.create` | ✅ | - |
| `GET /v1/acl/policy/:id` | `Policy.read` | ✅ | - |
| `PUT /v1/acl/policy/:id` | - | ❌ | - |
| `DELETE /v1/acl/policy/:id` | - | ❌ | - |
| `GET /v1/acl/roles` | `Role.list` | ✅ | - |
| `PUT /v1/acl/role` | `Role.create` | ✅ | - |
| `GET /v1/acl/role/:id` | `Role.read` | ✅ | - |
| `GET /v1/acl/role/name/:name` | `Role.read_by_name` | ✅ | - |
| `PUT /v1/acl/role/:id` | `Role.update` | ✅ | - |
| `DELETE /v1/acl/role/:id` | `Role.delete` | ✅ | - |
| `GET /v1/acl/auth-methods` | `AuthMethod.list` | ✅ | - |
| `PUT /v1/acl/auth-method` | `AuthMethod.create` | ✅ | - |
| `GET /v1/acl/auth-method/:name` | `AuthMethod.read` | ✅ | - |
| `PUT /v1/acl/auth-method/:name` | `AuthMethod.update` | ✅ | - |
| `DELETE /v1/acl/auth-method/:name` | `AuthMethod.delete` | ✅ | - |
| `GET /v1/acl/binding-rules` | `BindingRule.list` | ✅ | - |
| `PUT /v1/acl/binding-rule` | `BindingRule.create` | ✅ | - |
| `GET /v1/acl/binding-rule/:id` | `BindingRule.read` | ✅ | - |
| `PUT /v1/acl/binding-rule/:id` | `BindingRule.update` | ✅ | - |
| `DELETE /v1/acl/binding-rule/:id` | `BindingRule.delete` | ✅ | - |

## 7. Event (`/v1/event`)
File: `consul/api/event.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/event/fire/:name` | `Event.fire` | ✅ | - |
| `GET /v1/event/list` | `Event.list` | ✅ | `node`/`service`/`tag` accepted but observed to have no effect at list-time — see docstring |

## 8. Coordinate (`/v1/coordinate`)
File: `consul/api/coordinates.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/coordinate/datacenters` | `Coordinate.datacenters` | ✅ | - |
| `GET /v1/coordinate/nodes` | `Coordinate.nodes` | ✅ | - |
| `GET /v1/coordinate/node/:node` | `Coordinate.node` | ✅ | - |
| `PUT /v1/coordinate/update` | `Coordinate.update` | ✅ | - |

## 9. Operator (`/v1/operator`)
File: `consul/api/operator.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/operator/raft/configuration` | `Operator.raft_config` | ✅ | - |
| `DELETE /v1/operator/raft/peer` | `Operator.raft_remove_peer` | ✅ | - |
| `POST /v1/operator/raft/transfer-leader` | `Operator.raft_transfer_leader` | ✅ | - |
| `GET /v1/operator/autopilot/configuration` | `Operator.autopilot_configuration` | ✅ | - |
| `PUT /v1/operator/autopilot/configuration` | `Operator.update_autopilot_configuration` | ✅ | - |
| `GET /v1/operator/autopilot/health` | `Operator.autopilot_health` | ✅ | - |
| `GET /v1/operator/keyring` | `Operator.keyring_list` | ✅ | - |
| `POST /v1/operator/keyring` | `Operator.keyring_install` | ✅ | - |
| `PUT /v1/operator/keyring` | `Operator.keyring_use` | ✅ | - |
| `DELETE /v1/operator/keyring` | `Operator.keyring_remove` | ✅ | - |
| `GET /v1/operator/usage` | `Operator.usage` | ✅ | - |

## 10. Query (`/v1/query`)
File: `consul/api/query.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/query` | `Query.list` | ✅ | - |
| `POST /v1/query` | `Query.create` | ✅ | - |
| `GET /v1/query/:uuid` | `Query.get` | ✅ | - |
| `PUT /v1/query/:uuid` | `Query.update` | ✅ | - |
| `DELETE /v1/query/:uuid` | `Query.delete` | ✅ | - |
| `GET /v1/query/:uuid/execute` | `Query.execute` | ✅ | - |
| `GET /v1/query/:uuid/explain` | `Query.explain` | ✅ | - |

## 11. Status (`/v1/status`)
File: `consul/api/status.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/status/leader` | `Status.leader` | ✅ | - |
| `GET /v1/status/peers` | `Status.peers` | ✅ | - |

## 12. Transactions (`/v1/txn`)
File: `consul/api/txn.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/txn` | `Txn.put` | ✅ | - |

## 13. Connect (`/v1/connect`)
File: `consul/api/connect.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/connect/ca/roots` | `Connect.CA.roots` | ✅ | - |
| `GET /v1/connect/ca/configuration` | `Connect.CA.configuration` | ✅ | - |
| `PUT /v1/connect/ca/configuration` | - | ❌ | - |
| `PUT /v1/connect/intentions/exact` | `Connect.Intentions.upsert` | ✅ | - |
| `GET /v1/connect/intentions/exact` | `Connect.Intentions.read` | ✅ | - |
| `DELETE /v1/connect/intentions/exact` | `Connect.Intentions.delete` | ✅ | - |
| `GET /v1/connect/intentions` | `Connect.Intentions.list` | ✅ | - |
| `GET /v1/connect/intentions/check` | `Connect.Intentions.check` | ✅ | - |
| `GET /v1/connect/intentions/match` | `Connect.Intentions.match` | ✅ | - |
| `POST /v1/connect/intentions` (legacy, deprecated 1.9.0) | - | ❌ | Intentionally not implemented — use exact-match endpoints above |
| `GET/PUT/DELETE /v1/connect/intentions/:uuid` (legacy, deprecated 1.9.0) | - | ❌ | Intentionally not implemented — use exact-match endpoints above |

## 14. Config Entries (`/v1/config`)
File: `consul/api/config.py`

Generic CRUD covering all config entry kinds (service-defaults, service-router,
service-splitter, service-resolver, service-intentions, ingress-gateway,
terminating-gateway, proxy-defaults, mesh, exported-services, api-gateway,
http-route, tcp-route, inline-certificate, file-system-certificate, and others)
through a single Kind/Name-based implementation. Kind-specific body fields are
not individually modeled — callers pass the kind-specific body as a dict.

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `PUT /v1/config` | `Config.set` | ✅ | - |
| `GET /v1/config/:kind/:name` | `Config.get` | ✅ | - |
| `GET /v1/config/:kind` | `Config.list` | ✅ | - |
| `DELETE /v1/config/:kind/:name` | `Config.delete` | ✅ | - |

## 15. Discovery Chain (`/v1/discovery-chain`)
File: `consul/api/discovery_chain.py`

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/discovery-chain/:service` | `DiscoveryChain.get` | ✅ | - |
| `POST /v1/discovery-chain/:service` | `DiscoveryChain.get` | ✅ | Uses POST automatically when any override is passed |

## 16. Snapshot (`/v1/snapshot`)
File: `consul/api/snapshot.py`

Both endpoints require a management-level ACL token (not a granular ACL rule).

| Endpoint | Python Method | Status | Missing Parameters |
| :--- | :--- | :--- | :--- |
| `GET /v1/snapshot` | `Snapshot.save` | ✅ | - |
| `PUT /v1/snapshot` | `Snapshot.restore` | ✅ | - |

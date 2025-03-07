# Change log


## 1.5.5

- **fix:**  Simplify loop handling in async Consul client


## 1.5.4

- **feature:**  Improve robustness of JSON decoding
- **feature:**  Add support for honoring additional arguments in consul.Consul()

## 1.5.3

- **feature:** add replace_existing_checks option to agent.service.register()
- **revert:** add replace_existing_checks option to Catalog.register()

## 1.5.2

- **feature:** add replace_existing_checks option to Catalog.register()

## 1.5.1

- **feature:** Implement creation of policies.
- **feature:** Integrate policy addition during token creation.

## 1.5.0

- **[Breaking]** ACL endpoint change, consul.acl is now consul.acl.token
- **feature:** add consul.acl.policy.list and acl.policy.read

## 1.4.1

- **ci:** fix package publishing and update GH actions versions

## 1.4.0 (unreleased)

- **[Breaking]** due to the re-implementation of the ACL endpoint and the drop of the support of OSX and consul 1.1.0.
  - **feature:** re-implement some basic ACL endpoint
  - **feature:** drop support of OSX and consul 1.1.0
  - **feature:** support multi-check service registration (through extra_checks parameter)
  - **env:** support python 3.12
  - **tests:** multi consul version test (1.13.8, 1.15.4, 1.16.1, 1.17.3)
  - **tests:** add test utils for cleaner API output expected assertion
  - **code-style:** use ruff linter and formatter
  - **code-style:** split files following the consul API logic
  - **ci:** speedup ci with uv/tox-uv

## 1.3.0

- **feature:** drop tornado and twisted support
- **env:** support python 3.10 and 3.11
- **env:** drop support of EOL python versions 3.5, 3.6, and 3.7
- **code-style:** syntax modernization
- **code-style:** formatter and linter use
- **ci:** multiple python version test and linter enforcement

## 1.2.4

- **feature:** aio: allow setting timeout by request

## 1.2.3

- **feature:** base: ensure return format of json callback is more consistent

## 1.2.2

- **bugfix:** connect: fix wrong endpoints callbacks

## 1.2.1

- **feature:** Add support for context-managers
- **feature:** Add support for /agent/service/:service_id API
- **bugfix:** rename internal connect method

## 1.2.0

- **feature:** Support deregister field in Check.script
- **feature:** Introduce Consul Connect-related API wrappers
- **feature:** Add token support missing in multiple methods
- **bugfix:** aio: fix timeout type
- **feature:** allow multiple tags in service health query

## 1.1.5

- Dummy release to overcome a pypi release issue

## 1.1.4

- **bugfix:** fixed connection_timeout usage for aiohttp

## 1.1.3

- **bugfix:** fixed connection_limit usage for aiohttp

## 1.1.2

- add support for connection_limit and connection_timeout in aiohttp
- fix asyncio session close

## 1.1.1

- Add support for python 3.7 and 3.8
- Fix asyncio compatibility to support latest python version
- Remove six dependency
- Use new style of class declaration
- Get rid of py3.4 old compat
- Drop support of deprecated python2
- **base:** allow weights parameter in service register

# Base fork

Criteo starts forking this library from [https://github.com/cablehead/python-consul](https://github.com/cablehead/python-consul)

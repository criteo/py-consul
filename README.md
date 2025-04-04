# py-consul [![PyPi version](https://img.shields.io/pypi/v/py-consul.svg)](https://pypi.python.org/pypi/py-consul/) [![Python version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/) ![Status](https://img.shields.io/badge/status-maintained-green.svg)

Status
-----------
This project is maintained and actively developed by Criteo.
We aim at converging towards a full compatibility with the official Consul API.

We're currently supporting consul 1.17 up to 1.20. Due to quite a few changes
since our development started (see section "A bit of history"), some endpoints are 
still partially handled.

Therefore, we are open to contributions and suggestions.

Example
-------

```python
    import consul

    c = consul.Consul()

    # poll a key for updates
    index = None
    while True:
        index, data = c.kv.get('foo', index=index)
        print data['Value']

    # in another process
    c.kv.put('foo', 'bar')
```

Installation
------------
```bash
    pip install py-consul
```

**Note:** When using py-consul library in environment with proxy server, 
setting of ``http_proxy``, ``https_proxy`` and ``no_proxy`` environment variables 
can be required for proper functionality.

A bit of history
-----------

The origin project [python-consul](https://github.com/cablehead/python-consul) is not maintained
since 2018.  As we were not able to get in touch with the maintainer (cablehead)
to merge and release our PRs, we've forked the project in order to continue the
maintenance of the project. We also renamed the project to be able to upload
on pypi; see [PyPI](https://pypi.org/project/py-consul/)

Following some major changes, we decided to detach this fork from the original project
and move from [criteo fork space](https://github.com/criteo-forks/) 
to [criteo space](https://github.com/criteo/).

Contributing
------------

Please reach out if you're interested in being a maintainer as well. Otherwise,
open a PR or Issue we'll try and respond as quickly as possible.

When you create a PR please ensure:

- To add tests for your new features, if applicable
- To add docstrings for new API features you may add
